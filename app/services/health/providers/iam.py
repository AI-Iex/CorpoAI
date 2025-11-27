import logging
import time
from app.core.enums import HealthStatus
from app.clients.interfaces.iam import IIAMClient
from app.services.health.providers.base import IHealthCheckProvider
from app.schemas.health import HealthProviderResponse

logger = logging.getLogger(__name__)


class IAMHealthProvider(IHealthCheckProvider):
    """
    IAM service health check provider.
    """

    def __init__(self, iam_client: IIAMClient):
        """
        Initialize IAM health check provider.
        """
        self._iam_client = iam_client

    @property
    def name(self) -> str:
        """Returns service name."""
        return "iam_service"

    async def check_health(self) -> HealthProviderResponse:
        """
        Check IAM service health delegating to the client.
        """
        start_time = time.time()

        try:
            is_healthy = await self._iam_client.check_health()
            response_time = (time.time() - start_time) * 1000

            status = HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY

            if not is_healthy:
                logger.warning("IAM service health check failed")

            return HealthProviderResponse(status=status, response_time_ms=round(response_time, 2))

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"IAM health check failed: {type(e).__name__}")
            logger.debug(f"Err msg: {e}", exc_info=True)

            return HealthProviderResponse(status=HealthStatus.UNHEALTHY, response_time_ms=round(response_time, 2))
