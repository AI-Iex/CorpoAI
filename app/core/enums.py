from enum import Enum

# region MESSAGE ROLES ENUM


class MessageRoleTypes(str, Enum):
    """Message role types"""

    USER = "user"
    "User"

    ASSISTANT = "assistant"
    "AI assistant"

    SYSTEM = "system"
    "System message"


# endregion MESSAGE ROLES ENUM

# region HEALTH STATUS ENUM


class HealthStatus(str, Enum):
    """Health status types"""

    HEALTHY = "healthy"
    "Healthy status"

    UNHEALTHY = "unhealthy"
    "Unhealthy status"

    DISABLED = "disabled"
    "Disabled/not configured"


# endregion HEALTH STATUS ENUM

# region CHROMA MODE ENUM


class ChromaMode(str, Enum):
    """Chroma mode types"""

    LOCAL = "local"
    "Local mode"

    SERVER = "server"
    "Server mode"


# endregion CHROMA MODE ENUM

# region LLM PROVIDER ENUM


class LLMProvider(str, Enum):
    """LLM provider types"""

    OLLAMA = "ollama"
    "Ollama local provider"

    OPENAI = "openai"
    "OpenAI API provider"

    ANTHROPIC = "anthropic"
    "Anthropic API provider"


# endregion LLM PROVIDER ENUM

# region LOG PRIVACY LEVEL ENUM


class LogPrivacyLevel(str, Enum):
    """Log privacy level types"""

    NONE = "none"
    "No masking applied"

    STANDARD = "standard"
    "Mask emails only"

    STRICT = "strict"
    "Mask emails and UUIDs"


# endregion LOG PRIVACY LEVEL ENUM


# region DOCUMENT STATUS ENUM


class DocumentStatus(str, Enum):
    """Document processing status types"""

    PENDING = "pending"
    "Pending processing"

    PROCESSING = "processing"
    "Currently being processed"

    COMPLETED = "completed"
    "Processing completed successfully"

    FAILED = "failed"
    "Processing failed"


# endregion DOCUMENT STATUS ENUM


# region DOCUMENT TYPE FILE ENUM


class DocumentTypeFile(str, Enum):
    """Document type file categories"""

    PDF = "pdf"
    "PDF document"

    TXT = "txt"
    "Text document"

    MD = "md"
    "Markdown document"

    DOCX = "docx"
    "Word document"


# endregion DOCUMENT TYPE FILE ENUM


# region PROMPT TYPE ENUM


class PromptType(str, Enum):
    """Prompt types for LLM interactions"""

    SYSTEM = "system"
    "Main system prompt defining assistant personality and behavior"

    RAG_CONTEXT = "rag_context"
    "Prompt for RAG-augmented responses with document context"

    TITLE_GENERATOR = "title_generator"
    "Prompt for generating session titles from conversation"

    SUMMARIZER = "summarizer"
    "Prompt for summarizing long conversations"


# endregion PROMPT TYPE ENUM

# region STREAM EVENT TYPE ENUM


class StreamEventType(str, Enum):
    """Types of streaming events."""

    STATUS = "status"
    "Progress updates: 'Searching documents...', 'Generating...'" 
    SOURCE = "source"
    "RAG source found"
    TOKEN = "token"
    "Individual token from LLM"
    DONE = "done"
    "Stream completed"
    ERROR = "error"
    "Error occurred"

# endregion STREAM EVENT TYPE ENUM