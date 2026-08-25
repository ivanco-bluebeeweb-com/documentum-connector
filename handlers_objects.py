"""Cabinet/folder/object handlers for Documentum Connector."""
from __future__ import annotations

from imperal_sdk import ActionResult

import documentum_client as dc
from app import chat
from handlers_connection import _client_for, _resolve_connection
from schemas import (
    CreateFolderParams, DeleteResult, DocumentumObject, ListCabinetsParams,
    ListFolderContentsParams, ObjectIdParams, ObjectList,
    RenameOrMoveObjectParams,
)


def _object_entity(o: dict) -> DocumentumObject:
    props = o.get("properties", o) if isinstance(o, dict) else {}
    return DocumentumObject(
        object_id=str(props.get("r_object_id", props.get("object_id", ""))),
        name=props.get("object_name", props.get("name", "")),
        object_type=props.get("r_object_type", ""),
        parent_id=str(props.get("i_folder_id", "") or ""),
        size_bytes=int(props.get("r_full_content_size", 0) or 0),
        modify_date=props.get("r_modify_date", "") or "",
        checked_out_by=props.get("r_lock_owner", "") or "",
    )


@chat.function(
    "list_cabinets",
    action_type="read",
    event="documentum-connector.list_cabinets",
    data_model=ObjectList,
    description="List top-level Cabinets in the connected repository.",
)
async def fn_list_cabinets(ctx, params: ListCabinetsParams) -> ActionResult:
    """List top-level cabinets in the connected Documentum repository."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", "/cabinets")
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    entries = (data or {}).get("entries", []) or (data or {}).get("results", [])
    objects = [_object_entity(e.get("content", e)) for e in entries]
    return ActionResult.success(data=ObjectList(objects=objects).model_dump(), summary=f"{len(objects)} cabinet(s) found.")


@chat.function(
    "get_object",
    action_type="read",
    event="documentum-connector.get_object",
    data_model=DocumentumObject,
    description="Read one Documentum object's (folder or document) metadata in full.",
)
async def fn_get_object(ctx, params: ObjectIdParams) -> ActionResult:
    """Read one Documentum object's metadata."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/objects/{params.object_id}")
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    obj = (data or {}).get("content", data)
    entity = _object_entity(obj)
    return ActionResult.success(data=entity.model_dump(), summary=f"Object '{entity.name}' loaded.")


@chat.function(
    "list_folder_contents",
    action_type="read",
    event="documentum-connector.list_folder_contents",
    data_model=ObjectList,
    description="List the folders and documents inside a folder or cabinet.",
)
async def fn_list_folder_contents(ctx, params: ListFolderContentsParams) -> ActionResult:
    """List a Documentum folder's contents."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/folders/{params.object_id}/contents", query={"items-per-page": params.limit})
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    entries = (data or {}).get("entries", []) or (data or {}).get("results", [])
    objects = [_object_entity(e.get("content", e)) for e in entries]
    return ActionResult.success(data=ObjectList(objects=objects).model_dump(), summary=f"{len(objects)} item(s) found.")


@chat.function(
    "create_folder",
    action_type="write",
    event="documentum-connector.create_folder",
    data_model=DocumentumObject,
    description="Create a new folder inside an existing folder or cabinet.",
)
async def fn_create_folder(ctx, params: CreateFolderParams) -> ActionResult:
    """Create a new Documentum folder."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request(
            "POST", "/folders",
            json_body={"properties": {"object_name": params.name, "r_object_type": "dm_folder"},
                       "parent-folder-id": params.parent_id},
        )
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    obj = (data or {}).get("content", data)
    entity = _object_entity(obj)
    return ActionResult.success(data=entity.model_dump(), summary=f"Folder '{params.name}' created.")


@chat.function(
    "rename_or_move_object",
    action_type="write",
    event="documentum-connector.rename_or_move_object",
    data_model=DocumentumObject,
    description="Rename an object and/or move it to a new parent folder.",
)
async def fn_rename_or_move_object(ctx, params: RenameOrMoveObjectParams) -> ActionResult:
    """Rename and/or move a Documentum object."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    body: dict = {}
    if params.name:
        body["properties"] = {"object_name": params.name}
    if params.new_parent_id:
        body["parent-folder-id"] = params.new_parent_id
    if not body:
        return ActionResult.error("Provide a new name and/or a new_parent_id.")
    try:
        data = await client.request("PUT", f"/objects/{params.object_id}", json_body=body)
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    obj = (data or {}).get("content", data)
    entity = _object_entity(obj)
    return ActionResult.success(data=entity.model_dump(), summary=f"Object '{entity.name}' updated.")


@chat.function(
    "delete_object",
    action_type="write",
    event="documentum-connector.delete_object",
    data_model=DeleteResult,
    description="Permanently delete a folder or document. Cannot be undone.",
)
async def fn_delete_object(ctx, params: ObjectIdParams) -> ActionResult:
    """Permanently delete a Documentum object."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request("DELETE", f"/objects/{params.object_id}")
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=DeleteResult(deleted=True, item_id=params.object_id).model_dump(), summary="Object deleted.")
