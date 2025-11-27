from app.clients.llm_client_manager import get_llm_client
from app.clients.interfaces.llm import ILLMClient


def get_llm() -> ILLMClient:
    """
    Dependency to inject LLM client into endpoints.
    """
    return get_llm_client()
