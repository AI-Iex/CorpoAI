from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
from app.core.enums import HealthStatus


class DependencyHealth(BaseModel):
    name: str = Field(..., description="Name of the dependency", json_schema_extra={"example": "postgres_db"})
    status: HealthStatus = Field(
        ..., description="Health status of the dependency", json_schema_extra={"example": "healthy"}
    )
    response_time_ms: float = Field(
        ..., description="Response time in milliseconds", json_schema_extra={"example": 12.5}
    )


class HealthProviderResponse(BaseModel):
    status: HealthStatus = Field(
        ..., description="Health status reported by the provider", json_schema_extra={"example": "healthy"}
    )
    response_time_ms: float = Field(
        ..., description="Response time in milliseconds", json_schema_extra={"example": 25.3}
    )


class HealthCheckResponse(BaseModel):
    status: HealthStatus = Field(..., description="Overall health status", json_schema_extra={"example": "healthy"})
    timestamp: datetime = Field(
        ..., description="Timestamp of the health check", json_schema_extra={"example": "2025-10-31T18:55:54Z"}
    )
    checks: List[DependencyHealth] = Field(
        ...,
        description="Health status of individual dependencies",
        json_schema_extra={
            "example": [
                {"name": "postgres_db", "status": "healthy", "response_time_ms": 12.5},
                {"name": "reddis_cache", "status": "healthy", "response_time_ms": 2.1},
            ]
        },
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-31T18:55:54Z",
                "checks": {
                    "postgres_db": {"status": "healthy", "response_time": 12.5},
                    "reddis_cache": {"status": "healthy", "response_time": 2.1},
                },
            }
        }
    }
