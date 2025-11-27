import logging
from datetime import datetime
from typing import List
from app.core.enums import HealthStatus
from app.schemas.health import DependencyHealth, HealthCheckResponse
from app.services.health.providers.base import IHealthCheckProvider
from app.services.interfaces.health import IHealthService

logger = logging.getLogger(__name__)


class HealthService(IHealthService):
    """
    Health check orchestration service.
    """

    def __init__(self, providers: List[IHealthCheckProvider]):
        """
        Initialize health service.
        """
        self._providers = providers

    async def check_all(self) -> HealthCheckResponse:
        """
        Execute all health checks and aggregate results.
        """
        checks: List[DependencyHealth] = []

        # Execute all providers
        logger.info("Starting health checks", extra={"provider_count": len(self._providers)})

        for provider in self._providers:
            try:
                provider_response = await provider.check_health()

                logger.debug(
                    f"Health check completed for {provider.name}",
                    extra={
                        "provider": provider.name,
                        "status": provider_response.status.value,
                        "response_time_ms": provider_response.response_time_ms,
                    },
                )

                checks.append(
                    DependencyHealth(
                        name=provider.name,
                        status=provider_response.status,
                        response_time_ms=provider_response.response_time_ms,
                    )
                )

            except Exception as e:
                logger.error(
                    f"Health check provider {provider.name} failed",
                    extra={
                        "provider": provider.name,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )
                checks.append(
                    DependencyHealth(
                        name=provider.name,
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=0.0,
                    )
                )

        # Determine overall status
        overall_status = self._calculate_overall_status(checks)

        logger.info(
            "Health checks completed",
            extra={
                "overall_status": overall_status.value,
                "total_checks": len(checks),
                "healthy_count": sum(1 for c in checks if c.status == HealthStatus.HEALTHY),
                "unhealthy_count": sum(1 for c in checks if c.status == HealthStatus.UNHEALTHY),
            },
        )

        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            checks=checks,
        )

    def _calculate_overall_status(self, checks: List[DependencyHealth]) -> HealthStatus:
        """
        Calculate overall health status from individual checks.

        Logic:
        - If any service is UNHEALTHY → UNHEALTHY
        - If all are HEALTHY or DISABLED → HEALTHY
        """
        if not checks:
            return HealthStatus.UNHEALTHY

        for check in checks:
            if check.status == HealthStatus.UNHEALTHY:
                logger.warning(
                    f"Service {check.name} is unhealthy",
                    extra={
                        "service": check.name,
                        "status": check.status.value,
                    },
                )
                return HealthStatus.UNHEALTHY

        return HealthStatus.HEALTHY
