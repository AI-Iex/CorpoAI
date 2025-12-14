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


class RepositoryError(BaseAppException):
    """Exception raised when repository operation fails."""

    def __init__(self, message: str = "Repository error"):
        super().__init__(message, status_code=500)


class LLMError(BaseAppException):
    """Exception raised when LLM operation fails."""

    def __init__(self, message: str = "LLM processing error", status_code: int = 500):
        super().__init__(message, status_code=status_code)


class VectorStoreError(BaseAppException):
    """Exception raised when vector store operation fails."""

    def __init__(self, message: str = "Vector store error"):
        super().__init__(message, status_code=500)


class DocumentError(BaseAppException):
    """Base exception for document-related errors."""

    def __init__(self, message: str = "Document error", status_code: int = 500):
        super().__init__(message, status_code=status_code)


class DocumentNotFoundError(DocumentError):
    """Exception raised when a document is not found."""

    def __init__(self, document_id: str = None):
        message = f"Document not found: {document_id}" if document_id else "Document not found"
        super().__init__(message, status_code=404)


class DocumentUploadError(DocumentError):
    """Exception raised when document upload fails."""

    def __init__(self, message: str = "Failed to upload document"):
        super().__init__(message, status_code=400)


class DocumentProcessingError(DocumentError):
    """Exception raised when document processing fails."""

    def __init__(self, message: str = "Failed to process document"):
        super().__init__(message, status_code=422)


class UnsupportedFileTypeError(DocumentError):
    """Exception raised when file type is not supported."""

    def __init__(self, file_type: str = None):
        message = f"Unsupported file type: {file_type}" if file_type else "Unsupported file type"
        super().__init__(message, status_code=415)


class FileTooLargeError(DocumentError):
    """Exception raised when file exceeds size limit."""

    def __init__(self, max_size_mb: int = None):
        message = f"File exceeds maximum size of {max_size_mb}MB" if max_size_mb else "File too large"
        super().__init__(message, status_code=413)


class DocumentExtractionError(DocumentError):
    """Exception raised when text extraction from document fails."""

    def __init__(self, message: str = "Failed to extract text from document"):
        super().__init__(message, status_code=422)


class ChunkingError(DocumentError):
    """Exception raised when document chunking fails."""

    def __init__(self, message: str = "Failed to chunk document"):
        super().__init__(message, status_code=500)


class EmbeddingError(DocumentError):
    """Exception raised when embedding generation fails."""

    def __init__(self, message: str = "Failed to generate embeddings"):
        super().__init__(message, status_code=500)


class NotImplementedError(BaseAppException):
    """Exception raised when a feature is not implemented."""

    def __init__(self, message: str = "Not implemented error"):
        super().__init__(message, status_code=501)
