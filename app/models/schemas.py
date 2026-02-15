"""
Data Models and Schemas

This module defines all Pydantic models for request/response validation.
Ensures type safety and data validation throughout the application.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Request Models
# ============================================================================

class SymptomsRequest(BaseModel):
    """
    Request model for symptom analysis
    
    Attributes:
        symptoms: User's description of symptoms or health concerns
    """
    symptoms: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Description of symptoms or health condition",
        examples=["I have a headache and fever", "Chest pain and difficulty breathing"]
    )
    
    @field_validator('symptoms')
    @classmethod
    def validate_symptoms(cls, v: str) -> str:
        """Validate and clean symptoms input"""
        v = v.strip()
        if not v:
            raise ValueError("Symptoms cannot be empty")
        return v


# ============================================================================
# Response Models
# ============================================================================

class MedicineInfo(BaseModel):
    """
    Detailed information about a medicine
    
    Attributes:
        drug_id: Wikidata entity ID
        name: Medicine name
        description: Brief description of the medicine
        chemical_formula: Chemical formula (if available)
        molecular_mass: Molecular mass (if available)
        atc_code: Anatomical Therapeutic Chemical code
        medical_conditions: List of conditions this medicine treats
    """
    drug_id: str = Field(..., description="Wikidata entity ID (e.g., Q18216)")
    name: str = Field(..., description="Medicine name")
    description: Optional[str] = Field(None, description="Medicine description")
    chemical_formula: Optional[str] = Field(None, description="Chemical formula")
    molecular_mass: Optional[str] = Field(None, description="Molecular mass")
    atc_code: Optional[str] = Field(None, description="ATC classification code")
    medical_conditions: List[str] = Field(
        default_factory=list,
        description="List of medical conditions treated"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "drug_id": "Q18216",
                "name": "Aspirin",
                "description": "Medication used to reduce pain, fever, or inflammation",
                "chemical_formula": "C9H8O4",
                "molecular_mass": "180.16 g/mol",
                "atc_code": "N02BA01",
                "medical_conditions": ["Pain", "Fever", "Inflammation"]
            }
        }


class AnalysisResult(BaseModel):
    """
    AI analysis result from symptoms
    
    Attributes:
        identified_conditions: Medical conditions identified from symptoms
        confidence: Confidence level (low, medium, high)
        reasoning: AI's reasoning process
    """
    identified_conditions: List[str] = Field(
        ...,
        description="List of identified medical conditions"
    )
    confidence: str = Field(
        ...,
        description="Confidence level: low, medium, high"
    )
    reasoning: str = Field(
        ...,
        description="Explanation of the analysis"
    )


class MedicineRecommendation(BaseModel):
    """
    Complete medicine recommendation response
    
    Attributes:
        user_symptoms: Original user input
        analysis: AI analysis result
        recommended_medicines: List of recommended medicines with details
        disclaimer: Medical disclaimer message
        success: Whether the request was successful
        message: Additional message or error information
    """
    user_symptoms: str = Field(..., description="Original user symptoms")
    analysis: Optional[AnalysisResult] = Field(None, description="AI analysis")
    recommended_medicines: List[MedicineInfo] = Field(
        default_factory=list,
        description="List of recommended medicines"
    )
    disclaimer: str = Field(
        default="This is for informational purposes only. Please consult a healthcare professional for medical advice.",
        description="Medical disclaimer"
    )
    success: bool = Field(True, description="Whether request was successful")
    message: str = Field("", description="Additional information or error message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_symptoms": "headache and fever",
                "analysis": {
                    "identified_conditions": ["Pain", "Fever"],
                    "confidence": "high",
                    "reasoning": "Common symptoms indicating pain and fever"
                },
                "recommended_medicines": [
                    {
                        "drug_id": "Q18216",
                        "name": "Aspirin",
                        "description": "Pain and fever reducer",
                        "chemical_formula": "C9H8O4",
                        "molecular_mass": "180.16 g/mol",
                        "atc_code": "N02BA01",
                        "medical_conditions": ["Pain", "Fever"]
                    }
                ],
                "disclaimer": "This is for informational purposes only...",
                "success": True,
                "message": "Found 1 relevant medicine(s)"
            }
        }


class ErrorResponse(BaseModel):
    """
    Error response model
    
    Attributes:
        success: Always False for errors
        error: Error type/category
        message: Detailed error message
        details: Additional error details
    """
    success: bool = Field(False, description="Success flag (always False)")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")


# ============================================================================
# Internal Models (for service layer communication)
# ============================================================================

class ConditionQuery(BaseModel):
    """
    Internal model for condition-based drug queries
    
    Attributes:
        condition: Medical condition to search for
        language: Query language (default: en)
    """
    condition: str = Field(..., description="Medical condition")
    language: str = Field("en", description="Language code")


class SPARQLResult(BaseModel):
    """
    Internal model for SPARQL query results
    
    Attributes:
        bindings: List of result bindings from SPARQL
        count: Number of results
    """
    bindings: List[dict] = Field(default_factory=list)
    count: int = Field(0, description="Number of results")