import logging
import time
from chromadb import Client
from app.core.config import settings
from app.core.enums import HealthStatus, ChromaMode
from app.schemas.health import HealthProviderResponse
from app.services.health.providers.base import IHealthCheckProvider

logger = logging.getLogger(__name__)


class ChromaHealthProvider(IHealthCheckProvider):
    """
    ChromaDB health check provider.
    """

    def __init__(self, client: Client):
        """
        Initialize ChromaDB health provider.
        """
        self._client = client

    @property
    def name(self) -> str:
        return "chroma_db"

    async def check_health(self) -> HealthProviderResponse:
        """
        Check ChromaDB health using the client's heartbeat method.
        """
        start_time = time.time()
        
        try:
            # Check if ChromaDB is enabled
            if not settings.ENABLE_RAG:
                logger.debug("ChromaDB check skipped (RAG disabled)")
                return HealthProviderResponse(
                    status=HealthStatus.DISABLED,
                    response_time_ms=0.0
                )
            
            heartbeat = self._client.heartbeat()
            
            response_time = (time.time() - start_time) * 1000
            
            if heartbeat and heartbeat > 0:
                logger.debug(f"ChromaDB health check passed in {response_time:.2f}ms")
                return HealthProviderResponse(
                    status=HealthStatus.HEALTHY,
                    response_time_ms=round(response_time, 2)
                )
            else:
                logger.warning("ChromaDB heartbeat returned invalid response")
                return HealthProviderResponse(
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=round(response_time, 2)
                )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"ChromaDB health check failed: {type(e).__name__}")
            logger.debug(f"Err msg: {e}", exc_info=True)
            
            return HealthProviderResponse(
                status=HealthStatus.UNHEALTHY,
                response_time_ms=round(response_time, 2)
            )