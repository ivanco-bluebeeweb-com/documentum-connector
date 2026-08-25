"""Permissions (ACL) handlers for Documentum Connector."""
from __future__ import annotations

from imperal_sdk import ActionResult

import documentum_client as dc
from app import chat
from handlers_connection import _client_for, _resolve_connection
from schemas import (
    DocumentumPermission, GrantPermissionParams, ListPermissionsParams,
    PermissionList, RevokePermissionParams,
)


@chat.function(
    "list_permissions",
    action_type="read",
    event="documentum-connector.list_permissions",
    data_model=PermissionList,
    description="List the ACL permission grants (who can see/modify/delete) on an object.",
)
async def fn_list_permissions(ctx, params: ListPermissionsParams) -> ActionResult:
    """List ACL permission grants on a Documentum object."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/objects/{params.object_id}/permissions")
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    entries = (data or {}).get("entries", []) or (data or {}).get("results", [])
    perms = []
    for e in entries:
        props = e.get("content", e) if isinstance(e, dict) else {}
        perms.append(DocumentumPermission(
            accessor_name=props.get("accessor_name", ""),
            permission_level=props.get("permit_type", props.get("permission", "")),
        ))
    return ActionResult.success(data=PermissionList(permissions=perms).model_dump(), summary=f"{len(perms)} permission grant(s) found.")


@chat.function(
    "grant_permission",
    action_type="write",
    event="documentum-connector.grant_permission",
    data_model=DocumentumPermission,
    description="Grant an ACL permission level (e.g. Read, Write, Delete) to a user or group on an object.",
)
async def fn_grant_permission(ctx, params: GrantPermissionParams) -> ActionResult:
    """Grant an ACL permission on a Documentum object."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request(
            "POST", f"/objects/{params.object_id}/permissions",
            json_body={"accessor-name": params.accessor_name, "permit-type": params.permission_level},
        )
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(
        data=DocumentumPermission(accessor_name=params.accessor_name, permission_level=params.permission_level).model_dump(),
        summary=f"Granted '{params.permission_level}' to {params.accessor_name}.",
    )


@chat.function(
    "revoke_permission",
    action_type="write",
    event="documentum-connector.revoke_permission",
    data_model=DocumentumPermission,
    description="Revoke a user's or group's ACL permission on an object.",
)
async def fn_revoke_permission(ctx, params: RevokePermissionParams) -> ActionResult:
    """Revoke an ACL permission on a Documentum object."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request("DELETE", f"/objects/{params.object_id}/permissions/{params.accessor_name}")
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(
        data=DocumentumPermission(accessor_name=params.accessor_name, permission_level="").model_dump(),
        summary=f"Revoked access for {params.accessor_name}.",
    )
