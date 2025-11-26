from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.chroma_client import get_chroma_client
from app.db.session import get_db
from app.services.interfaces.health import IHealthService
from app.services.health.health_service import HealthService
from app.services.health.providers import (
    ChromaHealthProvider,
    DatabaseHealthProvider,
    OllamaHealthProvider,
)


async def get_health_service(
    db: AsyncSession = Depends(get_db),
) -> IHealthService:
    """
    Dependency to get HealthService interface.
    """
   
    chroma_client = get_chroma_client()
    
    providers = [
        DatabaseHealthProvider(db),
        ChromaHealthProvider(chroma_client),
        OllamaHealthProvider(),
    ]
    
    return HealthService(providers=providers)
