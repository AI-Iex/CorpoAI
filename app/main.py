import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.logging_config import setup_logging, configure_third_party_loggers
from app.db.chroma_client import close_chroma, init_chroma
from app.db.session import close_db, init_db
from app.middleware.exception_handler import exception_handler_middleware
from app.middleware.logging import logging_middleware

# Setup logging
logger = setup_logging()
configure_third_party_loggers(level=logging.WARNING, attach_json_handler=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    """
    # Startup
    logger.info("Application startup", extra={"environment": settings.ENVIRONMENT, "debug": settings.DEBUG})

    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", extra={"error": str(e)}, exc_info=True)
        raise

    # Initialize ChromaDB (optional, only if RAG enabled)
    if settings.ENABLE_RAG:
        try:
            await init_chroma()
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.warning("ChromaDB initialization failed (non-critical)", extra={"error": str(e)})

    yield

    # Shutdown
    logger.info("Application shutdown")

    if settings.ENABLE_RAG:
        await close_chroma()

    await close_db()
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI Assistant Service with LangChain, LangGraph, and RAG capabilities",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Custom middleware
@app.middleware("http")
async def logging_middleware_wrapper(request, call_next):
    """Wrapper for logging middleware."""
    return await logging_middleware(request, call_next)


@app.middleware("http")
async def exception_handler_middleware_wrapper(request, call_next):
    """Wrapper for exception handler middleware."""
    return await exception_handler_middleware(request, call_next)


# Include routers
app.include_router(health_router, tags=["Health"])


# Root endpoint - redirect to documentation
@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API documentation"""

    return RedirectResponse(url="/docs")


# API info endpoint
@app.get("/info", tags=["Info"])
async def info():
    """Get API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
