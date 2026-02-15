"""
Application Runner Script

Simple script to start the FastAPI application server.
"""

import uvicorn
from app.config import settings


def main():
    """
    Start the application server
    
    This function starts the Uvicorn server with configuration from settings.
    """
    print("=" * 60)
    print(f"  {settings.APP_NAME} v{settings.APP_VERSION}")
    print("=" * 60)
    print(f"  Starting server on http://{settings.HOST}:{settings.PORT}")
    print(f"  API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"  Environment: {'Development' if settings.is_development else 'Production'}")
    print("=" * 60)
    print()
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )


if __name__ == "__main__":
    main()