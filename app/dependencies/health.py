from fastapi import Depends
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

    providers = [
        DatabaseHealthProvider(db),
        ChromaHealthProvider(chroma_client),
        LLMHealthProvider(llm_client),
        IAMHealthProvider(iam_client),
    ]

    return HealthService(providers=providers)
