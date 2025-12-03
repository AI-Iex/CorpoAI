import logging
from typing import Optional
from app.core.config import settings
from app.core.enums import LLMProvider
from app.core.exceptions import NotImplementedError, ValidationError
from app.clients.interfaces.llm import ILLMClient
from app.clients.interfaces.context import IContextManager
from app.clients.llm.ollama_client import OllamaClient
from app.clients.llm.context_manager import ContextManager

logger = logging.getLogger(__name__)

_llm_client: Optional[ILLMClient] = None
_context_manager: Optional[IContextManager] = None


def init_llm_client() -> ILLMClient:
    """
    Initialize LLM client.
    """
    global _llm_client

    if _llm_client is not None:
        logger.warning("LLM client already initialized, returning existing instance")
        return _llm_client

    provider_name = settings.LLM_PROVIDER.lower()

    if provider_name == LLMProvider.OLLAMA:
        logger.debug(
            "Initializing Ollama LLM client",
            extra={
                "model": settings.LLM_MODEL,
                "base_url": settings.LLM_BASE_URL,
            },
        )
        _llm_client = OllamaClient(
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
        raise ValidationError(f"Unsupported LLM provider: {provider_name}. Available providers: {available}")

    logger.debug(
        "LLM client initialized successfully",
        extra={"provider": provider_name, "model": settings.LLM_MODEL},
    )
    return _llm_client


def get_llm_client() -> ILLMClient:
    """
    Get the LLM client instance.
    """
    if _llm_client is None:
        raise RuntimeError("LLM client not initialized.")
    return _llm_client


def close_llm_client() -> None:
    """
    Close and cleanup LLM client resources.
    """
    global _llm_client
    global _context_manager

    if _llm_client is not None:
        logger.debug("Closing LLM client")
        _llm_client = None
        _context_manager = None
        logger.debug("LLM client closed successfully")
    else:
        logger.warning("LLM client already closed or never initialized")


def init_context_manager() -> IContextManager:
    """
    Initialize Context Manager (requires LLM client to be initialized first).
    """
    global _context_manager

    if _context_manager is not None:
        logger.warning("Context manager already initialized, returning existing instance")
        return _context_manager

    llm_client = get_llm_client()
    _context_manager = ContextManager(llm_client=llm_client)

    logger.debug("Context manager initialized successfully")
    return _context_manager


def get_context_manager() -> IContextManager:
    """
    Get the Context Manager instance.
    """
    if _context_manager is None:
        raise RuntimeError("Context manager not initialized. Call init_context_manager() first.")
    return _context_manager
