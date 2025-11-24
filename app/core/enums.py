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
