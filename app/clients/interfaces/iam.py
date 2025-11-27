from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional


class IIAMClient(ABC):
    """
    Interface for IAM clients
    """

    @abstractmethod
    async def authenticate(self) -> str:
        """
        Perform client authentication.
        """
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """
        Check if IAM service is healthy and available.
        """
        pass

    @abstractmethod
    async def get_current_token(self) -> Optional[str]:
        """
        Get stored access token.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close the IAM client and release any resources.
        """
        pass

    @property
    @abstractmethod
    def service_version(self) -> str:
        """
        Get the service version being used.
        """
        pass

