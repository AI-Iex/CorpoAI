from app.clients.iam_client_manager import get_iam_client
from app.clients.interfaces.iam import IIAMClient


def get_iam() -> IIAMClient:
    """
    Dependency to inject IAM client into endpoints.
    """
    return get_iam_client()
