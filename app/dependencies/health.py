from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.chroma_client import get_chroma_client
from app.db.session import get_db
from app.services.interfaces.health import IHealthService
from app.services.health.health_service import HealthService
from app.services.health.providers import (
    ChromaHealthProvider,
    DatabaseHealthProvider,
    LLMHealthProvider,
    IAMHealthProvider,
)
from app.clients.llm_client_manager import get_llm_client
from app.clients.iam_client_manager import get_iam_client


async def get_health_service(
    db: AsyncSession = Depends(get_db),
) -> IHealthService:
    """
    Get HealthService interface.
    Initializes health check providers based on enabled features.
    """
    providers = []

    # Always required: Database and LLM
    providers.append(DatabaseHealthProvider(db))
    providers.append(LLMHealthProvider(get_llm_client()))

    # ChromaDB - only if RAG is enabled
    if settings.ENABLE_RAG:
        chroma_client = get_chroma_client()
        providers.append(ChromaHealthProvider(chroma_client))

    # IAM - only if authentication is enabled
    if settings.AUTH_ENABLED:
        providers.append(IAMHealthProvider(get_iam_client()))

    return HealthService(providers=providers)
