"""
Similarity-Based Medicine Service (v2.0)
Orchestrates ontology-based similarity search for disease-drug matching.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from app.services.similarity_service import (
    get_similarity_service,
    SimilarityResult,
    SimilarityPath
)
from app.services.sparql_service import get_sparql_service
from app.utils.logger import LoggerSetup

logger = LoggerSetup.get_logger(__name__)


@dataclass
class DrugRecommendation:
    """Recommendation result with similarity score and explanation."""
    drug_id: str
    drug_name: str
    similarity_score: float
    treats_conditions: List[str]
    explanation: str
    similar_drugs: List[Dict[str, Any]]
    properties: Dict[str, Any]


@dataclass
class SearchResult:
    """Complete search result with metadata."""
    query: str
    query_type: str  # "symptom" or "disease"
    identified_conditions: List[Dict[str, str]]
    drug_recommendations: List[DrugRecommendation]
    total_results: int
    search_metadata: Dict[str, Any]


class SimilarityMedicineService:
    """
    Orchestration service for similarity-based medicine recommendations.
    Integrates symptom analysis, condition matching, and drug similarity.
    """
    
    def __init__(self):
        """Initialize the service with dependencies."""
        self.similarity_service = get_similarity_service()
        self.sparql_service = get_sparql_service()
        logger.info("Similarity medicine service initialized")
    
    def search_by_symptom(
        self,
        symptoms: List[str],
        top_k: int = 10,
        min_similarity: float = 0.70
    ) -> SearchResult:
        """
        Search for drug recommendations based on symptoms.
        Mode 1: Symptom → Disease → Similar Drugs
        
        Args:
            symptoms: List of symptom names (e.g., ["fever", "cough"])
            top_k: Number of top recommendations to return
            min_similarity: Minimum similarity threshold (default 0.70)
            
        Returns:
            SearchResult with drug recommendations and explanations
            
        Example:
            >>> service = SimilarityMedicineService()
            >>> result = service.search_by_symptom(["fever", "headache"])
            >>> for drug in result.drug_recommendations:
            ...     print(f"{drug.drug_name}: {drug.similarity_score:.1%}")
        """
        logger.info(f"Searching by symptoms: {symptoms}")
        
        # Step 1: Find conditions matching symptoms
        conditions = self.sparql_service.find_conditions_by_symptom(
            symptoms, 
            limit=20
        )
        
        if not conditions:
            logger.warning(f"No conditions found for symptoms: {symptoms}")
            return SearchResult(
                query=", ".join(symptoms),
                query_type="symptom",
                identified_conditions=[],
                drug_recommendations=[],
                total_results=0,
                search_metadata={
                    "symptoms": symptoms,
                    "conditions_found": 0,
                    "drugs_found": 0
                }
            )
        
        logger.info(f"Found {len(conditions)} conditions matching symptoms")
        
        # Step 2: For each condition, find drugs that treat it
        all_drug_recommendations = []
        identified_conditions = []
        
        for condition in conditions[:5]:  # Top 5 conditions
            condition_id = condition['condition_id']
            condition_name = condition['name']
            
            identified_conditions.append({
                'condition_id': condition_id,
                'name': condition_name,
                'matched_symptoms': condition['matched_symptoms']
            })
            
            # Get drugs that treat this condition
            drugs = self._find_drugs_for_condition(
                condition_id,
                condition_name,
                min_similarity
            )
            
            all_drug_recommendations.extend(drugs)
        
        # Step 3: Deduplicate and rank by similarity
        unique_drugs = self._deduplicate_drugs(all_drug_recommendations)
        ranked_drugs = sorted(
            unique_drugs,
            key=lambda d: d.similarity_score,
            reverse=True
        )[:top_k]
        
        logger.info(f"Returning {len(ranked_drugs)} drug recommendations")
        
        return SearchResult(
            query=", ".join(symptoms),
            query_type="symptom",
            identified_conditions=identified_conditions,
            drug_recommendations=ranked_drugs,
            total_results=len(ranked_drugs),
            search_metadata={
                "symptoms": symptoms,
                "conditions_found": len(conditions),
                "drugs_found": len(ranked_drugs),
                "threshold": min_similarity
            }
        )
    
    def search_by_disease(
        self,
        disease_name: str,
        disease_id: Optional[str] = None,
        top_k: int = 10,
        min_similarity: float = 0.70
    ) -> SearchResult:
        """
        Search for drug recommendations for a specific disease.
        Mode 2: Disease → Similar Drugs
        
        Args:
            disease_name: Name of the disease (e.g., "diabetes")
            disease_id: Optional Wikidata ID (e.g., "Q12206")
            top_k: Number of recommendations
            min_similarity: Minimum similarity threshold
            
        Returns:
            SearchResult with drug recommendations
            
        Example:
            >>> service = SimilarityMedicineService()
            >>> result = service.search_by_disease("diabetes", "Q12206")
        """
        logger.info(f"Searching for disease: {disease_name} ({disease_id})")
        
        # If no disease_id provided, search for it by name
        if not disease_id:
            logger.info(f"No disease ID provided, searching by name: {disease_name}")
            # Try to find disease ID using the disease name directly as a condition
            # This allows searching by common disease names like "diabetes", "asthma", etc.
            drugs = self.sparql_service.find_medicines_by_condition(
                disease_name,
                limit=15
            )
            
            if not drugs:
                logger.warning(f"No drugs found for disease: {disease_name}")
                return SearchResult(
                    query=disease_name,
                    query_type="disease",
                    identified_conditions=[],
                    drug_recommendations=[],
                    total_results=0,
                    search_metadata={
                        "searched_by": "name",
                        "message": f"No drugs found for '{disease_name}'. Try providing the Wikidata ID for more accurate results."
                    }
                )
            
            # Process drugs found by name
            recommendations = []
            for drug in drugs:
                drug_id = drug['drug_id']
                drug_name = drug['name']
                
                # Base score for direct matches
                base_score = 0.90
                
                if base_score >= min_similarity:
                    recommendations.append(
                        DrugRecommendation(
                            drug_id=drug_id,
                            drug_name=drug_name,
                            similarity_score=base_score,
                            treats_conditions=[disease_name],
                            explanation=f"{drug_name} is used to treat {disease_name}.",
                            similar_drugs=[],
                            properties={
                                'formula': drug.get('chemical_formula'),
                                'atc_code': drug.get('atc_code'),
                                'description': drug.get('description')
                            }
                        )
                    )
            
            # Sort and limit results
            ranked_drugs = sorted(
                recommendations,
                key=lambda d: d.similarity_score,
                reverse=True
            )[:top_k]
            
            logger.info(f"Found {len(ranked_drugs)} drugs for {disease_name} (searched by name)")
            
            return SearchResult(
                query=disease_name,
                query_type="disease",
                identified_conditions=[{
                    'condition_id': None,
                    'name': disease_name,
                    'searched_by': 'name'
                }],
                drug_recommendations=ranked_drugs,
                total_results=len(ranked_drugs),
                search_metadata={
                    "searched_by": "name",
                    "drugs_found": len(ranked_drugs),
                    "threshold": min_similarity
                }
            )
        
        # Get drugs for this disease using the provided ID
        drugs = self._find_drugs_for_condition(
            disease_id,
            disease_name,
            min_similarity
        )
        
        # Get related conditions for context
        related_conditions = self.sparql_service.get_related_conditions(
            disease_id,
            max_hops=2,
            limit=10
        )
        
        # Rank by similarity
        ranked_drugs = sorted(
            drugs,
            key=lambda d: d.similarity_score,
            reverse=True
        )[:top_k]
        
        logger.info(f"Found {len(ranked_drugs)} drug recommendations for {disease_name}")
        
        return SearchResult(
            query=disease_name,
            query_type="disease",
            identified_conditions=[{
                'condition_id': disease_id,
                'name': disease_name,
                'related_count': len(related_conditions)
            }],
            drug_recommendations=ranked_drugs,
            total_results=len(ranked_drugs),
            search_metadata={
                "disease_id": disease_id,
                "drugs_found": len(ranked_drugs),
                "related_conditions": len(related_conditions),
                "threshold": min_similarity
            }
        )
    
    def find_similar_drugs(
        self,
        drug_id: str,
        drug_name: str,
        top_k: int = 5,
        min_similarity: float = 0.70
    ) -> List[SimilarityResult]:
        """
        Find drugs similar to a given drug.
        Uses drug class, active ingredients, and conditions treated.
        
        Args:
            drug_id: Wikidata ID of the drug
            drug_name: Name of the drug
            top_k: Number of similar drugs to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar drugs with similarity scores
        """
        logger.info(f"Finding drugs similar to: {drug_name} ({drug_id})")
        
        # Get drug details
        drug_details = self.sparql_service.get_medicine_details(drug_id)
        
        if not drug_details:
            logger.warning(f"No details found for drug: {drug_id}")
            return []
        
        # Get conditions this drug treats
        conditions = drug_details.get('medical_conditions', [])
        
        if not conditions:
            logger.warning(f"No conditions found for drug: {drug_id}")
            return []
        
        # Find other drugs that treat the same conditions
        similar_drugs = []
        
        for condition in conditions[:3]:  # Top 3 conditions
            # Search for drugs treating this condition
            condition_drugs = self.sparql_service.find_medicines_by_condition(
                condition,
                limit=10
            )
            
            for candidate in condition_drugs:
                if candidate['drug_id'] != drug_id:
                    similar_drugs.append({
                        'drug_id': candidate['drug_id'],
                        'name': candidate['name'],
                        'common_condition': condition,
                        'similarity_score': 0.85  # Base score for same condition
                    })
        
        # Deduplicate and rank
        unique_similar = {}
        for drug in similar_drugs:
            drug_id_key = drug['drug_id']
            if drug_id_key not in unique_similar:
                unique_similar[drug_id_key] = drug
            else:
                # Increase score if multiple conditions match
                unique_similar[drug_id_key]['similarity_score'] += 0.05
        
        # Convert to list and sort
        result = sorted(
            unique_similar.values(),
            key=lambda d: d['similarity_score'],
            reverse=True
        )[:top_k]
        
        logger.info(f"Found {len(result)} similar drugs")
        return result
    
    def _find_drugs_for_condition(
        self,
        condition_id: str,
        condition_name: str,
        min_similarity: float
    ) -> List[DrugRecommendation]:
        """
        Find drugs that treat a specific condition.
        Internal method used by search_by_symptom and search_by_disease.
        
        Args:
            condition_id: Wikidata condition ID
            condition_name: Name of the condition
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of drug recommendations
        """
        # Direct query for drugs treating this condition
        drugs = self.sparql_service.find_medicines_by_condition(
            condition_name,
            limit=15
        )
        
        if not drugs:
            return []
        
        recommendations = []
        
        for drug in drugs:
            drug_id = drug['drug_id']
            drug_name = drug['name']
            
            # Calculate base similarity score
            # Drugs directly treating the condition get high score
            base_score = 0.90
            
            # OPTIMIZATION: Don't find similar drugs during initial search
            # This was causing query explosion and timeouts
            # Similar drugs can be found on-demand when user clicks a drug
            
            # Generate simple explanation
            explanation = f"{drug_name} is used to treat {condition_name}."
            
            # Only include if above threshold
            if base_score >= min_similarity:
                recommendations.append(
                    DrugRecommendation(
                        drug_id=drug_id,
                        drug_name=drug_name,
                        similarity_score=base_score,
                        treats_conditions=[condition_name],
                        explanation=explanation,
                        similar_drugs=[],  # Empty for now, can be populated later
                        properties={
                            'formula': drug.get('chemical_formula'),
                            'atc_code': drug.get('atc_code'),
                            'description': drug.get('description')
                        }
                    )
                )
        
        return recommendations
    
    def _deduplicate_drugs(
        self,
        drugs: List[DrugRecommendation]
    ) -> List[DrugRecommendation]:
        """
        Remove duplicate drugs, keeping the one with highest similarity.
        
        Args:
            drugs: List of drug recommendations
            
        Returns:
            Deduplicated list
        """
        unique_drugs = {}
        
        for drug in drugs:
            drug_id = drug.drug_id
            
            if drug_id not in unique_drugs:
                unique_drugs[drug_id] = drug
            else:
                # Keep the one with higher score
                if drug.similarity_score > unique_drugs[drug_id].similarity_score:
                    unique_drugs[drug_id] = drug
                else:
                    # Merge conditions
                    existing_conditions = set(unique_drugs[drug_id].treats_conditions)
                    new_conditions = set(drug.treats_conditions)
                    unique_drugs[drug_id].treats_conditions = list(
                        existing_conditions | new_conditions
                    )
        
        return list(unique_drugs.values())
    
    def _generate_explanation(
        self,
        drug_name: str,
        condition_name: str,
        similarity_score: float,
        similar_drugs: List[Dict[str, Any]]
    ) -> str:
        """
        Generate human-readable explanation for recommendation.
        
        Args:
            drug_name: Name of recommended drug
            condition_name: Condition being treated
            similarity_score: Similarity score
            similar_drugs: List of similar drugs
            
        Returns:
            Explanation string
        """
        explanation = f"{drug_name} treats {condition_name} (confidence: {similarity_score:.0%})"
        
        if similar_drugs:
            similar_names = [d['name'] for d in similar_drugs[:2]]
            explanation += f". Similar drugs: {', '.join(similar_names)}"
        
        return explanation


# Singleton instance
_similarity_medicine_service = None


def get_similarity_medicine_service() -> SimilarityMedicineService:
    """Get singleton instance of similarity medicine service."""
    global _similarity_medicine_service
    if _similarity_medicine_service is None:
        _similarity_medicine_service = SimilarityMedicineService()
    return _similarity_medicine_service
