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


# ============================================================================
# V2 API Models (Similarity-based Search)
# ============================================================================

class SymptomSearchRequest(BaseModel):
    """
    Request model for symptom-based similarity search (v2)
    
    Attributes:
        symptoms: List of symptoms to search for
        top_k: Maximum number of drug recommendations to return
        min_similarity: Minimum similarity threshold (0.0 to 1.0)
    """
    symptoms: List[str] = Field(
        ...,
        min_length=1,
        description="List of symptoms (e.g., ['fever', 'headache', 'nausea'])",
        examples=[["fever", "headache"], ["chest pain", "shortness of breath"]]
    )
    top_k: int = Field(
        5,
        ge=1,
        le=20,
        description="Maximum number of drug recommendations (1-20)"
    )
    min_similarity: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold (0.0-1.0)"
    )
    
    @field_validator('symptoms')
    @classmethod
    def validate_symptoms(cls, v: List[str]) -> List[str]:
        """Validate and clean symptoms list"""
        if not v:
            raise ValueError("Symptoms list cannot be empty")
        # Clean and validate each symptom
        cleaned = [s.strip() for s in v if s and s.strip()]
        if not cleaned:
            raise ValueError("Symptoms list must contain at least one valid symptom")
        return cleaned


class DiseaseSearchRequest(BaseModel):
    """
    Request model for disease-based drug search (v2)
    
    Attributes:
        disease_name: Name of the disease
        disease_id: Optional Wikidata ID for the disease
        top_k: Maximum number of drug recommendations
        min_similarity: Minimum similarity threshold
    """
    disease_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Name of the disease or medical condition",
        examples=["Type 2 Diabetes", "Hypertension", "Asthma"]
    )
    disease_id: Optional[str] = Field(
        None,
        description="Wikidata entity ID (e.g., Q3025883)",
        examples=["Q3025883", "Q12155"]
    )
    top_k: int = Field(
        5,
        ge=1,
        le=20,
        description="Maximum number of drug recommendations"
    )
    min_similarity: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold"
    )
    
    @field_validator('disease_name')
    @classmethod
    def validate_disease_name(cls, v: str) -> str:
        """Validate and clean disease name"""
        v = v.strip()
        if not v:
            raise ValueError("Disease name cannot be empty")
        return v


class SimilarDrugsRequest(BaseModel):
    """
    Request model for finding similar drugs (v2)
    
    Attributes:
        drug_name: Name of the reference drug
        drug_id: Optional Wikidata ID for the drug
        top_k: Maximum number of similar drugs to return
        min_similarity: Minimum similarity threshold
    """
    drug_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Name of the drug to find similar drugs for",
        examples=["Aspirin", "Metformin", "Ibuprofen"]
    )
    drug_id: Optional[str] = Field(
        None,
        description="Wikidata entity ID (e.g., Q18216)",
        examples=["Q18216", "Q19484"]
    )
    top_k: int = Field(
        5,
        ge=1,
        le=20,
        description="Maximum number of similar drugs"
    )
    min_similarity: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold"
    )
    
    @field_validator('drug_name')
    @classmethod
    def validate_drug_name(cls, v: str) -> str:
        """Validate and clean drug name"""
        v = v.strip()
        if not v:
            raise ValueError("Drug name cannot be empty")
        return v


class DrugRecommendationResponse(BaseModel):
    """
    Individual drug recommendation with similarity details (v2)
    
    Attributes:
        drug_id: Wikidata entity ID
        drug_name: Name of the drug
        similarity_score: Similarity score (0.0-1.0)
        explanation: Human-readable explanation of why this drug was recommended
        treats_conditions: List of conditions this drug treats
    """
    drug_id: str = Field(..., description="Wikidata entity ID")
    drug_name: str = Field(..., description="Drug name")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    explanation: str = Field(..., description="Explanation for recommendation")
    treats_conditions: List[str] = Field(
        default_factory=list,
        description="List of conditions this drug treats"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "drug_id": "Q18216",
                "drug_name": "Aspirin",
                "similarity_score": 0.95,
                "explanation": "Highly effective for treating pain and fever",
                "treats_conditions": ["Pain", "Fever", "Inflammation"]
            }
        }


class SearchResultResponse(BaseModel):
    """
    Complete search result response for v2 API
    
    Attributes:
        success: Whether the search was successful
        query_type: Type of query (symptom, disease, or drug_similarity)
        query_input: Original user input
        recommendations: List of drug recommendations
        total_found: Total number of drugs found
        message: Additional information
        search_metadata: Metadata about the search
    """
    success: bool = Field(True, description="Success status")
    query_type: str = Field(
        ...,
        description="Type of search: symptom, disease, or drug_similarity"
    )
    query_input: dict = Field(..., description="Original query parameters")
    recommendations: List[DrugRecommendationResponse] = Field(
        default_factory=list,
        description="List of drug recommendations"
    )
    total_found: int = Field(0, description="Total number of recommendations")
    message: str = Field("", description="Additional information")
    search_metadata: Optional[dict] = Field(
        None,
        description="Additional search metadata (execution time, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "query_type": "symptom",
                "query_input": {
                    "symptoms": ["fever", "headache"],
                    "top_k": 5,
                    "min_similarity": 0.7
                },
                "recommendations": [
                    {
                        "drug_id": "Q18216",
                        "drug_name": "Aspirin",
                        "similarity_score": 0.95,
                        "explanation": "Highly effective for treating pain and fever",
                        "treats_conditions": ["Pain", "Fever"]
                    }
                ],
                "total_found": 1,
                "message": "Found 1 drug recommendation(s)",
                "search_metadata": {
                    "execution_time_ms": 1250,
                    "conditions_analyzed": 2
                }
            }
        }