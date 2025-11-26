import logging
from fastapi import Depends
from app.core.config import settings
from app.core.enums import LLMProvider
from app.services.interfaces.llm import ILLMProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.core.exceptions import NotImplementedError, ValidationError

logger = logging.getLogger(__name__)


def get_llm_provider() -> ILLMProvider:
    """
    Factory function to get the configured LLM provider.
    """
    provider_name = settings.LLM_PROVIDER.lower()
    
    if provider_name == LLMProvider.OLLAMA:
        logger.debug(f"Creating Ollama provider with model: {settings.LLM_MODEL}")
        return OllamaProvider(
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=settings.LLM_TIMEOUT,
        )
    
    elif provider_name == LLMProvider.OPENAI:
        
        raise NotImplementedError("OpenAI provider is not yet implemented.")
    
    elif provider_name == LLMProvider.ANTHROPIC:
        
        raise NotImplementedError("Anthropic provider is not yet implemented.")
    
    else:
        raise ValidationError(f"Unsupported LLM provider: {provider_name}.")


def get_llm(
    provider: ILLMProvider = Depends(get_llm_provider)
) -> ILLMProvider:
    """
    Dependency to inject LLM provider into endpoints.
    """
    return provider
