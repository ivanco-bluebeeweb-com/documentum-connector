"""Document content handlers (upload/download) for Documentum Connector."""
from __future__ import annotations

import base64

from imperal_sdk import ActionResult

import documentum_client as dc
from app import chat
from handlers_connection import _client_for, _resolve_connection
from handlers_objects import _object_entity
from schemas import (
    DownloadDocumentParams, DownloadResult, UploadDocumentParams,
    UploadResult, UploadVersionParams,
)


@chat.function(
    "download_document",
    action_type="read",
    event="documentum-connector.download_document",
    data_model=DownloadResult,
    description="Download a document's primary content, base64-encoded.",
)
async def fn_download_document(ctx, params: DownloadDocumentParams) -> ActionResult:
    """Download a Documentum document's raw content."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        meta = await client.request("GET", f"/objects/{params.object_id}")
        content = await client.download(params.object_id)
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    obj = (meta or {}).get("content", meta)
    entity = _object_entity(obj)
    return ActionResult.success(
        data=DownloadResult(name=entity.name, content_base64=base64.b64encode(content).decode()).model_dump(),
        summary=f"Downloaded '{entity.name}' ({len(content)} bytes).",
    )


@chat.function(
    "upload_document",
    action_type="write",
    event="documentum-connector.upload_document",
    data_model=UploadResult,
    description="Upload a new document (base64-encoded content) into a folder.",
)
async def fn_upload_document(ctx, params: UploadDocumentParams) -> ActionResult:
    """Upload a new document into a Documentum folder."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        raw = base64.b64decode(params.content_base64)
    except Exception:
        return ActionResult.error("content_base64 is not valid base64.")
    try:
        data = await client.upload(params.name, params.parent_folder_id, raw)
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    obj = (data or {}).get("content", data)
    entity = _object_entity(obj)
    return ActionResult.success(data=UploadResult(object_id=entity.object_id, name=entity.name).model_dump(), summary=f"Document '{entity.name}' uploaded.")


@chat.function(
    "upload_document_version",
    action_type="write",
    event="documentum-connector.upload_document_version",
    data_model=UploadResult,
    description="Check in a new version of an existing document (base64-encoded content).",
)
async def fn_upload_document_version(ctx, params: UploadVersionParams) -> ActionResult:
    """Check in a new version of an existing Documentum document."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        raw = base64.b64decode(params.content_base64)
    except Exception:
        return ActionResult.error("content_base64 is not valid base64.")
    try:
        data = await client.upload_version(params.object_id, params.name, raw)
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    obj = (data or {}).get("content", data)
    entity = _object_entity(obj)
    return ActionResult.success(data=UploadResult(object_id=entity.object_id, name=entity.name).model_dump(), summary=f"New version of '{entity.name}' checked in.")
