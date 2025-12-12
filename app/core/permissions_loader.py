import json
from pathlib import Path
from types import SimpleNamespace
from app.core.config import settings

# Load and parse JSON
with open(settings.SERVICE_PERMISSIONS_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

PERMISSIONS: dict[str, str] = data["permissions"]


# Build a dynamic namespace with constants
class PermissionNamespace(SimpleNamespace):
    """
    Allows access like:
        Permissions.USERS_CREATE -> "users:create"
    """


Permissions = PermissionNamespace(**{k.replace(":", "_").upper(): k for k in PERMISSIONS.keys()})
