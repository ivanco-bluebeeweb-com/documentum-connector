"""Documentum Connector extension declaration.

Documentum Content Server is managed via Documentum REST Services
(base path .../dctm-rest/repositories/{repo}) using HTTP Basic Auth --
username+password sent on every request. There is no token/ticket to
cache, so credentials are stored directly and reused as-is on every call
(see documentum_client.py).
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "documentum-connector",
    version="0.1.0",
    display_name="Documentum",
    description=(
        "Connect your own OpenText Documentum repository to browse and "
        "manage Cabinets, Folders, Documents, Versions (checkout/checkin), "
        "Permissions, Lifecycles, and run a content-health audit."
    ),
    icon="icon.svg",
    capabilities=["documentum:read", "documentum:write"],
    actions_explicit=True,
    system=False,
)

chat = ChatExtension(
    ext,
    tool_name="documentum",
    description=(
        "Documentum Connector — manage Cabinets, Folders, Documents, "
        "Versions, Permissions, and Lifecycles in a connected Documentum "
        "repository."
    ),
)

ext.secret(
    "documentum_connections",
    "JSON list of connected Documentum repositories and their username/password (Basic Auth, sent on every request). Managed only through connect_documentum and disconnect_documentum.",
    required=True,
    write_mode="both",
    max_bytes=65536,
    rotation_hint_days=90,
)(lambda: None)


@ext.health_check
async def health_check(ctx) -> dict:
    """Report whether at least one Documentum connection is saved."""
    import json

    raw = await ctx.secrets.get("documentum_connections")
    try:
        connections = json.loads(raw) if raw else []
    except (TypeError, ValueError):
        connections = []
    return {
        "healthy": True,
        "connected_repositories": len(connections) if isinstance(connections, list) else 0,
    }
