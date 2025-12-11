import logging
from typing import Any, AsyncIterator, List
import ollama
from app.clients.interfaces.llm import ILLMClient, LLMResponse, MessageType
from app.core.config import settings
from app.core.enums import PromptType, MessageRoleTypes
from app.core.exceptions import LLMError
from app.core.prompts import PromptLoader, get_prompt_loader
from app.schemas.context import LLMMessage

logger = logging.getLogger(__name__)


class OllamaClient(ILLMClient):
    """
    Ollama LLM client implementation.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
        prompt_loader: PromptLoader | None = None,
    ):
        """
        Initialize Ollama client.
        """
        self._base_url = base_url or settings.LLM_BASE_URL
        self._model = model or settings.LLM_MODEL
        self._temperature = temperature or settings.LLM_TEMPERATURE
        self._max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        self._timeout = timeout or settings.LLM_TIMEOUT
        self._prompt_loader = prompt_loader or get_prompt_loader()

        # Create Ollama async client
        self._client = ollama.AsyncClient(host=self._base_url)

        logger.debug(f"Ollama client initialized with model: {self._model}")

    @property
    def model_name(self) -> str:
        """Get the model name being used."""
        return self._model

    @property
    def system_prompt(self) -> str:
        """Get the system prompt from the loader."""
        return self._prompt_loader.get_or_default(PromptType.SYSTEM)

    @property
    def prompt_loader(self) -> PromptLoader:
        """Get the prompt loader instance."""
        return self._prompt_loader

    def get_prompt(self, prompt_type: PromptType) -> str:
        """
        Get a prompt by type.
        """
        return self._prompt_loader.get(prompt_type)

    def _normalize_messages(self, messages: List[MessageType]) -> List[dict]:
        """Convert LLMMessage objects to dicts for Ollama API."""
        result = []
        for msg in messages:
            if isinstance(msg, LLMMessage):
                result.append({"role": msg.role.value, "content": msg.content})
            else:
                result.append(msg)
        return result

    def _build_messages(
        self,
        messages: List[MessageType],
        system_prompt_override: str | None = None,
    ) -> List[dict]:
        """
        Build messages list with system prompt prepended.
        Always ensures the main system prompt is first.
        """
        prompt = system_prompt_override or self.system_prompt

        # Normalize to dicts
        normalized = self._normalize_messages(messages)

        # Check if the first message is the main system prompt
        if normalized and normalized[0].get("role") == MessageRoleTypes.SYSTEM.value:
            first_content = normalized[0].get("content", "")
            # If first message starts with the system prompt, don't duplicate
            if first_content.startswith(prompt[:50]):
                return normalized

        # Prepend main system message
        return [{"role": MessageRoleTypes.SYSTEM.value, "content": prompt}] + normalized

    async def chat(
        self,
        messages: List[MessageType],
        thinking: bool | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a chat response to a message and history.
        """
        try:
            final_messages = self._build_messages(messages, system_prompt)

            print(final_messages)

            response = await self._client.chat(
                model=self._model,
                messages=final_messages,
                options={
                    "temperature": temperature or self._temperature,
                    "num_predict": max_tokens or self._max_tokens,
                    "num_ctx_tokens": settings.LLM_MAX_CONTEXT_LENGTH,
                    **kwargs,
                },
                stream=False,
                think=thinking if thinking is not None else False,
            )

            # Extract token counts
            tokens_used = None
            if "eval_count" in response:
                tokens_used = response.get("eval_count", 0) + response.get("prompt_eval_count", 0)

            # Ensure content is not empty
            content = response["message"]["content"].strip()

            if not content:
                raise ValueError("Ollama chat response content is empty.")

            return LLMResponse(
                content=content,
                tokens_used=tokens_used,
                model=self._model,
            )

        except ollama.ResponseError as e:
            status_code = getattr(e, "status_code", 502)
            raise LLMError(f"LLM error: {e}", status_code=status_code)

        except Exception as e:
            logger.error(f"Ollama chat failed: {type(e).__name__}")
            logger.debug(f"Err msg: {e}", exc_info=True)
            raise LLMError("LLM error")

    async def chat_stream(
        self,
        messages: List[MessageType],
        thinking: bool | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Generate a chat response with streaming.
        """
        try:
            final_messages = self._build_messages(messages, system_prompt)

            stream = await self._client.chat(
                model=self._model,
                messages=final_messages,
                options={
                    "temperature": temperature or self._temperature,
                    "num_predict": max_tokens or self._max_tokens,
                    "num_ctx_tokens": settings.LLM_MAX_CONTEXT_LENGTH,
                    **kwargs,
                },
                stream=True,
                think=thinking if thinking is not None else False,
            )

            async for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]

        except ollama.ResponseError as e:
            status_code = getattr(e, "status_code", 502)
            raise LLMError(f"LLM error: {e}", status_code=status_code)

        except Exception as e:
            logger.error(f"Ollama chat streaming failed: {type(e).__name__}")
            logger.debug(f"Err msg: {e}", exc_info=True)
            raise LLMError("LLM error")

    async def generate(
        self,
        prompt: str,
        thinking: bool | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a response.
        """
        try:
            response = await self._client.generate(
                model=self._model,
                prompt=prompt,
                options={
                    "temperature": temperature or self._temperature,
                    "num_predict": max_tokens or self._max_tokens,
                    "num_ctx_tokens": settings.LLM_MAX_CONTEXT_LENGTH,
                    **kwargs,
                },
                stream=False,
                think=thinking if thinking is not None else False,
            )

            # Extract token counts
            tokens_used = None
            if "eval_count" in response:
                tokens_used = response.get("eval_count", 0) + response.get("prompt_eval_count", 0)

            content = response.get("response", "").strip()

            if not content:
                raise ValueError("Ollama chat response content is empty.")

            return LLMResponse(
                content=content,
                tokens_used=tokens_used,
                model=self._model,
            )

        except ollama.ResponseError as e:
            status_code = getattr(e, "status_code", 502)
            raise LLMError(f"LLM error: {e}", status_code=status_code)

        except Exception as e:
            logger.error(f"Ollama generation failed: {type(e).__name__}")
            logger.debug(f"Err msg: {e}", exc_info=True)
            raise LLMError("LLM error")

    async def generate_stream(
        self,
        prompt: str,
        thinking: bool | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Generate a response with streaming.
        """
        try:
            stream = await self._client.generate(
                model=self._model,
                prompt=prompt,
                options={
                    "temperature": temperature or self._temperature,
                    "num_predict": max_tokens or self._max_tokens,
                    "num_ctx_tokens": settings.LLM_MAX_CONTEXT_LENGTH,
                    **kwargs,
                },
                stream=True,
                think=thinking if thinking is not None else False,
            )

            async for chunk in stream:
                if "response" in chunk:
                    yield chunk["response"]

        except ollama.ResponseError as e:
            status_code = getattr(e, "status_code", 502)
            raise LLMError(f"LLM error: {e}", status_code=status_code)

        except Exception as e:
            logger.error(f"Ollama streaming failed: {type(e).__name__}")
            logger.debug(f"Err msg: {e}", exc_info=True)
            raise LLMError("LLM error")

    async def check_health(self) -> bool:
        """
        Check if Ollama service is available and the model is ready.
        """
        try:
            # List available models
            models_response = await self._client.list()

            # Extract model names from response
            model_names = [model.model for model in models_response.models]

            if self._model in model_names:
                logger.debug(f"Ollama model '{self._model}' is available")
                return True
            else:
                logger.warning(f"Ollama model '{self._model}' not found. " f"Available: {model_names}")
                return False

        except Exception as e:
            logger.error(f"Ollama health check failed: {type(e).__name__}")
            logger.debug(f"Err msg: {e}", exc_info=True)
            return False
