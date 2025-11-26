"""Main FastAPI application for quiz game."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.services.s3_service import S3Service
from app.services.cache_service import CacheService
from app.api.routes import health, game

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize cache, download cards from S3, download images
    - Shutdown: Cleanup resources
    """
    settings = get_settings()
    logger.info("Starting application initialization...")

    try:
        # Initialize cache service
        cache_service = CacheService(settings.cache_dir)
        cache_service.initialize_cache()

        # Initialize S3 service
        s3_service = S3Service(
            bucket_name=settings.s3_bucket_name,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            aws_region=settings.aws_region,
        )

        # Download and parse cards metadata
        logger.info("Fetching cards metadata from S3...")
        cards = s3_service.fetch_cards_metadata(settings.s3_cards_json_key)
        logger.info(f"Loaded {len(cards)} cards from S3")

        # Download all images to cache
        logger.info("Downloading card images to cache...")
        cache_dir = cache_service.get_cache_dir()
        s3_service.download_all_images(cards, cache_dir)
        logger.info("All images cached successfully")

        # Store cards in app state
        app.state.cards = cards
        logger.info("Application initialization complete")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Application shutdown")


# Create FastAPI application
app = FastAPI(
    title="Quiz Game API",
    description="A quiz game where players match card images with correct answers",
    version="1.0.0",
    lifespan=lifespan,
)

# Add session middleware for cookie-based session management
settings = get_settings()
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key,
    session_cookie="quiz_session",
    max_age=3600,  # 1 hour
    same_site="lax",
    https_only=False,  # Set to True in production with HTTPS
)

# Include routers
app.include_router(health.router)
app.include_router(game.router)

# Mount static files
# Serve frontend assets (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Serve cached images
app.mount("/images", StaticFiles(directory=settings.cache_dir), name="images")


@app.get("/", tags=["root"])
def read_root() -> Dict[str, str]:
    """Root endpoint - redirects to API docs."""
    return {
        "message": "Quiz Game API",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
