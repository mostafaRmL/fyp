"""
FastAPI Application Entry Point

This module initializes and configures the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.config import settings
from app.api.routes import router
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered medical assistant using knowledge graphs and LLM for medicine recommendations",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API router
app.include_router(router)


# Mount static files
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    logger.info(f"Static files mounted from: {static_path}")
else:
    logger.warning(f"Static directory not found: {static_path}")


@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler
    
    Performs initialization tasks when the application starts.
    """
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 60)
    logger.info(f"Environment: {'Development' if settings.is_development else 'Production'}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info(f"Log Level: {settings.LOG_LEVEL}")
    logger.info(f"Groq Model: {settings.GROQ_MODEL}")
    logger.info(f"SPARQL Endpoint: {settings.WIKIDATA_ENDPOINT}")
    logger.info("=" * 60)
    
    # Test service initialization
    try:
        from app.services.llm_service import get_llm_service
        from app.services.sparql_service import get_sparql_service
        
        llm_service = get_llm_service()
        logger.info("✓ LLM Service initialized successfully")
        
        sparql_service = get_sparql_service()
        logger.info("✓ SPARQL Service initialized successfully")
        
    except Exception as e:
        logger.error(f"✗ Service initialization failed: {str(e)}")
        logger.warning("Application may not function correctly")
    
    logger.info("Application startup complete")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler
    
    Performs cleanup tasks when the application shuts down.
    """
    logger.info("=" * 60)
    logger.info("Shutting down application...")
    logger.info("=" * 60)


@app.get("/")
async def root():
    """
    Root endpoint - Serves the main frontend page
    
    Returns:
        HTML file for the web interface
    """
    index_path = static_path / "index.html"
    
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        return {
            "message": "Medical Assistant API",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "api": "/api"
        }


@app.get("/favicon.ico")
async def favicon():
    """
    Favicon endpoint
    
    Returns:
        Favicon file or 404
    """
    favicon_path = static_path / "favicon.ico"
    
    if favicon_path.exists():
        return FileResponse(str(favicon_path))
    
    # Return 204 No Content if favicon doesn't exist
    from fastapi import Response
    return Response(status_code=204)


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return {
        "error": "not_found",
        "message": "The requested resource was not found",
        "path": str(request.url)
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(exc)}")
    return {
        "error": "internal_error",
        "message": "An internal server error occurred"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )