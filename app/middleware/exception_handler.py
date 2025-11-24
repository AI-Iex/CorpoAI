import logging
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import BaseAppException

logger = logging.getLogger(__name__)


async def exception_handler_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to handle all exceptions and return consistent error responses.
    """
    try:
        return await call_next(request)

    except BaseAppException as e:
        logger.warning(
            f"Application exception: {e.message}",
            extra={
                "status_code": e.status_code,
                "path": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": e.__class__.__name__,
                "message": e.message,
                "path": request.url.path,
            },
        )

    except SQLAlchemyError as e:
        logger.error(
            f"Database error: {str(e)}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "DatabaseError",
                "message": "A database error occurred",
                "path": request.url.path,
            },
        )

    except Exception as e:
        logger.error(
            f"Unhandled exception: {str(e)}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "path": request.url.path,
            },
        )
