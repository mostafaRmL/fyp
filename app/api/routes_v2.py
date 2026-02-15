"""
API Routes V2 - Similarity-based Search

This module defines V2 API endpoints using the ontology-based similarity engine.
Implements three search modes:
  1. Symptom-based search
  2. Disease-based search
  3. Drug similarity search
"""

import time
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Optional
from app.models.schemas import (
    SymptomSearchRequest,
    DiseaseSearchRequest,
    SimilarDrugsRequest,
    SearchResultResponse,
    DrugRecommendationResponse,
    ErrorResponse
)
from app.services.similarity_medicine_service import get_similarity_medicine_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Create API router for v2
router = APIRouter(
    prefix="/api/v2",
    tags=["similarity-search"]
)


@router.get("/")
async def root():
    """
    V2 API root endpoint
    
    Returns:
        API information and available endpoints
    """
    return {
        "name": "Medical Assistant API v2.0",
        "version": "2.0.0",
        "description": "Ontology-based similarity search for drug recommendations",
        "features": [
            "Symptom-based drug search",
            "Disease-based drug search",
            "Drug-to-drug similarity",
            "Graph-based scoring algorithm",
            "Multi-hop ontology traversal"
        ],
        "endpoints": {
            "symptom_search": "/api/v2/search/symptom",
            "disease_search": "/api/v2/search/disease",
            "drug_similarity": "/api/v2/drugs/similar"
        },
        "algorithm": {
            "type": "BFS Graph Traversal",
            "scoring": "Path-based weighted similarity",
            "threshold": 0.7,
            "max_hops": 3
        }
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint for v2 API
    
    Returns:
        Health status and service availability
    """
    try:
        # Test service initialization
        service = get_similarity_medicine_service()
        
        return {
            "status": "healthy",
            "version": "2.0.0",
            "services": {
                "similarity_engine": "operational",
                "sparql_endpoint": "operational"
            },
            "message": "V2 API is running"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@router.post(
    "/search/symptom",
    response_model=SearchResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Search drugs by symptoms (similarity-based)",
    description="Find drug recommendations based on symptoms using ontology-based similarity search"
)
async def search_by_symptom(request: SymptomSearchRequest):
    """
    Search for drug recommendations based on symptoms
    
    This endpoint uses a sophisticated ontology-based similarity algorithm:
    1. Analyzes input symptoms
    2. Finds related medical conditions using SPARQL queries
    3. Identifies drugs that treat those conditions
    4. Calculates similarity scores using BFS graph traversal
    5. Finds similar drugs based on shared conditions
    6. Returns ranked recommendations with explanations
    
    Args:
        request: SymptomSearchRequest with symptoms list and search parameters
        
    Returns:
        SearchResultResponse with ranked drug recommendations
        
    Raises:
        HTTPException: On validation or processing errors
        
    Example:
        POST /api/v2/search/symptom
        {
            "symptoms": ["fever", "headache", "muscle pain"],
            "top_k": 5,
            "min_similarity": 0.7
        }
    """
    start_time = time.time()
    
    try:
        logger.info(f"[V2 Symptom Search] Request: symptoms={request.symptoms}, "
                   f"top_k={request.top_k}, min_similarity={request.min_similarity}")
        
        # Get similarity medicine service
        service = get_similarity_medicine_service()
        
        # Execute symptom-based search
        result = service.search_by_symptom(
            symptoms=request.symptoms,
            top_k=request.top_k,
            min_similarity=request.min_similarity
        )
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Convert to API response format
        recommendations = [
            DrugRecommendationResponse(
                drug_id=drug.drug_id,
                drug_name=drug.drug_name,
                similarity_score=drug.similarity_score,
                explanation=drug.explanation,
                treats_conditions=drug.treats_conditions
            )
            for drug in result.drug_recommendations
        ]
        
        response = SearchResultResponse(
            success=True,
            query_type="symptom",
            query_input={
                "symptoms": request.symptoms,
                "top_k": request.top_k,
                "min_similarity": request.min_similarity
            },
            recommendations=recommendations,
            total_found=len(recommendations),
            message=f"Found {len(recommendations)} drug recommendation(s) based on symptoms",
            search_metadata={
                "execution_time_ms": execution_time_ms,
                "symptoms_analyzed": len(request.symptoms),
                "conditions_found": len(result.conditions_analyzed) if hasattr(result, 'conditions_analyzed') else 0
            }
        )
        
        logger.info(f"[V2 Symptom Search] Success: {len(recommendations)} drugs, "
                   f"{execution_time_ms}ms")
        
        return response
        
    except ValueError as e:
        logger.error(f"[V2 Symptom Search] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[V2 Symptom Search] Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing symptom search"
        )


@router.post(
    "/search/disease",
    response_model=SearchResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Search drugs by disease (similarity-based)",
    description="Find drug recommendations for a specific disease using ontology-based similarity"
)
async def search_by_disease(request: DiseaseSearchRequest):
    """
    Search for drug recommendations for a specific disease
    
    This endpoint:
    1. Searches for the disease in Wikidata ontology
    2. Finds drugs that treat the disease
    3. Calculates similarity scores based on shared conditions
    4. Finds similar drugs using graph traversal
    5. Returns ranked recommendations with explanations
    
    Args:
        request: DiseaseSearchRequest with disease name/ID and parameters
        
    Returns:
        SearchResultResponse with ranked drug recommendations
        
    Raises:
        HTTPException: On validation or processing errors
        
    Example:
        POST /api/v2/search/disease
        {
            "disease_name": "Type 2 Diabetes",
            "disease_id": "Q3025883",
            "top_k": 5,
            "min_similarity": 0.7
        }
    """
    start_time = time.time()
    
    try:
        logger.info(f"[V2 Disease Search] Request: disease='{request.disease_name}', "
                   f"id={request.disease_id}, top_k={request.top_k}, "
                   f"min_similarity={request.min_similarity}")
        
        # Get similarity medicine service
        service = get_similarity_medicine_service()
        
        # Execute disease-based search
        result = service.search_by_disease(
            disease_name=request.disease_name,
            disease_id=request.disease_id,
            top_k=request.top_k,
            min_similarity=request.min_similarity
        )
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Convert to API response format
        recommendations = [
            DrugRecommendationResponse(
                drug_id=drug.drug_id,
                drug_name=drug.drug_name,
                similarity_score=drug.similarity_score,
                explanation=drug.explanation,
                treats_conditions=drug.treats_conditions
            )
            for drug in result.drug_recommendations
        ]
        
        response = SearchResultResponse(
            success=True,
            query_type="disease",
            query_input={
                "disease_name": request.disease_name,
                "disease_id": request.disease_id,
                "top_k": request.top_k,
                "min_similarity": request.min_similarity
            },
            recommendations=recommendations,
            total_found=len(recommendations),
            message=f"Found {len(recommendations)} drug recommendation(s) for {request.disease_name}",
            search_metadata={
                "execution_time_ms": execution_time_ms,
                "disease_found": result.disease_id if hasattr(result, 'disease_id') else None
            }
        )
        
        logger.info(f"[V2 Disease Search] Success: {len(recommendations)} drugs, "
                   f"{execution_time_ms}ms")
        
        return response
        
    except ValueError as e:
        logger.error(f"[V2 Disease Search] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[V2 Disease Search] Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing disease search"
        )


@router.post(
    "/drugs/similar",
    response_model=SearchResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Find similar drugs",
    description="Find drugs similar to a reference drug based on shared medical conditions"
)
async def find_similar_drugs(request: SimilarDrugsRequest):
    """
    Find drugs similar to a reference drug
    
    This endpoint:
    1. Identifies the reference drug in Wikidata
    2. Finds conditions treated by the drug
    3. Searches for other drugs treating similar conditions
    4. Calculates similarity scores using ontology relationships
    5. Returns ranked similar drugs with explanations
    
    Args:
        request: SimilarDrugsRequest with drug name/ID and parameters
        
    Returns:
        SearchResultResponse with similar drug recommendations
        
    Raises:
        HTTPException: On validation or processing errors
        
    Example:
        POST /api/v2/drugs/similar
        {
            "drug_name": "Aspirin",
            "drug_id": "Q18216",
            "top_k": 5,
            "min_similarity": 0.7
        }
    """
    start_time = time.time()
    
    try:
        logger.info(f"[V2 Drug Similarity] Request: drug='{request.drug_name}', "
                   f"id={request.drug_id}, top_k={request.top_k}, "
                   f"min_similarity={request.min_similarity}")
        
        # Get similarity medicine service
        service = get_similarity_medicine_service()
        
        # Execute drug similarity search
        result = service.find_similar_drugs(
            drug_id=request.drug_id,
            drug_name=request.drug_name,
            top_k=request.top_k,
            min_similarity=request.min_similarity
        )
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Convert to API response format
        recommendations = [
            DrugRecommendationResponse(
                drug_id=drug.drug_id,
                drug_name=drug.drug_name,
                similarity_score=drug.similarity_score,
                explanation=drug.explanation,
                treats_conditions=drug.treats_conditions
            )
            for drug in result.drug_recommendations
        ]
        
        response = SearchResultResponse(
            success=True,
            query_type="drug_similarity",
            query_input={
                "drug_name": request.drug_name,
                "drug_id": request.drug_id,
                "top_k": request.top_k,
                "min_similarity": request.min_similarity
            },
            recommendations=recommendations,
            total_found=len(recommendations),
            message=f"Found {len(recommendations)} drug(s) similar to {request.drug_name}",
            search_metadata={
                "execution_time_ms": execution_time_ms,
                "reference_drug": request.drug_name,
                "shared_conditions": len(result.shared_conditions) if hasattr(result, 'shared_conditions') else 0
            }
        )
        
        logger.info(f"[V2 Drug Similarity] Success: {len(recommendations)} similar drugs, "
                   f"{execution_time_ms}ms")
        
        return response
        
    except ValueError as e:
        logger.error(f"[V2 Drug Similarity] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[V2 Drug Similarity] Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while finding similar drugs"
        )
