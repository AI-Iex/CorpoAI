import logging
import time
import uuid
from typing import Any, Dict, Optional
from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from app.core.logging_config import reset_request_context, set_request_context

logger = logging.getLogger("access")

# HTTP status codes
HTTP_INTERNAL_SERVER_ERROR = 500

# Error message max length
ERROR_MESSAGE_MAX_LENGTH = 200


def _get_request_id(request: Request) -> str:
    """
    Get or generate request ID.
    """
    return getattr(request.state, "request_id", None) or str(uuid.uuid4())


def _extract_status_code(exc: Exception) -> int:
    """
    Extract HTTP status code from exception.
    """
    if isinstance(exc, HTTPException):
        return exc.status_code
    return getattr(exc, "status_code", HTTP_INTERNAL_SERVER_ERROR)


def _get_route_name(request: Request) -> Optional[str]:
    """
    Extract route name from request scope.
    """
    route = request.scope.get("route")
    return getattr(route, "name", None) if route else None


def _build_log_extra(
    request: Request,
    request_id: str,
    duration_ms: float,
    status_code: int,
) -> Dict[str, Any]:
    """
    Build structured log extra data.
    """
    log_extra = {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "route": _get_route_name(request),
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "client_ip": request.client.host if request.client else None,
    }

    # Add user context if available
    user_id = getattr(request.state, "user_id", None)
    client_id = getattr(request.state, "client_id", None)

    if user_id is not None:
        log_extra["request_by_user_id"] = user_id
    if client_id is not None:
        log_extra["request_by_client_id"] = client_id

    return log_extra


async def logging_middleware(request: Request, call_next):
    """
    Structured access log middleware.

    Responsibilities:
    - Generate or retrieve request ID
    - Set request context for log propagation
    - Measure request duration
    - Log structured request/response data
    - Add correlation headers
    - Clean up context after request
    """
    start_time = time.perf_counter()

    # Setup request tracking
    request_id = _get_request_id(request)
    request.state.request_id = request_id

    # Set context for log propagation
    request_token, user_token, client_token = set_request_context(request_id)

    try:
        response: Response = await call_next(request)
        
    except Exception as exc:
        # Log error summary without full traceback in access log
        duration_ms = (time.perf_counter() - start_time) * 1000
        status_code = _extract_status_code(exc)

        logger.error(
            "HTTP request error",
            extra={
                **_build_log_extra(request, request_id, duration_ms, status_code),
                "error_type": type(exc).__name__,
                "error_message": str(exc)[:ERROR_MESSAGE_MAX_LENGTH],
            },
        )
        
        # Cleanup and re-raise for exception handler
        try:
            reset_request_context(request_token, user_token, client_token)
        except Exception:
            pass
        raise

    # Log successful request
    duration_ms = (time.perf_counter() - start_time) * 1000
    log_extra = _build_log_extra(request, request_id, duration_ms, response.status_code)

    logger.info("HTTP request completed", extra=log_extra)

    # Add correlation header
    if isinstance(response, Response):
        response.headers.setdefault("X-Request-Id", request_id)

    # Cleanup context
    try:
        reset_request_context(request_token, user_token, client_token)
    except Exception:
        pass

    return response
