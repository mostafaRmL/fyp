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