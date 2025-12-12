import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.api.routes.health import router as health_router
from app.api.routes.chat import router as chat_router
from app.api.routes.info import router as info_router
from app.core.config import settings
from app.core.logging_config import setup_logging, configure_third_party_loggers
from app.db.chroma_client import close_chroma, init_chroma
from app.db.session import close_db, init_db
from app.clients.llm_client_manager import (
    init_llm_client,
    close_llm_client,
    init_context_manager,
)
from app.clients.iam_client_manager import init_iam_client, close_iam_client
from app.middleware.exception_handler import exception_handler_middleware
from app.middleware.logging import logging_middleware

# Setup logging
logger = setup_logging()
configure_third_party_loggers(level=logging.WARNING, attach_json_handler=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes all required clients and services during startup.
    """
    # Startup
    logger.info(
        "Application startup",
        extra={
            "environment": settings.ENVIRONMENT,
            "log_level": settings.LOG_LEVEL,
            "rag_enabled": settings.ENABLE_RAG,
            "auth_enabled": settings.AUTH_ENABLED,
        },
    )

    # Initialize Database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", extra={"error": str(e)}, exc_info=True)
        raise

    # Initialize LLM Client (always required)
    try:
        init_llm_client()
        logger.info("LLM client initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize LLM client", extra={"error": str(e)}, exc_info=True)
        raise

    # Initialize Context Manager (requires LLM client)
    try:
        init_context_manager()
        logger.info("Context manager initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize context manager", extra={"error": str(e)}, exc_info=True)
        raise

    # Initialize ChromaDB (optional, only if RAG enabled)
    if settings.ENABLE_RAG:
        try:
            await init_chroma()
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.warning("ChromaDB initialization failed (non-critical)", extra={"error": str(e)})

    # Initialize IAM Client (optional, only if AUTH enabled)
    if settings.AUTH_ENABLED:
        try:
            init_iam_client()
            logger.info("IAM client initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize IAM client", extra={"error": str(e)}, exc_info=True)
            raise

    yield

    # Shutdown
    logger.info("Application shutdown")

    # Cleanup in reverse order
    if settings.AUTH_ENABLED:
        close_iam_client()

    if settings.ENABLE_RAG:
        await close_chroma()

    close_llm_client()
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
app.include_router(info_router)
app.include_router(health_router)
app.include_router(chat_router)


# Root endpoint - redirect to documentation
@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API documentation"""

    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
