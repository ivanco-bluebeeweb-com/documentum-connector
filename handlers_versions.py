"""Version and checkout/checkin handlers for Documentum Connector."""
from __future__ import annotations

from imperal_sdk import ActionResult

import documentum_client as dc
from app import chat
from handlers_connection import _client_for, _resolve_connection
from handlers_objects import _object_entity
from schemas import (
    CancelCheckoutParams, CheckinParams, CheckoutParams, CheckoutResult,
    DocumentumVersion, ListVersionsParams, VersionList,
)


@chat.function(
    "list_versions",
    action_type="read",
    event="documentum-connector.list_versions",
    data_model=VersionList,
    description="List the version tree of a document.",
)
async def fn_list_versions(ctx, params: ListVersionsParams) -> ActionResult:
    """List saved versions of a Documentum document."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/objects/{params.object_id}/versions")
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    entries = (data or {}).get("entries", []) or (data or {}).get("results", [])
    versions = []
    for e in entries:
        props = e.get("content", {}).get("properties", e) if isinstance(e, dict) else {}
        versions.append(DocumentumVersion(
            version_label=",".join(props.get("r_version_label", [])) if isinstance(props.get("r_version_label"), list) else str(props.get("r_version_label", "")),
            object_id=str(props.get("r_object_id", "")),
            modify_date=props.get("r_modify_date", "") or "",
            modified_by=props.get("r_modifier", "") or "",
        ))
    return ActionResult.success(data=VersionList(versions=versions).model_dump(), summary=f"{len(versions)} version(s) found.")


@chat.function(
    "checkout_document",
    action_type="write",
    event="documentum-connector.checkout_document",
    data_model=CheckoutResult,
    description="Check out a document, locking it for editing by the connected user.",
)
async def fn_checkout_document(ctx, params: CheckoutParams) -> ActionResult:
    """Check out a Documentum document for editing."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request("PUT", f"/objects/{params.object_id}", json_body={"checkout": True})
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=CheckoutResult(object_id=params.object_id, checked_out=True).model_dump(), summary="Document checked out.")


@chat.function(
    "cancel_checkout",
    action_type="write",
    event="documentum-connector.cancel_checkout",
    data_model=CheckoutResult,
    description="Cancel a checkout without saving changes, releasing the lock.",
)
async def fn_cancel_checkout(ctx, params: CancelCheckoutParams) -> ActionResult:
    """Cancel a Documentum document checkout (release lock, discard edits)."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request("PUT", f"/objects/{params.object_id}", json_body={"cancel-checkout": True})
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=CheckoutResult(object_id=params.object_id, checked_out=False).model_dump(), summary="Checkout cancelled.")


@chat.function(
    "checkin_document",
    action_type="write",
    event="documentum-connector.checkin_document",
    data_model=CheckoutResult,
    description="Check in a checked-out document, saving it as a new version and releasing the lock (or keeping it checked out for another iterative save).",
)
async def fn_checkin_document(ctx, params: CheckinParams) -> ActionResult:
    """Check in a Documentum document, completing the checkout/checkin cycle."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request(
            "PUT", f"/objects/{params.object_id}",
            json_body={"checkin": True, "keep-checked-out": params.keep_checked_out},
        )
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    summary = "Checked in; still checked out for another save." if params.keep_checked_out else "Checked in and lock released."
    return ActionResult.success(
        data=CheckoutResult(object_id=params.object_id, checked_out=params.keep_checked_out).model_dump(),
        summary=summary,
    )
