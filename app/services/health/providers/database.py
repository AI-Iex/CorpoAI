import logging
import time
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.enums import HealthStatus
from app.services.health.providers.base import IHealthCheckProvider
from app.schemas.health import HealthProviderResponse

logger = logging.getLogger(__name__)


class DatabaseHealthProvider(IHealthCheckProvider):
    """
    PostgreSQL database health check provider.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize database health provider.
        """
        self._session = session

    @property
    def name(self) -> str:
        return "postgres_db"

    async def check_health(self) -> HealthProviderResponse:
        """
        Check PostgreSQL database health.
        """
        start_time = time.time()
        
        try:
            # Simple query to check database connectivity
            result = await self._session.execute(text("SELECT 1"))
            result.scalar_one()
            
            response_time = (time.time() - start_time) * 1000
            logger.debug(f"Database health check passed in {response_time:.2f}ms")
            
            return HealthProviderResponse(
                status=HealthStatus.HEALTHY,
                response_time_ms=round(response_time, 2)
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {type(e).__name__}")
            
            return HealthProviderResponse(
                status=HealthStatus.UNHEALTHY,
                response_time_ms=round(response_time, 2)
            )