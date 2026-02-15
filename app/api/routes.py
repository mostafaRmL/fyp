"""
API Routes Module

This module defines all API endpoints for the medical assistant application.
Handles HTTP requests and coordinates with service layer.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Optional
from app.models.schemas import (
    SymptomsRequest,
    MedicineRecommendation,
    ErrorResponse,
    MedicineInfo
)
from app.services.medicine_service import get_medicine_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Create API router
router = APIRouter(
    prefix="/api",
    tags=["medical-assistant"]
)


@router.get("/")
async def root():
    """
    API root endpoint - Health check
    
    Returns:
        Basic API information
    """
    return {
        "name": "Medical Assistant API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "analyze": "/api/analyze",
            "search": "/api/search",
            "medicine": "/api/medicine/{drug_id}"
        }
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Health status of the API
    """
    return {
        "status": "healthy",
        "message": "API is running"
    }


@router.post(
    "/analyze",
    response_model=MedicineRecommendation,
    status_code=status.HTTP_200_OK,
    summary="Analyze symptoms and get medicine recommendations",
    description="Submit symptoms to get AI-powered analysis and medicine recommendations from knowledge graph"
)
async def analyze_symptoms(request: SymptomsRequest):
    """
    Analyze user symptoms and recommend medicines
    
    This endpoint:
    1. Validates user input
    2. Analyzes symptoms using AI
    3. Queries Wikidata for relevant medicines
    4. Returns comprehensive recommendations
    
    Args:
        request: SymptomsRequest containing user symptoms
        
    Returns:
        MedicineRecommendation with analysis and medicine list
        
    Raises:
        HTTPException: On validation or processing errors
        
    Example:
        POST /api/analyze
        {
            "symptoms": "I have a headache and fever"
        }
    """
    try:
        logger.info(f"Received symptom analysis request: {request.symptoms[:50]}...")
        
        # Get medicine service
        medicine_service = get_medicine_service()
        
        # Process request
        result = medicine_service.get_medicine_recommendations(request.symptoms)
        
        # Log result
        if result.success:
            logger.info(f"Request successful: {len(result.recommended_medicines)} medicines found")
        else:
            logger.warning(f"Request failed: {result.message}")
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in analyze_symptoms: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing your request"
        )


@router.get(
    "/search",
    response_model=List[MedicineInfo],
    summary="Search medicines by name",
    description="Search for medicines in the knowledge graph by name"
)
async def search_medicines(
    name: str,
    limit: int = 10
):
    """
    Search for medicines by name
    
    Args:
        name: Medicine name or partial name to search for
        limit: Maximum number of results (default: 10, max: 50)
        
    Returns:
        List of matching medicines
        
    Raises:
        HTTPException: On validation or processing errors
        
    Example:
        GET /api/search?name=aspirin&limit=5
    """
    try:
        # Validate input
        if not name or len(name.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medicine name must be at least 2 characters"
            )
        
        # Limit constraint
        if limit < 1 or limit > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 50"
            )
        
        logger.info(f"Searching medicines: name='{name}', limit={limit}")
        
        # Get service and search
        medicine_service = get_medicine_service()
        medicines = medicine_service.search_medicine_by_name(name)
        
        # Apply limit
        medicines = medicines[:limit]
        
        logger.info(f"Found {len(medicines)} medicines")
        return medicines
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search_medicines: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while searching for medicines"
        )


@router.get(
    "/medicine/{drug_id}",
    response_model=MedicineInfo,
    summary="Get medicine details",
    description="Get detailed information about a specific medicine by Wikidata ID"
)
async def get_medicine_details(drug_id: str):
    """
    Get detailed information about a specific medicine
    
    Args:
        drug_id: Wikidata entity ID (e.g., Q18216 for Aspirin)
        
    Returns:
        MedicineInfo with complete details
        
    Raises:
        HTTPException: If medicine not found or invalid ID
        
    Example:
        GET /api/medicine/Q18216
    """
    try:
        logger.info(f"Fetching medicine details: {drug_id}")
        
        # Get service and fetch details
        medicine_service = get_medicine_service()
        medicine = medicine_service.get_medicine_details(drug_id)
        
        if not medicine:
            logger.warning(f"Medicine not found: {drug_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medicine with ID '{drug_id}' not found"
            )
        
        logger.info(f"Medicine details retrieved: {medicine.name}")
        return medicine
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching medicine details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching medicine details"
        )


@router.post(
    "/test-connection",
    summary="Test external service connections",
    description="Test connectivity to Groq AI and Wikidata SPARQL endpoint"
)
async def test_connection():
    """
    Test connection to external services
    
    Returns:
        Connection status for LLM and SPARQL services
        
    Example:
        POST /api/test-connection
    """
    try:
        from app.services.llm_service import get_llm_service
        from app.services.sparql_service import get_sparql_service
        
        results = {
            "llm_service": "unknown",
            "sparql_service": "unknown"
        }
        
        # Test LLM service
        try:
            llm_service = get_llm_service()
            results["llm_service"] = "connected"
        except Exception as e:
            results["llm_service"] = f"error: {str(e)}"
            logger.error(f"LLM service connection failed: {str(e)}")
        
        # Test SPARQL service
        try:
            sparql_service = get_sparql_service()
            # Try a simple query
            test_result = sparql_service.search_medicines_by_name("aspirin", limit=1)
            results["sparql_service"] = "connected"
        except Exception as e:
            results["sparql_service"] = f"error: {str(e)}"
            logger.error(f"SPARQL service connection failed: {str(e)}")
        
        return {
            "status": "test_complete",
            "services": results
        }
        
    except Exception as e:
        logger.error(f"Error in test_connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Connection test failed"
        )