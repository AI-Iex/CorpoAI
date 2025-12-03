from app.clients.llm_client_manager import get_llm_client, get_context_manager as _get_context_manager
from app.clients.interfaces.llm import ILLMClient
from app.clients.interfaces.context import IContextManager


def get_llm() -> ILLMClient:
    """
    Dependency to inject LLM client into endpoints.
    """
    return get_llm_client()


def get_context_manager() -> IContextManager:
    """
    Dependency to inject Context Manager into services.
    """
    return _get_context_manager()
