"""Connection management for Documentum Connector."""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import documentum_client as dc
from app import chat, ext
from schemas import (
    ConnectDocumentumParams, ConnectionList, DocumentumConnection,
    DisconnectDocumentumParams, NoParams,
)

_SECRET_NAME = "documentum_connections"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET_NAME)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(_SECRET_NAME, json.dumps(connections))


def _connection_entity(c: dict) -> DocumentumConnection:
    return DocumentumConnection(
        connection_id=c.get("id", ""),
        label=c.get("label") or c.get("repository_name", ""),
        repository_name=c.get("repository_name", ""),
    )


def _client_for(c: dict) -> dc.DocumentumClient:
    return dc.DocumentumClient(
        base_url=c.get("base_url", ""),
        repository_name=c.get("repository_name", ""),
        username=c.get("username", ""),
        password=c.get("password", ""),
    )


async def _resolve_connection(ctx, connection_id: str) -> dict:
    connections = await _load_connections(ctx)
    if not connections:
        raise dc.DocumentumError("No Documentum repository connected yet. Use connect_documentum first.")
    if connection_id:
        for c in connections:
            if c.get("id") == connection_id:
                return c
        raise dc.DocumentumError(f"No connection found with id '{connection_id}'.")
    return connections[0]


@chat.function(
    "connect_documentum",
    action_type="write",
    event="documentum-connector.connect",
    data_model=DocumentumConnection,
    description="Connect a Documentum repository via base URL, repository name, and username/password.",
)
async def fn_connect_documentum(ctx, params: ConnectDocumentumParams) -> ActionResult:
    """Connect a Documentum repository, verifying it can actually be reached."""
    client = dc.DocumentumClient(
        base_url=params.base_url,
        repository_name=params.repository_name,
        username=params.username,
        password=params.password,
    )
    try:
        await client.request_absolute("GET", f"/repositories/{params.repository_name}")
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    connections = await _load_connections(ctx)
    conn_id = str(uuid.uuid4())
    record = {
        "id": conn_id,
        "label": params.label or params.repository_name,
        "base_url": params.base_url.strip().rstrip("/"),
        "repository_name": params.repository_name,
        "username": params.username,
        "password": params.password,
    }
    connections.append(record)
    await _save_connections(ctx, connections)
    return ActionResult.success(
        data=_connection_entity(record).model_dump(),
        summary=f"Connected to Documentum repository '{record['label']}'.",
    )


@chat.function(
    "disconnect_documentum",
    action_type="write",
    event="documentum-connector.disconnect",
    description="Disconnect a saved Documentum repository connection.",
)
async def fn_disconnect_documentum(ctx, params: DisconnectDocumentumParams) -> ActionResult:
    """Remove a saved Documentum connection."""
    connections = await _load_connections(ctx)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    if len(remaining) == len(connections):
        return ActionResult.error(f"No connection found with id '{params.connection_id}'.")
    await _save_connections(ctx, remaining)
    return ActionResult.success(data={"disconnected": True}, summary="Documentum repository disconnected.")


@chat.function(
    "list_connections",
    action_type="read",
    event="documentum-connector.list_connections",
    data_model=ConnectionList,
    description="List the connected Documentum repositories.",
)
async def fn_list_connections(ctx, params: NoParams) -> ActionResult:
    """List saved Documentum connections."""
    connections = await _load_connections(ctx)
    entities = [_connection_entity(c) for c in connections]
    return ActionResult.success(
        data=ConnectionList(connections=entities).model_dump(),
        summary=f"{len(entities)} Documentum repository/ies connected.",
    )
