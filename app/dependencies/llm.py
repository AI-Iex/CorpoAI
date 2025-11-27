import logging
from fastapi import Depends
from app.core.config import settings
from app.core.enums import LLMProvider
from app.clients.interfaces.llm import ILLMClient
from app.clients.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


def get_llm_client() -> ILLMClient:
    """
    Factory function to get the configured LLM client.
    Returns the appropriate client based on LLM_PROVIDER setting.
    """
    provider_name = settings.LLM_PROVIDER.lower()
    
    if provider_name == LLMProvider.OLLAMA:
        logger.debug(f"Creating Ollama client with model: {settings.LLM_MODEL}")
        return OllamaClient(
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=settings.LLM_TIMEOUT,
        )
    
    elif provider_name == LLMProvider.OPENAI:
        raise NotImplementedError("OpenAI client is not yet implemented.")
    
    elif provider_name == LLMProvider.ANTHROPIC:
        raise NotImplementedError("Anthropic client is not yet implemented.")
    
    else:
        available = ", ".join([p.value for p in LLMProvider])
        raise ValueError(
            f"Unsupported LLM provider: {provider_name}. "
            f"Available providers: {available}"
        )


def get_llm(
    client: ILLMClient = Depends(get_llm_client)
) -> ILLMClient:
    """
    Dependency to inject LLM client into endpoints.
    """
    return client
