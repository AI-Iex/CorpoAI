from abc import ABC, abstractmethod
from typing import Any, AsyncIterator


class ILLMProvider(ABC):
    """Interface for Language Model providers."""

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
        ...

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
        ...

    @abstractmethod
    async def check_health(self) -> bool:
        """
        Check if the LLM provider is available and healthy.
        """
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the model name being used."""
        ...
