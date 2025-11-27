import logging
import httpx
from typing import Optional
from app.core.config import settings
from app.clients.interfaces.iam import IIAMClient
from app.core.exceptions import UnauthorizedError, ServiceUnavailableError

logger = logging.getLogger(__name__)


class IAMClient(IIAMClient):
    """
    IAM client implementation.
    """

    def __init__(
        self,
        base_url: str | None = None,
        service_version: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        timeout: int | None = None,
    ):
        """
        Initialize IAM client.
        """
        self._base_url = base_url or settings.IAM_SERVICE_URL
        self._service_version = service_version or settings.IAM_SERVICE_VERSION
        self._client_id = client_id or settings.IAM_CLIENT_ID
        self._client_secret = client_secret or settings.IAM_CLIENT_SECRET
        self._timeout = timeout or settings.IAM_SERVICE_TIMEOUT

        self._api_prefix = f"/api/{self._service_version}"
        self._access_token: Optional[str] = None

        # Create IAM async client
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)

        logger.debug(f"IAM client initialized with service version: {self._service_version}")

    @property
    def service_version(self) -> str:
        """Get the service version being used."""
        return self._service_version

    async def authenticate(self) -> str:
        """
        Client authentication.
        """
        try:
            response = await self._client.post(
                f"{self._api_prefix}/auth/client",
                json={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "grant_type": "client_credentials",
                },
            )
            data = response.json()
            if response.status_code == 200:
                token_data = data.get("token", {})
                self._access_token = token_data.get("access_token")
                logger.info("Authentication successful for IAM client")
                return self._access_token

            elif response.status_code == 401:
                err_msg = data.get("detail")
                raise UnauthorizedError(err_msg or "Unauthorized credentials for IAM client")
            else:
                raise ServiceUnavailableError(f"IAM service error: {response.status_code}")

        except Exception as e:
            logger.error(f"IAM authentication failed: {type(e).__name__}")
            logger.debug(f"Err msg: {e}", exc_info=True)
            raise

    async def check_health(self) -> bool:
        """
        Check if IAM service is available
        """
        try:
            response = await self._client.get(f"{self._api_prefix}/health")
            return response.status_code == 200

        except Exception as e:
            logger.error(f"IAM health check failed: {type(e).__name__}")
            logger.debug(f"Err msg: {e}", exc_info=True)
            return False

    async def get_current_token(self) -> Optional[str]:
        """
        Get currently stored access token.
        """
        return self._access_token

    async def close(self) -> None:
        """
        Close the IAM client and release any resources.
        """
        await self._client.aclose()
