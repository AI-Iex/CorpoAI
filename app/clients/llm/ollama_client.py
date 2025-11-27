import logging
from typing import Any, AsyncIterator
import ollama
from app.core.config import settings
from app.clients.interfaces.llm import ILLMClient

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
    ):
        """
        Initialize Ollama client.
        """
        self._base_url = base_url or settings.LLM_BASE_URL
        self._model = model or settings.LLM_MODEL
        self._temperature = temperature or settings.LLM_TEMPERATURE
        self._max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        self._timeout = timeout or settings.LLM_TIMEOUT

        # Create Ollama async client
        self._client = ollama.AsyncClient(host=self._base_url)
        
        logger.info(f"Ollama client initialized with model: {self._model}")

    @property
    def model_name(self) -> str:
        """Get the model name being used."""
        return self._model

    async def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any
    ) -> str:
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
                    **kwargs
                },
                stream=False
            )
            
            return response['response']
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {type(e).__name__}")
            logger.debug(f"Err msg: {e}", exc_info=True)
            raise

    async def generate_stream(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any
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
                    **kwargs
                },
                stream=True
            )
            
            async for chunk in stream:
                if 'response' in chunk:
                    yield chunk['response']
                    
        except Exception as e:
            logger.error(f"Ollama streaming failed: {type(e).__name__}")
            logger.debug(f"Err msg: {e}", exc_info=True)
            raise

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
                logger.warning(
                    f"Ollama model '{self._model}' not found. "
                    f"Available: {model_names}"
                )
                return False
                
        except Exception as e:
            logger.error(f"Ollama health check failed: {type(e).__name__}")
            logger.debug(f"Err msg: {e}", exc_info=True)
            return False
