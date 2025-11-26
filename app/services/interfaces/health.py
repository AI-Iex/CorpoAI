from abc import ABC, abstractmethod
from app.schemas.health import HealthCheckResponse


class IHealthService(ABC):
    """Interface for health check service."""

    @abstractmethod
    async def check_all(self) -> HealthCheckResponse:
        """
        Execute all health checks and return aggregated results.
        """
        ...
