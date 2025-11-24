class BaseAppException(Exception):
    """Base exception for all application exceptions."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(BaseAppException):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class UnauthorizedError(BaseAppException):
    """Exception raised when authentication fails."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ForbiddenError(BaseAppException):
    """Exception raised when user lacks permissions."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)


class ValidationError(BaseAppException):
    """Exception raised when validation fails."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)


class ConflictError(BaseAppException):
    """Exception raised when there's a conflict (e.g., duplicate)."""

    def __init__(self, message: str = "Conflict"):
        super().__init__(message, status_code=409)


class ServiceUnavailableError(BaseAppException):
    """Exception raised when a service is unavailable."""

    def __init__(self, message: str = "Service unavailable"):
        super().__init__(message, status_code=503)


class DatabaseError(BaseAppException):
    """Exception raised when database operation fails."""

    def __init__(self, message: str = "Database error"):
        super().__init__(message, status_code=500)


class LLMError(BaseAppException):
    """Exception raised when LLM operation fails."""

    def __init__(self, message: str = "LLM processing error"):
        super().__init__(message, status_code=500)


class VectorStoreError(BaseAppException):
    """Exception raised when vector store operation fails."""

    def __init__(self, message: str = "Vector store error"):
        super().__init__(message, status_code=500)
