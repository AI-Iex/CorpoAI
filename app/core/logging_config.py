import json
import logging
import sys
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from app.core.config import settings
from app.core.enums import LogPrivacyLevel

# Masking constants
MASK_PLACEHOLDER = "****"
UUID_DISPLAY_LENGTH = 8
EMAIL_MIN_LENGTH = 1

# Context variables for request tracking
_request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_user_id_ctx: ContextVar[Optional[UUID]] = ContextVar("user_id", default=None)
_client_id_ctx: ContextVar[Optional[UUID]] = ContextVar("client_id", default=None)


# region Privacy Masking Methods


def _mask_value(value: str, level: str) -> str:
    """Mask sensitive values based on privacy level.
    
    Privacy levels:
        - none: No masking applied
        - standard: Mask emails only
        - strict: Mask emails and UUIDs
    """
    if level == LogPrivacyLevel.NONE:
        return value

    if not isinstance(value, str):
        return value

    # Always mask emails at standard or strict level
    if "@" in value:
        return _mask_email(value)

    # Mask UUIDs only at strict level
    if level == LogPrivacyLevel.STRICT and len(value) > 4:
        # Check if it looks like a UUID (hex chars and hyphens)
        if len(value) >= UUID_DISPLAY_LENGTH and all(
            c in "0123456789abcdef-" for c in value.lower()
        ):
            return _mask_uuid(value)

    return value


def _mask_email(email: str) -> str:
    """
    Mask email addresses for log safety.
    """
    try:
        local, domain = email.split("@", 1)
        
        # Mask local part
        if len(local) <= EMAIL_MIN_LENGTH:
            masked_local = "*"
        else:
            masked_local = local[0] + "*" * (len(local) - 1)
        
        # Mask domain part
        domain_parts = domain.split(".")
        if not domain_parts or not domain_parts[0]:
            return MASK_PLACEHOLDER
            
        masked_domain = domain_parts[0][0] + "*" * max(0, len(domain_parts[0]) - 1)
        if len(domain_parts) > 1:
            masked_domain = f"{masked_domain}.{'.'.join(domain_parts[1:])}"
            
        return f"{masked_local}@{masked_domain}"
    except (ValueError, IndexError, AttributeError):
        return MASK_PLACEHOLDER


def _mask_uuid(value: str) -> str:
    """
    Mask UUIDs and long identifiers for log safety.
    """
    try:
        if isinstance(value, str) and len(value) >= UUID_DISPLAY_LENGTH:
            return value[:UUID_DISPLAY_LENGTH] + "..."
        return value
    except Exception:
        return MASK_PLACEHOLDER


# endregion Privacy Masking Methods


# Blacklist of LogRecord attributes to exclude from extras
_RECORD_BLACKLIST = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "taskName",
}


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging with privacy masking.
    
    Produces JSON logs with the following structure:
    {
        "timestamp": "2025-11-27T14:50:42.693643Z",
        "level": "INFO",
        "logger": "service_name",
        "function": "function_name",
        "message": "log message",
        "extra": {"key": "value"}
    }
    """

    def __init__(self, privacy_level: Optional[str] = None) -> None:
        """
        Initialize JSON formatter.
        """
        super().__init__()
        self.privacy_level = privacy_level or settings.LOG_PRIVACY_LEVEL

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON string.
        """
        payload = self._build_base_payload(record)
        extras = self._extract_extras(record)
        
        if extras:
            payload["extra"] = extras

        # Apply privacy masking
        payload = self._mask_sensitive_data(payload, self.privacy_level)

        return json.dumps(payload, default=str)

    def _build_base_payload(self, record: logging.LogRecord) -> Dict[str, Any]:
        """
        Build base log payload with standard fields.
        
        Dictionary with timestamp, level, logger, function, message
        """
        log_dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        
        return {
            "timestamp": log_dt.isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "function": record.funcName,
            "message": record.getMessage(),
        }

    def _extract_extras(self, record: logging.LogRecord) -> Dict[str, Any]:
        """
        Extract extra fields from log record.
        """
        extras = {}
        for key, value in record.__dict__.items():
            if key in _RECORD_BLACKLIST or value is None:
                continue
                
            # Ensure value is JSON serializable
            try:
                json.dumps(value, default=str)
                extras[key] = value
            except (TypeError, ValueError):
                extras[key] = str(value)

        return extras

    def _mask_sensitive_data(self, obj: Any, level: str) -> Any:
        """
        Recursively mask sensitive data in nested structures.
        """
        if level == LogPrivacyLevel.NONE:
            return obj
            
        if isinstance(obj, dict):
            return {k: self._mask_sensitive_data(v, level) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._mask_sensitive_data(v, level) for v in obj]
        elif isinstance(obj, str):
            return _mask_value(obj, level)
            
        return obj


class RequestIdFilter(logging.Filter):
    """
    Logging filter that injects request context from ContextVars.
    
    Adds request_id, request_by_user_id, and request_by_client_id to all
    log records when available in the current context.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Inject context variables into log record.
        """
        self._add_request_id(record)
        self._add_user_id(record)
        self._add_client_id(record)
        return True

    def _add_request_id(self, record: logging.LogRecord) -> None:
        """
        Add request_id to record if available.
        """
        try:
            request_id = _request_id_ctx.get(None)
            record.request_id = request_id if request_id else None
        except LookupError:
            record.request_id = None

    def _add_user_id(self, record: logging.LogRecord) -> None:
        """
        Add user_id to record if available.
        """
        try:
            user_id = _user_id_ctx.get(None)
            record.request_by_user_id = str(user_id) if user_id else None
        except LookupError:
            record.request_by_user_id = None

    def _add_client_id(self, record: logging.LogRecord) -> None:
        """
        Add client_id to record if available.
        """
        try:
            client_id = _client_id_ctx.get(None)
            record.request_by_client_id = str(client_id) if client_id else None
        except LookupError:
            record.request_by_client_id = None


def setup_logging(
    service_name: str = settings.APP_NAME,
    level: int = logging.INFO,
    privacy_level: Optional[str] = None,
) -> logging.Logger:
    """
    Configure application logging with JSON formatting and context injection.
    """
    # Create and configure handler
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(JSONFormatter(privacy_level=privacy_level))
    handler.addFilter(RequestIdFilter())

    # Configure root logger
    root = logging.getLogger()
    root.handlers = []
    root.addHandler(handler)
    root.setLevel(level)

    return logging.getLogger(service_name)


# Third-party loggers to configure
_THIRD_PARTY_LOGGERS = (
    "uvicorn",
    "uvicorn.access",
    "uvicorn.error",
    "sqlalchemy.engine",
    "asyncio",
    "urllib3",
    "httpx",
    "httpcore",
    "chromadb",
)


def configure_third_party_loggers(
    level: int = logging.WARNING,
    attach_json_handler: bool = True,
) -> None:
    """
    Configure logging for third-party libraries.
    """
    handler = None
    if attach_json_handler:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(JSONFormatter())

    for logger_name in _THIRD_PARTY_LOGGERS:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.propagate = False
        
        if attach_json_handler and handler:
            logger.handlers = [handler]


# region ContextVar Management Methods (Request ID and User ID)


def get_request_id() -> Optional[str]:
    """
    Get current request ID from context.
    """
    return _request_id_ctx.get(None)


def get_user_id() -> Optional[UUID]:
    """
    Get current user ID from context.
    """
    return _user_id_ctx.get(None)


def get_client_id() -> Optional[UUID]:
    """
    Get current client ID from context.
    """
    return _client_id_ctx.get(None)


def get_request_context() -> Tuple[Optional[str], Optional[UUID], Optional[UUID]]:
    """
    Get all context variables.
    """
    return (
        _request_id_ctx.get(None),
        _user_id_ctx.get(None),
        _client_id_ctx.get(None),
    )


def set_request_context(
    request_id: str,
    user_id: Optional[UUID] = None,
    client_id: Optional[UUID] = None,
) -> Tuple[Token[Optional[str]], Optional[Token[Optional[UUID]]], Optional[Token[Optional[UUID]]]]:
    """
    Set request context variables.
    """
    request_token = _request_id_ctx.set(request_id)
    user_token = _user_id_ctx.set(user_id) if user_id is not None else None
    client_token = _client_id_ctx.set(client_id) if client_id is not None else None

    return request_token, user_token, client_token


def reset_request_context(
    request_token: Token[Optional[str]],
    user_token: Optional[Token[Optional[UUID]]] = None,
    client_token: Optional[Token[Optional[UUID]]] = None,
) -> None:
    """
    Reset request context to previous values.
    """
    _request_id_ctx.reset(request_token)
    
    if user_token is not None:
        _user_id_ctx.reset(user_token)
    if client_token is not None:
        _client_id_ctx.reset(client_token)


# endregion ContextVar Management Methods (Request ID and User ID)
