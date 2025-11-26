from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.chroma_client import get_chroma_client
from app.db.session import get_db
from app.services.interfaces.health import IHealthService
from app.services.interfaces.llm import ILLMProvider
from app.services.health.health_service import HealthService
from app.services.health.providers import (
    ChromaHealthProvider,
    DatabaseHealthProvider,
    LLMHealthProvider,
)
from app.dependencies.llm import get_llm_provider


async def get_health_service(
    db: AsyncSession = Depends(get_db),
    llm_provider: ILLMProvider = Depends(get_llm_provider),
) -> IHealthService:
    """
    Dependency to get HealthService interface.
    Initializes all health check providers with their dependencies.
    """
    chroma_client = get_chroma_client()
    
    providers = [
        DatabaseHealthProvider(db),
        ChromaHealthProvider(chroma_client),
        LLMHealthProvider(llm_provider),
    ]
    
    return HealthService(providers=providers)
