from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, List, Union, TYPE_CHECKING
from app.core.enums import PromptType
from app.schemas.context import LLMMessage, LLMResponse

if TYPE_CHECKING:
    from app.tools.schemas import ToolDefinition

MessageType = Union[LLMMessage, dict]


class ILLMClient(ABC):
    """
    Interface for LLM clients (Ollama, OpenAI, Anthropic, etc.). Qwen 
    """

    @abstractmethod
    async def chat(
        self,
        messages: List[MessageType],
        tools: List["ToolDefinition"] | None = None,
        thinking: bool | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Send a chat conversation and get a response.

        Args:
            messages: Conversation messages
            tools: Tool definitions available for this request
            thinking: Enable thinking/reasoning mode
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific options

        Returns:
            LLMResponse with content and/or tool_calls
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[MessageType],
        tools: List["ToolDefinition"] | None = None,
        thinking: bool | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Send a chat conversation and get a response with streaming.

        Note: Tool calls are not supported in streaming mode.
        """
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        thinking: bool | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a completion from the prompt.
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        thinking: bool | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Generate a completion with streaming.
        """
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """
        Check if LLM service is healthy and model is available.
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Get the model name being used.
        """
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """
        Get the system prompt being used.
        """
        pass

    @abstractmethod
    def get_prompt(self, prompt_type: PromptType) -> str:
        """
        Get a prompt by type.
        """
        pass
