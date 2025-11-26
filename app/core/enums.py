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
