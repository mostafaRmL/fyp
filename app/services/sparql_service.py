"""
SPARQL Service Module

This module handles all interactions with the Wikidata SPARQL endpoint.
Provides methods to query pharmaceutical data from the knowledge graph.
"""

import requests
from typing import List, Dict, Optional, Any
from app.config import settings
from app.utils.logger import get_logger
from app.utils.validators import SPARQLValidator

logger = get_logger(__name__)


class SPARQLService:
    """
    Service for querying Wikidata via SPARQL
    
    Handles construction and execution of SPARQL queries for
    pharmaceutical and medical data.
    """
    
    def __init__(self):
        """Initialize SPARQL service with configuration"""
        self.endpoint = settings.WIKIDATA_ENDPOINT
        self.headers = settings.sparql_headers
        self.timeout = settings.SPARQL_TIMEOUT
        self.validator = SPARQLValidator()
    
    def _execute_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Execute a SPARQL query against Wikidata endpoint
        
        Args:
            query: SPARQL query string
            
        Returns:
            Query results as dictionary, None on error
        """
        try:
            logger.info("Executing SPARQL query")
            logger.debug(f"Query: {query[:200]}...")  # Log first 200 chars
            
            response = requests.post(
                self.endpoint,
                data={'query': query},
                headers=self.headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            results = response.json()
            logger.info(f"Query successful, returned {len(results.get('results', {}).get('bindings', []))} results")
            
            return results
            
        except requests.exceptions.Timeout:
            logger.error(f"SPARQL query timeout after {self.timeout} seconds")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"SPARQL query failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in SPARQL query: {str(e)}")
            return None
    
    def find_medicines_by_condition(self, condition: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find medicines that treat a specific medical condition
        
        Args:
            condition: Medical condition name (e.g., "Pain", "Fever")
            limit: Maximum number of results to return
            
        Returns:
            List of medicine dictionaries with details
            
        Example:
            >>> service = SPARQLService()
            >>> medicines = service.find_medicines_by_condition("Pain", limit=5)
        """
        # Sanitize condition name
        condition = self.validator.sanitize_condition_name(condition)
        logger.info(f"Searching medicines for condition: {condition}")
        
        # SPARQL query to find drugs that treat the condition
        query = f"""
        SELECT DISTINCT ?drug ?drugLabel ?drugDescription ?formula ?mass ?atcCode ?conditionLabel
        WHERE {{
          # Find drugs that have "medical condition treated" property
          ?drug wdt:P2175 ?condition .
          
          # Filter by condition label containing our search term
          ?condition rdfs:label ?conditionLabel .
          FILTER(CONTAINS(LCASE(?conditionLabel), LCASE("{condition}")))
          FILTER(LANG(?conditionLabel) = "en")
          
          # Get drug properties
          OPTIONAL {{ ?drug wdt:P274 ?formula . }}        # Chemical formula
          OPTIONAL {{ ?drug wdt:P2067 ?mass . }}          # Molecular mass
          OPTIONAL {{ ?drug wdt:P267 ?atcCode . }}        # ATC code
          
          # Get labels and descriptions
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "en" .
          }}
        }}
        LIMIT {limit}
        """
        
        results = self._execute_query(query)
        
        if not results:
            logger.warning(f"No results found for condition: {condition}")
            return []
        
        # Parse and format results
        medicines = self._parse_medicine_results(results)
        logger.info(f"Found {len(medicines)} medicines for condition: {condition}")
        
        return medicines
    
    def get_medicine_details(self, wikidata_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific medicine
        
        Args:
            wikidata_id: Wikidata entity ID (e.g., Q18216 for Aspirin)
            
        Returns:
            Dictionary with medicine details, None if not found
        """
        if not self.validator.is_valid_wikidata_id(wikidata_id):
            logger.error(f"Invalid Wikidata ID: {wikidata_id}")
            return None
        
        logger.info(f"Fetching details for medicine: {wikidata_id}")
        
        query = f"""
        SELECT ?drugLabel ?drugDescription ?formula ?mass ?atcCode 
               (GROUP_CONCAT(DISTINCT ?conditionLabel; separator=", ") AS ?conditions)
        WHERE {{
          BIND(wd:{wikidata_id} AS ?drug)
          
          # Get properties
          OPTIONAL {{ ?drug wdt:P274 ?formula . }}
          OPTIONAL {{ ?drug wdt:P2067 ?mass . }}
          OPTIONAL {{ ?drug wdt:P267 ?atcCode . }}
          
          # Get conditions treated
          OPTIONAL {{
            ?drug wdt:P2175 ?condition .
            ?condition rdfs:label ?conditionLabel .
            FILTER(LANG(?conditionLabel) = "en")
          }}
          
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "en" .
          }}
        }}
        GROUP BY ?drugLabel ?drugDescription ?formula ?mass ?atcCode
        """
        
        results = self._execute_query(query)
        
        if not results or not results.get('results', {}).get('bindings'):
            logger.warning(f"No details found for medicine: {wikidata_id}")
            return None
        
        binding = results['results']['bindings'][0]
        
        medicine = {
            'drug_id': wikidata_id,
            'name': binding.get('drugLabel', {}).get('value', 'Unknown'),
            'description': binding.get('drugDescription', {}).get('value'),
            'chemical_formula': binding.get('formula', {}).get('value'),
            'molecular_mass': binding.get('mass', {}).get('value'),
            'atc_code': binding.get('atcCode', {}).get('value'),
            'medical_conditions': self._parse_conditions(binding.get('conditions', {}).get('value', ''))
        }
        
        return medicine
    
    def search_medicines_by_name(self, name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for medicines by name
        
        Args:
            name: Medicine name or partial name
            limit: Maximum number of results
            
        Returns:
            List of matching medicines
        """
        logger.info(f"Searching medicines by name: {name}")
        
        query = f"""
        SELECT DISTINCT ?drug ?drugLabel ?drugDescription ?formula ?atcCode
        WHERE {{
          # Search for drugs with matching labels
          ?drug rdfs:label ?drugLabel .
          FILTER(CONTAINS(LCASE(?drugLabel), LCASE("{name}")))
          FILTER(LANG(?drugLabel) = "en")
          
          # Ensure it's a medication
          ?drug wdt:P31/wdt:P279* wd:Q12140 .  # Instance of pharmaceutical drug
          
          # Get properties
          OPTIONAL {{ ?drug wdt:P274 ?formula . }}
          OPTIONAL {{ ?drug wdt:P267 ?atcCode . }}
          
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "en" .
          }}
        }}
        LIMIT {limit}
        """
        
        results = self._execute_query(query)
        
        if not results:
            return []
        
        medicines = self._parse_medicine_results(results)
        logger.info(f"Found {len(medicines)} medicines matching: {name}")
        
        return medicines
    
    def find_conditions_by_symptom(self, symptoms: List[str], limit: int = 20) -> List[Dict[str, Any]]:
        """
        Find medical conditions that match given symptoms.
        Enhanced for v2.0 similarity-based search.
        
        Args:
            symptoms: List of symptom names (e.g., ["fever", "cough", "headache"])
            limit: Maximum number of results
            
        Returns:
            List of conditions with matching symptom count
            
        Example:
            >>> service = SPARQLService()
            >>> conditions = service.find_conditions_by_symptom(["fever", "cough"])
        """
        logger.info(f"Searching conditions by symptoms: {symptoms}")
        
        # Build symptom filter for SPARQL - search by label substring
        symptom_pattern = "|".join([s.lower() for s in symptoms])
        
        # Simplified query without transitive properties (which cause timeouts)
        query = f"""
        SELECT DISTINCT ?condition ?conditionLabel ?symptomLabel
        WHERE {{
          # Find conditions that have symptoms
          ?condition wdt:P780 ?symptom .
          
          # Get symptom label
          ?symptom rdfs:label ?symptomLabel .
          FILTER(LANG(?symptomLabel) = "en")
          
          # Match symptom names (case-insensitive)
          FILTER(REGEX(LCASE(STR(?symptomLabel)), "({symptom_pattern})", "i"))
          
          # Get condition label
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "en" .
          }}
        }}
        LIMIT {limit}
        """
        
        results = self._execute_query(query)
        
        if not results:
            logger.warning(f"No conditions found for symptoms: {symptoms}")
            return []
        
        # Group by condition and count matching symptoms
        condition_map = {}
        bindings = results.get('results', {}).get('bindings', [])
        
        for binding in bindings:
            condition_uri = binding.get('condition', {}).get('value', '')
            condition_id = condition_uri.split('/')[-1] if condition_uri else None
            
            if not condition_id:
                continue
            
            condition_name = binding.get('conditionLabel', {}).get('value', 'Unknown')
            symptom_name = binding.get('symptomLabel', {}).get('value', '')
            
            if condition_id not in condition_map:
                condition_map[condition_id] = {
                    'condition_id': condition_id,
                    'name': condition_name,
                    'matched_symptoms': 0,
                    'symptom_list': []
                }
            
            condition_map[condition_id]['matched_symptoms'] += 1
            if symptom_name:
                condition_map[condition_id]['symptom_list'].append(symptom_name)
        
        # Convert to list and sort by matched symptoms
        conditions = sorted(
            condition_map.values(),
            key=lambda x: x['matched_symptoms'],
            reverse=True
        )
        
        logger.info(f"Found {len(conditions)} conditions matching symptoms")
        return conditions
    
    def get_related_conditions(self, condition_id: str, max_hops: int = 2, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Find conditions related to the given condition through ontology relationships.
        Uses subclass hierarchy and related disease classes.
        
        Args:
            condition_id: Wikidata ID of the condition (e.g., "Q12206" for diabetes)
            max_hops: Maximum relationship hops (1-3)
            limit: Maximum number of results
            
        Returns:
            List of related conditions with relationship info
            
        Example:
            >>> service = SPARQLService()
            >>> related = service.get_related_conditions("Q12206", max_hops=2)
        """
        if not self.validator.is_valid_wikidata_id(condition_id):
            logger.error(f"Invalid Wikidata ID: {condition_id}")
            return []
        
        logger.info(f"Finding related conditions for: {condition_id} (max {max_hops} hops)")
        
        # Adjust property path based on max_hops
        if max_hops == 1:
            path = "wdt:P279"
        elif max_hops == 2:
            path = "wdt:P279/wdt:P279?"
        else:  # 3 or more
            path = "wdt:P279+"
        
        query = f"""
        SELECT DISTINCT ?relatedCondition ?relatedConditionLabel ?parent ?parentLabel
        WHERE {{
          # Find parent classes of source condition
          wd:{condition_id} {path} ?parent .
          
          # Find other conditions with same parent
          ?relatedCondition {path} ?parent .
          ?relatedCondition wdt:P31 wd:Q12136 .  # Instance of disease
          
          # Exclude source condition
          FILTER(?relatedCondition != wd:{condition_id})
          
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "en" .
          }}
        }}
        LIMIT {limit}
        """
        
        results = self._execute_query(query)
        
        if not results:
            logger.warning(f"No related conditions found for: {condition_id}")
            return []
        
        related_conditions = []
        bindings = results.get('results', {}).get('bindings', [])
        
        for binding in bindings:
            related_uri = binding.get('relatedCondition', {}).get('value', '')
            related_id = related_uri.split('/')[-1] if related_uri else None
            parent_uri = binding.get('parent', {}).get('value', '')
            parent_id = parent_uri.split('/')[-1] if parent_uri else None
            
            if not related_id:
                continue
            
            condition = {
                'condition_id': related_id,
                'name': binding.get('relatedConditionLabel', {}).get('value', 'Unknown'),
                'common_parent_id': parent_id,
                'common_parent': binding.get('parentLabel', {}).get('value', 'Unknown'),
                'relationship_type': 'subclass'
            }
            related_conditions.append(condition)
        
        logger.info(f"Found {len(related_conditions)} related conditions")
        return related_conditions
    
    def get_condition_relationships(self, condition_id: str) -> Dict[str, Any]:
        """
        Get comprehensive relationship information for a condition.
        Includes symptoms, parent classes, treated by drugs, etc.
        
        Args:
            condition_id: Wikidata ID of the condition
            
        Returns:
            Dictionary with relationship categories
            
        Example:
            >>> service = SPARQLService()
            >>> relationships = service.get_condition_relationships("Q12206")
            >>> print(relationships['symptoms'])  # List of symptoms
            >>> print(relationships['parent_classes'])  # Parent disease classes
            >>> print(relationships['treatments'])  # Drugs that treat this
        """
        if not self.validator.is_valid_wikidata_id(condition_id):
            logger.error(f"Invalid Wikidata ID: {condition_id}")
            return {}
        
        logger.info(f"Fetching relationships for condition: {condition_id}")
        
        query = f"""
        SELECT ?relationshipType ?entity ?entityLabel
        WHERE {{
          {{
            # Symptoms
            wd:{condition_id} wdt:P780 ?entity .
            BIND("symptom" AS ?relationshipType)
          }}
          UNION
          {{
            # Parent classes (subclass of)
            wd:{condition_id} wdt:P279 ?entity .
            BIND("parent_class" AS ?relationshipType)
          }}
          UNION
          {{
            # Treatments (drugs that treat this condition)
            ?entity wdt:P2175 wd:{condition_id} .
            ?entity wdt:P31/wdt:P279* wd:Q12140 .  # Is a medication
            BIND("treatment" AS ?relationshipType)
          }}
          UNION
          {{
            # Causative agents
            wd:{condition_id} wdt:P828 ?entity .
            BIND("causative_agent" AS ?relationshipType)
          }}
          
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "en" .
          }}
        }}
        """
        
        results = self._execute_query(query)
        
        if not results:
            logger.warning(f"No relationships found for condition: {condition_id}")
            return {
                'condition_id': condition_id,
                'symptoms': [],
                'parent_classes': [],
                'treatments': [],
                'causative_agents': []
            }
        
        # Organize results by relationship type
        relationships = {
            'condition_id': condition_id,
            'symptoms': [],
            'parent_classes': [],
            'treatments': [],
            'causative_agents': []
        }
        
        bindings = results.get('results', {}).get('bindings', [])
        
        for binding in bindings:
            rel_type = binding.get('relationshipType', {}).get('value', '')
            entity_uri = binding.get('entity', {}).get('value', '')
            entity_id = entity_uri.split('/')[-1] if entity_uri else None
            entity_label = binding.get('entityLabel', {}).get('value', 'Unknown')
            
            if not entity_id:
                continue
            
            entity_info = {
                'entity_id': entity_id,
                'name': entity_label
            }
            
            # Add to appropriate category
            if rel_type == 'symptom':
                relationships['symptoms'].append(entity_info)
            elif rel_type == 'parent_class':
                relationships['parent_classes'].append(entity_info)
            elif rel_type == 'treatment':
                relationships['treatments'].append(entity_info)
            elif rel_type == 'causative_agent':
                relationships['causative_agents'].append(entity_info)
        
        logger.info(f"Found {len(relationships['symptoms'])} symptoms, "
                   f"{len(relationships['parent_classes'])} parent classes, "
                   f"{len(relationships['treatments'])} treatments, "
                   f"{len(relationships['causative_agents'])} causative agents")
        
        return relationships
    
    def _parse_medicine_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse SPARQL results into medicine dictionaries
        
        Args:
            results: Raw SPARQL query results
            
        Returns:
            List of formatted medicine dictionaries
        """
        bindings = results.get('results', {}).get('bindings', [])
        medicines = []
        
        for binding in bindings:
            # Extract Wikidata ID from drug URI
            drug_uri = binding.get('drug', {}).get('value', '')
            drug_id = drug_uri.split('/')[-1] if drug_uri else None
            
            if not drug_id or not self.validator.is_valid_wikidata_id(drug_id):
                continue
            
            medicine = {
                'drug_id': drug_id,
                'name': binding.get('drugLabel', {}).get('value', 'Unknown'),
                'description': binding.get('drugDescription', {}).get('value'),
                'chemical_formula': binding.get('formula', {}).get('value'),
                'molecular_mass': binding.get('mass', {}).get('value'),
                'atc_code': binding.get('atcCode', {}).get('value'),
                'medical_conditions': self._parse_conditions(
                    binding.get('conditionLabel', {}).get('value', '')
                )
            }
            
            medicines.append(medicine)
        
        return medicines
    
    def _parse_conditions(self, conditions_str: str) -> List[str]:
        """
        Parse comma-separated conditions string into list
        
        Args:
            conditions_str: Comma-separated conditions
            
        Returns:
            List of condition names
        """
        if not conditions_str:
            return []
        
        conditions = [c.strip() for c in conditions_str.split(',')]
        return [c for c in conditions if c]  # Remove empty strings


# Singleton instance
_sparql_service_instance: Optional[SPARQLService] = None


def get_sparql_service() -> SPARQLService:
    """
    Get singleton instance of SPARQL service
    
    Returns:
        SPARQLService instance
    """
    global _sparql_service_instance
    
    if _sparql_service_instance is None:
        _sparql_service_instance = SPARQLService()
    
    return _sparql_service_instance