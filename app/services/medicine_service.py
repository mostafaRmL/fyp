"""
Medicine Service Module

This module orchestrates the LLM and SPARQL services to provide
complete medicine recommendations based on user symptoms.
"""

from typing import Dict, List, Optional, Any
from app.services.llm_service import get_llm_service
from app.services.sparql_service import get_sparql_service
from app.models.schemas import MedicineInfo, AnalysisResult, MedicineRecommendation
from app.utils.logger import get_logger
from app.utils.validators import ResponseValidator

logger = get_logger(__name__)


class MedicineService:
    """
    High-level service for medicine recommendations
    
    Coordinates symptom analysis (LLM) and medicine lookup (SPARQL)
    to provide comprehensive recommendations.
    """
    
    def __init__(self):
        """Initialize medicine service with dependencies"""
        self.llm_service = get_llm_service()
        self.sparql_service = get_sparql_service()
        self.validator = ResponseValidator()
        logger.info("Medicine Service initialized")
    
    def get_medicine_recommendations(self, symptoms: str) -> MedicineRecommendation:
        """
        Get medicine recommendations based on symptoms
        
        This is the main entry point for the service. It:
        1. Analyzes symptoms using AI
        2. Queries Wikidata for relevant medicines
        3. Formats and returns results
        
        Args:
            symptoms: User's symptom description
            
        Returns:
            MedicineRecommendation object with results
            
        Example:
            >>> service = MedicineService()
            >>> result = service.get_medicine_recommendations("headache and fever")
            >>> for medicine in result.recommended_medicines:
            ...     print(medicine.name)
        """
        logger.info("Processing medicine recommendation request")
        
        try:
            # Step 1: Analyze symptoms with AI
            analysis_result = self._analyze_symptoms(symptoms)
            
            if not analysis_result:
                return self._create_error_response(
                    symptoms,
                    "Unable to analyze symptoms. Please try rephrasing your symptoms."
                )
            
            # Step 2: Find medicines for identified conditions
            medicines = self._find_medicines_for_conditions(
                analysis_result['identified_conditions']
            )
            
            # Step 3: Format response
            response = self._format_response(
                symptoms,
                analysis_result,
                medicines
            )
            
            logger.info(f"Recommendation complete: {len(medicines)} medicines found")
            return response
            
        except Exception as e:
            logger.error(f"Error in get_medicine_recommendations: {str(e)}")
            return self._create_error_response(
                symptoms,
                "An error occurred while processing your request."
            )
    
    def _analyze_symptoms(self, symptoms: str) -> Optional[Dict[str, Any]]:
        """
        Analyze symptoms using LLM service
        
        Args:
            symptoms: User symptom description
            
        Returns:
            Analysis result dictionary or None
        """
        logger.info("Analyzing symptoms with AI")
        
        try:
            result = self.llm_service.analyze_symptoms(symptoms)
            
            if not result:
                logger.warning("AI analysis returned no results")
                return None
            
            if not result.get('identified_conditions'):
                logger.warning("No conditions identified from symptoms")
                return None
            
            logger.info(f"Identified conditions: {result['identified_conditions']}")
            return result
            
        except Exception as e:
            logger.error(f"Error during symptom analysis: {str(e)}")
            return None
    
    def _find_medicines_for_conditions(
        self, 
        conditions: List[str],
        limit_per_condition: int = 5
    ) -> List[MedicineInfo]:
        """
        Find medicines for multiple conditions
        
        Args:
            conditions: List of medical conditions
            limit_per_condition: Max medicines per condition
            
        Returns:
            List of MedicineInfo objects
        """
        logger.info(f"Searching medicines for {len(conditions)} conditions")
        
        all_medicines: Dict[str, MedicineInfo] = {}
        
        for condition in conditions:
            try:
                # Query SPARQL for medicines
                medicine_data = self.sparql_service.find_medicines_by_condition(
                    condition,
                    limit=limit_per_condition
                )
                
                # Convert to MedicineInfo objects
                for data in medicine_data:
                    # Validate data
                    is_valid, error = self.validator.validate_medicine_data(data)
                    if not is_valid:
                        logger.warning(f"Invalid medicine data: {error}")
                        continue
                    
                    # Use drug_id as key to prevent duplicates
                    drug_id = data['drug_id']
                    
                    if drug_id not in all_medicines:
                        # Clean data
                        clean_data = self.validator.filter_empty_values(data)
                        
                        # Create MedicineInfo object
                        medicine = MedicineInfo(**clean_data)
                        all_medicines[drug_id] = medicine
                        
            except Exception as e:
                logger.error(f"Error finding medicines for condition '{condition}': {str(e)}")
                continue
        
        medicines = list(all_medicines.values())
        logger.info(f"Found {len(medicines)} unique medicines")
        
        return medicines
    
    def _format_response(
        self,
        symptoms: str,
        analysis_result: Dict[str, Any],
        medicines: List[MedicineInfo]
    ) -> MedicineRecommendation:
        """
        Format the final recommendation response
        
        Args:
            symptoms: Original user symptoms
            analysis_result: AI analysis result
            medicines: List of medicine recommendations
            
        Returns:
            MedicineRecommendation object
        """
        # Create AnalysisResult object
        analysis = AnalysisResult(
            identified_conditions=analysis_result['identified_conditions'],
            confidence=analysis_result['confidence'],
            reasoning=analysis_result['reasoning']
        )
        
        # Create success message
        if medicines:
            message = f"Found {len(medicines)} relevant medicine(s) for your symptoms."
        else:
            message = "No medicines found in the database for the identified conditions. Please consult a healthcare professional."
        
        # Create recommendation object
        recommendation = MedicineRecommendation(
            user_symptoms=symptoms,
            analysis=analysis,
            recommended_medicines=medicines,
            success=True,
            message=message,
            disclaimer="This information is for educational purposes only and should not be considered medical advice. Always consult a qualified healthcare professional for proper diagnosis and treatment."
        )
        
        return recommendation
    
    def _create_error_response(
        self,
        symptoms: str,
        error_message: str
    ) -> MedicineRecommendation:
        """
        Create error response
        
        Args:
            symptoms: Original symptoms
            error_message: Error description
            
        Returns:
            MedicineRecommendation with error details
        """
        return MedicineRecommendation(
            user_symptoms=symptoms,
            analysis=None,
            recommended_medicines=[],
            success=False,
            message=error_message,
            disclaimer="Please try again or consult a healthcare professional."
        )
    
    def search_medicine_by_name(self, name: str) -> List[MedicineInfo]:
        """
        Search for medicines by name
        
        Args:
            name: Medicine name or partial name
            
        Returns:
            List of matching medicines
        """
        logger.info(f"Searching medicines by name: {name}")
        
        try:
            medicine_data = self.sparql_service.search_medicines_by_name(name)
            
            medicines = []
            for data in medicine_data:
                is_valid, _ = self.validator.validate_medicine_data(data)
                if is_valid:
                    clean_data = self.validator.filter_empty_values(data)
                    medicines.append(MedicineInfo(**clean_data))
            
            logger.info(f"Found {len(medicines)} medicines matching '{name}'")
            return medicines
            
        except Exception as e:
            logger.error(f"Error searching medicines by name: {str(e)}")
            return []
    
    def get_medicine_details(self, drug_id: str) -> Optional[MedicineInfo]:
        """
        Get detailed information about a specific medicine
        
        Args:
            drug_id: Wikidata entity ID (e.g., Q18216)
            
        Returns:
            MedicineInfo object or None
        """
        logger.info(f"Fetching medicine details: {drug_id}")
        
        try:
            data = self.sparql_service.get_medicine_details(drug_id)
            
            if not data:
                return None
            
            is_valid, error = self.validator.validate_medicine_data(data)
            if not is_valid:
                logger.error(f"Invalid medicine data: {error}")
                return None
            
            clean_data = self.validator.filter_empty_values(data)
            return MedicineInfo(**clean_data)
            
        except Exception as e:
            logger.error(f"Error fetching medicine details: {str(e)}")
            return None


# Singleton instance
_medicine_service_instance: Optional[MedicineService] = None


def get_medicine_service() -> MedicineService:
    """
    Get singleton instance of Medicine service
    
    Returns:
        MedicineService instance
    """
    global _medicine_service_instance
    
    if _medicine_service_instance is None:
        _medicine_service_instance = MedicineService()
    
    return _medicine_service_instance