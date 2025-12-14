import logging
import time
from app.core.enums import HealthStatus
from app.clients.interfaces.embedding import IEmbeddingClient
from app.services.health.providers.base import IHealthCheckProvider
from app.schemas.health import HealthProviderResponse

logger = logging.getLogger(__name__)


class EmbeddingHealthProvider(IHealthCheckProvider):
    """
    Embedding service health check provider.
    """

    def __init__(self, embedding_client: IEmbeddingClient):
        """
        Initialize Embedding health check provider.
        """
        self._embedding_client = embedding_client

    @property
    def name(self) -> str:
        """Returns dynamic name based on model."""
        return f"embedding_{self._embedding_client.model_name}"

    async def check_health(self) -> HealthProviderResponse:
        """
        Check embedding service health.
        """
        start_time = time.time()

        try:

            test_embedding = await self._embedding_client.check_health()
            response_time = (time.time() - start_time) * 1000

            return HealthProviderResponse(
                status=HealthStatus.HEALTHY if test_embedding else HealthStatus.UNHEALTHY,
                response_time_ms=round(response_time, 2),
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Embedding health check failed: {type(e).__name__}")
            logger.debug(f"Err msg: {e}", exc_info=True)

            return HealthProviderResponse(
                status=HealthStatus.UNHEALTHY,
                response_time_ms=round(response_time, 2),
            )
