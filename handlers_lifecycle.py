"""Lifecycle handlers for Documentum Connector."""
from __future__ import annotations

from imperal_sdk import ActionResult

import documentum_client as dc
from app import chat
from handlers_connection import _client_for, _resolve_connection
from schemas import (
    DemoteLifecycleParams, GetLifecycleStateParams, LifecycleState,
    PromoteLifecycleParams,
)


@chat.function(
    "get_lifecycle_state",
    action_type="read",
    event="documentum-connector.get_lifecycle_state",
    data_model=LifecycleState,
    description="Read an object's current lifecycle name and state (e.g. Draft, Review, Approved).",
)
async def fn_get_lifecycle_state(ctx, params: GetLifecycleStateParams) -> ActionResult:
    """Read a Documentum object's current lifecycle state."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/objects/{params.object_id}")
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    props = (data or {}).get("content", data).get("properties", {}) if isinstance(data, dict) else {}
    state = LifecycleState(
        object_id=params.object_id,
        lifecycle_name=props.get("r_policy_id", "") or "",
        current_state=props.get("r_current_state", "") or "",
    )
    return ActionResult.success(data=state.model_dump(), summary=f"Lifecycle state: {state.current_state or 'none'}.")


@chat.function(
    "promote_lifecycle",
    action_type="write",
    event="documentum-connector.promote_lifecycle",
    data_model=LifecycleState,
    description="Promote an object to the next lifecycle state (e.g. Draft -> Review).",
)
async def fn_promote_lifecycle(ctx, params: PromoteLifecycleParams) -> ActionResult:
    """Promote a Documentum object's lifecycle to its next state."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request("PUT", f"/objects/{params.object_id}/lifecycle/promote")
        data = await client.request("GET", f"/objects/{params.object_id}")
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    props = (data or {}).get("content", data).get("properties", {}) if isinstance(data, dict) else {}
    state = LifecycleState(object_id=params.object_id, lifecycle_name=props.get("r_policy_id", "") or "", current_state=props.get("r_current_state", "") or "")
    return ActionResult.success(data=state.model_dump(), summary=f"Promoted to '{state.current_state}'.")


@chat.function(
    "demote_lifecycle",
    action_type="write",
    event="documentum-connector.demote_lifecycle",
    data_model=LifecycleState,
    description="Demote an object to its previous lifecycle state.",
)
async def fn_demote_lifecycle(ctx, params: DemoteLifecycleParams) -> ActionResult:
    """Demote a Documentum object's lifecycle to its previous state."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request("PUT", f"/objects/{params.object_id}/lifecycle/demote")
        data = await client.request("GET", f"/objects/{params.object_id}")
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    props = (data or {}).get("content", data).get("properties", {}) if isinstance(data, dict) else {}
    state = LifecycleState(object_id=params.object_id, lifecycle_name=props.get("r_policy_id", "") or "", current_state=props.get("r_current_state", "") or "")
    return ActionResult.success(data=state.model_dump(), summary=f"Demoted to '{state.current_state}'.")
