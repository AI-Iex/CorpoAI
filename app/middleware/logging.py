import logging
import time
from typing import Callable

from fastapi import Request, Response

logger = logging.getLogger(__name__)


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to log all HTTP requests and responses.
    """
    # Generate unique request ID
    request_id = request.headers.get("X-Request-ID", f"{int(time.time() * 1000)}")

    # Log request
    logger.info(
        "Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
        },
    )

    # Process request
    start_time = time.time()

    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000

        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        # Log response
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time_ms": f"{process_time:.2f}",
            },
        )

        return response

    except Exception as e:
        process_time = (time.time() - start_time) * 1000

        logger.error(
            "Request failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "process_time_ms": f"{process_time:.2f}",
                "error": str(e),
            },
            exc_info=True,
        )
        raise
