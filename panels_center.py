"""Documentum Connector -- center panels for Cabinets and Content Audit."""
from __future__ import annotations

from imperal_sdk import ui

import handlers_connection as h
import handlers_objects as ho
import handlers_search as hs
from app import ext
from schemas import AuditContentParams, ListCabinetsParams


def _table_or_empty(rows, columns, empty_message, empty_icon):
    if not rows:
        return ui.Empty(message=empty_message, icon=empty_icon)
    return ui.DataTable(rows=rows, columns=columns)


@ext.panel("documentum_cabinets", slot="center", title="Cabinets", center_overlay=True)
async def documentum_cabinets(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="Folder")
    result = await ho.fn_list_cabinets(ctx, ListCabinetsParams())
    if not result.success:
        return ui.Alert(type="error", message=result.error or "Could not load cabinets")
    objects = (result.data or {}).get("objects", [])
    rows = [{"name": o["name"], "object_type": o["object_type"], "object_id": o["object_id"]} for o in objects]
    columns = [
        ui.DataColumn(key="name", label="Name"),
        ui.DataColumn(key="object_type", label="Type"),
        ui.DataColumn(key="object_id", label="Object ID"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Cabinets", level=2),
        _table_or_empty(rows, columns, "No cabinets found", "Folder"),
    ])


@ext.panel("documentum_audit", slot="center", title="Content audit", center_overlay=True)
async def documentum_audit(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="ShieldCheck")
    folder_id = kwargs.get("folder_id", "")
    if not folder_id:
        return ui.Text("Укажите folder_id для аудита через чат: audit_content_health.", variant="body")
    result = await hs.fn_audit_content_health(ctx, AuditContentParams(folder_id=folder_id))
    if not result.success:
        return ui.Alert(type="error", message=result.error or "Could not run audit")
    findings = (result.data or {}).get("findings", [])
    rows = [{"finding_type": f["finding_type"], "item_name": f["item_name"], "detail": f["detail"]} for f in findings]
    columns = [
        ui.DataColumn(key="finding_type", label="Type"),
        ui.DataColumn(key="item_name", label="Item"),
        ui.DataColumn(key="detail", label="Detail"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Content audit", level=2),
        _table_or_empty(rows, columns, "No issues found", "CheckCircle"),
    ])
