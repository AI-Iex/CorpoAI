from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.core.enums import MessageRoleTypes


# region LLM MESSAGE


class LLMMessage(BaseModel):
    """
    A message in LLM format.

    Used for communication with the LLM client.
    """

    role: MessageRoleTypes = Field(..., description="Message role: system, user, assistant")
    content: str = Field(..., description="Message content")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "user",
                "content": "What is the company's vacation policy?",
            }
        }
    )

    @classmethod
    def system(cls, content: str) -> "LLMMessage":
        """Create a system message."""
        return cls(role=MessageRoleTypes.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> "LLMMessage":
        """Create a user message."""
        return cls(role=MessageRoleTypes.USER, content=content)

    @classmethod
    def assistant(cls, content: str) -> "LLMMessage":
        """Create an assistant message."""
        return cls(role=MessageRoleTypes.ASSISTANT, content=content)


# endregion LLM MESSAGE


# region LLM RESPONSE


class LLMResponse(BaseModel):
    """Response from LLM chat or generation."""

    content: str = Field(..., description="Generated content from LLM")
    tokens_used: Optional[int] = Field(None, description="Total tokens used (prompt + completion)")
    model: Optional[str] = Field(None, description="Model used for generation")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "The company's vacation policy allows...",
                "tokens_used": 150,
                "model": "llama3.1:8b",
            }
        }
    )


# endregion LLM RESPONSE

# region TOKEN BUDGET


class ContextBudget(BaseModel):
    """
    Token budget breakdown for LLM context.

    Tracks token usage across all context components.
    """

    max_tokens: int = Field(..., description="Maximum context window size")
    reserved_output: int = Field(..., description="Tokens reserved for model response")

    system_prompt_tokens: int = Field(0, description="Tokens used by system prompt")
    summary_tokens: int = Field(0, description="Tokens used by conversation summary")
    history_tokens: int = Field(0, description="Tokens used by message history")
    new_message_tokens: int = Field(0, description="Tokens used by new user message")
    rag_context_tokens: int = Field(0, description="Tokens used by RAG context")
    tools_tokens: int = Field(0, description="Tokens used by tool definitions")

    @property
    def available_for_input(self) -> int:
        """Tokens available for input (excluding reserved output)."""
        return self.max_tokens - self.reserved_output

    @property
    def total_used(self) -> int:
        """Total tokens used by all components."""
        return (
            self.system_prompt_tokens
            + self.summary_tokens
            + self.history_tokens
            + self.new_message_tokens
            + self.rag_context_tokens
            + self.tools_tokens
        )

    @property
    def remaining(self) -> int:
        """Tokens remaining within budget."""
        return self.available_for_input - self.total_used

    @property
    def is_over_budget(self) -> bool:
        """Check if context exceeds available budget."""
        return self.total_used > self.available_for_input

    def __repr__(self) -> str:
        return (
            f"ContextBudget(used={self.total_used}/{self.available_for_input}, "
            f"remaining={self.remaining}, over={self.is_over_budget})"
        )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "max_tokens": 8000,
                "reserved_output": 1024,
                "system_prompt_tokens": 500,
                "summary_tokens": 200,
                "history_tokens": 1500,
                "new_message_tokens": 50,
                "rag_context_tokens": 0,
                "tools_tokens": 0,
            }
        }
    )


# endregion TOKEN BUDGET

# region CONTEXT RESULT


class ContextResult(BaseModel):
    """
    Result of context building for LLM.
    """

    messages: List[LLMMessage] = Field(
        ...,
        description="Final message list for LLM (excludes main system prompt)",
    )
    budget: Optional[ContextBudget] = Field(
        None,
        description="Token budget breakdown for debugging",
    )
    needs_summary_update: bool = Field(
        False,
        description="Whether session summary should be updated",
    )
    new_summary: Optional[str] = Field(
        None,
        description="New summary text if generated",
    )
    summary_up_to_message_id: Optional[UUID] = Field(
        None,
        description="ID of last message included in the new summary",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messages": [
                    {"role": "system", "content": "[Summary] Previous discussion..."},
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi! How can I help?"},
                ],
                "budget": {
                    "max_tokens": 8000,
                    "reserved_output": 1024,
                    "system_prompt_tokens": 500,
                    "history_tokens": 100,
                },
                "needs_summary_update": False,
                "new_summary": None,
                "summary_up_to_message_id": None,
            }
        }
    )


# endregion CONTEXT RESULT

# region UNSUMMARIZED MESSAGES


class UnsummarizedMessages(BaseModel):
    """
    Messages that haven't been included in the session summary yet.
    """

    messages: List[LLMMessage] = Field(
        ...,
        description="Messages in LLM format",
    )
    message_ids: List[UUID] = Field(
        ...,
        description="Original message UUIDs, for tracking summarization",
    )

    @property
    def count(self) -> int:
        """Number of unsummarized messages."""
        return len(self.messages)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi!"},
                ],
                "message_ids": [
                    "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                ],
            }
        }
    )


# endregion UNSUMMARIZED MESSAGES
