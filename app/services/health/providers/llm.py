import logging
import time
from app.core.enums import HealthStatus
from app.clients.interfaces.llm import ILLMClient
from app.services.health.providers.base import IHealthCheckProvider
from app.schemas.health import HealthProviderResponse

logger = logging.getLogger(__name__)


class LLMHealthProvider(IHealthCheckProvider):
    """
    LLM service health check provider.
    """

    def __init__(self, llm_client: ILLMClient):
        """
        Initialize LLM health check provider.
        """
        self._llm_client = llm_client

    @property
    def name(self) -> str:
        """Returns dynamic name based on model."""
        return f"llm_{self._llm_client.model_name}"

    async def check_health(self) -> HealthProviderResponse:
        """
        Check LLM service health by delegating to the client.
        """
        start_time = time.time()
        
        try:
            is_healthy = await self._llm_client.check_health()
            response_time = (time.time() - start_time) * 1000
            
            status = HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY
            
            if not is_healthy:
                logger.warning(f"LLM model '{self._llm_client.model_name}' health check failed")
            
            return HealthProviderResponse(
                status=status,
                response_time_ms=round(response_time, 2)
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"LLM health check failed: {type(e).__name__}")
            logger.debug(f"Err msg: {e}", exc_info=True)
            
            return HealthProviderResponse(
                status=HealthStatus.UNHEALTHY,
                response_time_ms=round(response_time, 2)
            )
