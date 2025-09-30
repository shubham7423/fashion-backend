from fastapi import FastAPI
from app.api.routes import router
from app.core.config import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
    )

    # Include API routes
    app.include_router(router, prefix="/api/v1")

    @app.get("/")
    async def root():
        """Root endpoint with API information"""
        return {
            "message": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "endpoints": {
                "/api/v1/attribute_clothes": "POST - Process image files for clothing attribute analysis",
                "/api/v1/health": "GET - Health check",
            },
        }

    return app


app = create_app()
