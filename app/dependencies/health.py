from fastapi import Depends
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.chroma_client import get_chroma_client
from app.db.session import get_db
from app.services.interfaces.health import IHealthService
from app.clients.interfaces.llm import ILLMClient
from app.clients.interfaces.iam import IIAMClient
from app.services.health.health_service import HealthService
from app.services.health.providers import (
    ChromaHealthProvider,
    DatabaseHealthProvider,
    LLMHealthProvider,
    IAMHealthProvider,
)
from app.dependencies.llm import get_llm_client
from app.dependencies.iam import get_iam_client


async def get_health_service(
    db: AsyncSession = Depends(get_db),
    llm_client: ILLMClient = Depends(get_llm_client),
    iam_client: IIAMClient = Depends(get_iam_client),
) -> IHealthService:
    """
    Dependency to get HealthService interface.
    Initializes all health check providers with their dependencies.
    """
    chroma_client = get_chroma_client()

    providers =[]

    # Always requeried providers
    providers.append(DatabaseHealthProvider(db))
    providers.append(LLMHealthProvider(llm_client))

    # Chroma, if RAG is enabled
    if settings.ENABLE_RAG:
        providers.append(ChromaHealthProvider(chroma_client))

    # IAM, if authentication is enabled
    if settings.AUTH_ENABLED:
        providers.append(IAMHealthProvider(iam_client))


    return HealthService(providers=providers)
