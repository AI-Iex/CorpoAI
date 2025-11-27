from abc import ABC, abstractmethod
from typing import Any, AsyncIterator


class ILLMClient(ABC):
    """
    Interface for LLM clients (Ollama, OpenAI, Anthropic, etc.).
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any
    ) -> str:
        """
        Generate a completion from the prompt.
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any
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
