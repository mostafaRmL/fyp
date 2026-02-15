"""
Ontology-based Similarity Service for v2.0
Implements graph traversal and scoring for disease-drug similarity search.
"""

from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass
from collections import deque
from enum import Enum
import requests
from app.utils.logger import LoggerSetup

logger = LoggerSetup.get_logger(__name__)


class RelationshipType(Enum):
    """Types of relationships in the medical ontology."""
    SUBCLASS_OF = "P279"  # Subclass of (inheritance)
    INSTANCE_OF = "P31"  # Instance of
    HAS_SYMPTOM = "P780"  # Has symptom
    TREATS = "P2175"  # Medical condition treated
    ACTIVE_INGREDIENT = "P3781"  # Active ingredient
    HAS_PART = "P527"  # Has part
    PART_OF = "P361"  # Part of
    CAUSATIVE_AGENT = "P828"  # Causative agent
    HAS_EFFECT = "P1542"  # Has effect


@dataclass
class SimilarityPath:
    """Represents a path between two entities in the knowledge graph."""
    source_id: str
    source_label: str
    target_id: str
    target_label: str
    path: List[Tuple[str, str, str]]  # [(entity_id, relationship, entity_label)]
    score: float
    explanation: str


@dataclass
class SimilarityResult:
    """Result of a similarity search."""
    entity_id: str
    entity_label: str
    similarity_score: float
    paths: List[SimilarityPath]
    explanation: str
    properties: Dict[str, str]


class SimilarityService:
    """
    Ontology-based similarity engine using graph traversal.
    Calculates semantic similarity between medical entities.
    """
    
    SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
    MAX_HOPS = 3  # Maximum path length for traversal
    MIN_SIMILARITY = 0.70  # 70% threshold
    
    # Relationship weights for scoring (higher = more important)
    RELATIONSHIP_WEIGHTS = {
        RelationshipType.SUBCLASS_OF: 0.9,
        RelationshipType.INSTANCE_OF: 0.85,
        RelationshipType.HAS_SYMPTOM: 0.8,
        RelationshipType.TREATS: 0.95,
        RelationshipType.ACTIVE_INGREDIENT: 0.75,
        RelationshipType.HAS_PART: 0.7,
        RelationshipType.PART_OF: 0.7,
        RelationshipType.CAUSATIVE_AGENT: 0.8,
        RelationshipType.HAS_EFFECT: 0.75,
    }
    
    def __init__(self):
        """Initialize the similarity service."""
        self.headers = {
            "User-Agent": "Medical-Assistant-FYP/2.0 (Educational Project)",
            "Accept": "application/json"
        }
        logger.info("Similarity service initialized")
    
    def _query_wikidata(self, sparql_query: str) -> Dict:
        """Execute SPARQL query against Wikidata."""
        try:
            response = requests.get(
                self.SPARQL_ENDPOINT,
                params={"query": sparql_query, "format": "json"},
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"SPARQL query failed: {e}")
            return {}
    
    def get_entity_neighbors(self, entity_id: str, max_results: int = 20) -> List[Tuple[str, str, str, str]]:
        """
        Get neighboring entities (1-hop connections).
        Returns: [(neighbor_id, neighbor_label, relationship_property, relationship_label)]
        """
        query = f"""
        SELECT DISTINCT ?neighbor ?neighborLabel ?property ?propertyLabel WHERE {{
          VALUES ?source {{ wd:{entity_id} }}
          
          # Outgoing relationships
          {{
            ?source ?prop ?neighbor.
            ?property wikibase:directClaim ?prop.
            FILTER(?property IN (
              wd:P279, wd:P31, wd:P780, wd:P2175, 
              wd:P3781, wd:P527, wd:P361, wd:P828, wd:P1542
            ))
          }}
          UNION
          # Incoming relationships
          {{
            ?neighbor ?prop ?source.
            ?property wikibase:directClaim ?prop.
            FILTER(?property IN (
              wd:P279, wd:P31, wd:P780, wd:P2175, 
              wd:P3781, wd:P527, wd:P361, wd:P828, wd:P1542
            ))
          }}
          
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT {max_results}
        """
        
        result = self._query_wikidata(query)
        neighbors = []
        
        if result and "results" in result:
            for binding in result["results"]["bindings"]:
                neighbor_id = binding.get("neighbor", {}).get("value", "").split("/")[-1]
                neighbor_label = binding.get("neighborLabel", {}).get("value", "Unknown")
                prop_id = binding.get("property", {}).get("value", "").split("/")[-1]
                prop_label = binding.get("propertyLabel", {}).get("value", "Unknown")
                
                if neighbor_id and neighbor_id != entity_id:
                    neighbors.append((neighbor_id, neighbor_label, prop_id, prop_label))
        
        return neighbors
    
    def find_paths_bfs(
        self, 
        source_id: str, 
        source_label: str,
        target_id: str, 
        target_label: str,
        max_hops: int = MAX_HOPS
    ) -> List[List[Tuple[str, str, str, str]]]:
        """
        Find paths between source and target using BFS.
        Returns list of paths, where each path is a list of (entity_id, entity_label, relation, relation_label).
        """
        paths = []
        queue = deque([(source_id, source_label, [])])
        visited = {source_id}
        
        while queue and len(paths) < 5:  # Limit to 5 paths for performance
            current_id, current_label, path = queue.popleft()
            
            if len(path) >= max_hops:
                continue
            
            neighbors = self.get_entity_neighbors(current_id)
            
            for neighbor_id, neighbor_label, rel_prop, rel_label in neighbors:
                new_path = path + [(current_id, current_label, rel_prop, rel_label)]
                
                if neighbor_id == target_id:
                    # Found a path to target
                    new_path.append((target_id, target_label, "", ""))
                    paths.append(new_path)
                    continue
                
                if neighbor_id not in visited and len(new_path) < max_hops:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, neighbor_label, new_path))
        
        return paths
    
    def calculate_path_score(self, path: List[Tuple[str, str, str, str]]) -> float:
        """
        Calculate similarity score for a path.
        Score = (1 / path_length) × avg(relationship_weights) × property_bonus
        """
        if not path or len(path) <= 1:
            return 0.0
        
        path_length = len(path) - 1  # Exclude start/end nodes
        
        # Calculate average relationship weight
        relationship_scores = []
        for _, _, rel_prop, _ in path[:-1]:  # Exclude last element (target)
            try:
                rel_type = RelationshipType(rel_prop)
                weight = self.RELATIONSHIP_WEIGHTS.get(rel_type, 0.5)
                relationship_scores.append(weight)
            except ValueError:
                relationship_scores.append(0.5)  # Unknown relationship
        
        avg_relationship_weight = sum(relationship_scores) / len(relationship_scores) if relationship_scores else 0.5
        
        # Path length penalty (shorter paths = higher scores)
        path_length_score = 1.0 / path_length if path_length > 0 else 1.0
        
        # Property bonus: high-value relationships get extra points
        property_bonus = 1.0
        if any(score >= 0.9 for score in relationship_scores):
            property_bonus = 1.1  # 10% bonus for high-value relationships
        
        # Final score
        score = path_length_score * avg_relationship_weight * property_bonus
        
        # Normalize to 0-1 range
        return min(score, 1.0)
    
    def generate_explanation(self, path: List[Tuple[str, str, str, str]]) -> str:
        """Generate human-readable explanation for a similarity path."""
        if not path or len(path) <= 1:
            return "No connection found"
        
        explanation_parts = []
        for i in range(len(path) - 1):
            entity_label = path[i][1]
            rel_label = path[i][3]
            next_entity_label = path[i + 1][1]
            
            if rel_label:
                explanation_parts.append(f"{entity_label} → ({rel_label}) → {next_entity_label}")
        
        return " | ".join(explanation_parts)
    
    def find_similar_entities(
        self,
        source_id: str,
        source_label: str,
        candidate_ids: List[Tuple[str, str]]  # [(id, label), ...]
    ) -> List[SimilarityResult]:
        """
        Find similar entities to the source entity from a list of candidates.
        Returns results with similarity >= MIN_SIMILARITY threshold.
        """
        results = []
        
        for target_id, target_label in candidate_ids:
            # Find paths between source and target
            paths = self.find_paths_bfs(source_id, source_label, target_id, target_label)
            
            if not paths:
                continue
            
            # Calculate scores for all paths
            similarity_paths = []
            for path in paths:
                score = self.calculate_path_score(path)
                if score >= self.MIN_SIMILARITY:
                    explanation = self.generate_explanation(path)
                    similarity_paths.append(
                        SimilarityPath(
                            source_id=source_id,
                            source_label=source_label,
                            target_id=target_id,
                            target_label=target_label,
                            path=[(p[0], p[2], p[1]) for p in path],  # (entity_id, rel, entity_label)
                            score=score,
                            explanation=explanation
                        )
                    )
            
            if similarity_paths:
                # Use highest score among all paths
                max_score = max(p.score for p in similarity_paths)
                best_path = max(similarity_paths, key=lambda p: p.score)
                
                results.append(
                    SimilarityResult(
                        entity_id=target_id,
                        entity_label=target_label,
                        similarity_score=max_score,
                        paths=similarity_paths,
                        explanation=best_path.explanation,
                        properties={}
                    )
                )
        
        # Sort by similarity score (descending)
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        logger.info(f"Found {len(results)} similar entities above {self.MIN_SIMILARITY} threshold")
        return results
    
    def search_diseases_by_common_parent(
        self,
        disease_id: str,
        disease_label: str,
        max_results: int = 10
    ) -> List[SimilarityResult]:
        """
        Find diseases similar to the given disease by finding shared parent classes.
        """
        query = f"""
        SELECT DISTINCT ?disease2 ?disease2Label ?commonParent ?commonParentLabel WHERE {{
          wd:{disease_id} wdt:P279+ ?commonParent.  # Source disease parents
          ?disease2 wdt:P279+ ?commonParent.  # Other diseases with same parent
          ?disease2 wdt:P31 wd:Q12136.  # Instance of disease
          FILTER(?disease2 != wd:{disease_id})
          
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT {max_results}
        """
        
        result = self._query_wikidata(query)
        candidates = []
        
        if result and "results" in result:
            for binding in result["results"]["bindings"]:
                disease2_id = binding.get("disease2", {}).get("value", "").split("/")[-1]
                disease2_label = binding.get("disease2Label", {}).get("value", "Unknown")
                if disease2_id:
                    candidates.append((disease2_id, disease2_label))
        
        # Remove duplicates
        candidates = list(set(candidates))
        
        # Find similarity scores
        return self.find_similar_entities(disease_id, disease_label, candidates)


# Singleton instance
_similarity_service = None


def get_similarity_service() -> SimilarityService:
    """Get singleton instance of similarity service."""
    global _similarity_service
    if _similarity_service is None:
        _similarity_service = SimilarityService()
    return _similarity_service
