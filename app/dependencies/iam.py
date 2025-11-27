import logging
from fastapi import Depends
from app.clients.iam.iam_client import IAMClient
from app.core.config import settings
from app.clients.interfaces.iam import IIAMClient

logger = logging.getLogger(__name__)


def get_iam_client() -> IIAMClient:
    """
    Factory function to get the configured IAM client.
    """

    logger.debug(f"Creating IAM client with service version: {settings.IAM_SERVICE_VERSION}")

    return IAMClient(
        base_url=settings.IAM_SERVICE_URL,
        service_version=settings.IAM_SERVICE_VERSION,
        client_id=settings.IAM_CLIENT_ID,
        client_secret=settings.IAM_CLIENT_SECRET,
        timeout=settings.IAM_SERVICE_TIMEOUT,
    )
