import logging
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from app.core.exceptions import BaseAppException
from app.core.logging_config import get_request_id

logger = logging.getLogger(__name__)


def _get_safe_request_id(request: Request) -> str:
    """
    Get request ID from context or request state.
    """
    return get_request_id() or getattr(request.state, "request_id", "unknown")


def _build_error_response(
    request: Request,
    request_id: str,
    error_name: str,
    message: str,
) -> dict:
    """
    Build standardized error response.
    """
    return {
        "request_id": request_id,
        "error": error_name,
        "message": message,
        "path": str(request.url.path),
    }


async def exception_handler_middleware(request: Request, call_next: Callable) -> Response:
    """
    Handle all exceptions with structured responses.
    """
    try:
        return await call_next(request)

    except BaseAppException as exc:
        request_id = _get_safe_request_id(request)
        
        logger.warning(
            f"Application exception: {exc.message}",
            extra={
                "error_type": exc.__class__.__name__,
                "status_code": exc.status_code,
                "path": str(request.url.path),
                "method": request.method,
            },
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_response(
                request, request_id, exc.__class__.__name__, exc.message
            ),
        )

    except SQLAlchemyError as exc:
        request_id = _get_safe_request_id(request)
        
        logger.error(
            f"Database error: {str(exc)}",
            extra={
                "error_type": "SQLAlchemyError",
                "path": str(request.url.path),
                "method": request.method,
            },
            exc_info=True,
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_build_error_response(
                request, request_id, "DatabaseError", "A database error occurred"
            ),
        )

    except Exception as exc:
        request_id = _get_safe_request_id(request)
        
        logger.error(
            f"Unhandled exception: {str(exc)}",
            extra={
                "error_type": type(exc).__name__,
                "path": str(request.url.path),
                "method": request.method,
            },
            exc_info=True,
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_build_error_response(
                request, request_id, "InternalServerError", "An unexpected error occurred"
            ),
        )
