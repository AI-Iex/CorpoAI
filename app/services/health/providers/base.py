import logging
from abc import ABC, abstractmethod
from app.schemas.health import HealthProviderResponse
from app.core.enums import HealthStatus

logger = logging.getLogger(__name__)


class IHealthCheckProvider(ABC):
    """
    Interface for health check providers.

    Each provider checks the health of a specific service/component.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the service being checked.
        """
        pass

    @abstractmethod
    async def check_health(self) -> HealthProviderResponse:
        """
        Check the health of the service.
        """
        pass
