"""Documentum Connector -- App settings panel."""
from __future__ import annotations

from imperal_sdk import ui

import handlers_connection as h
from app import ext


@ext.panel("documentum_settings", slot="center", title="Documentum settings", icon="Settings", center_overlay=True)
async def documentum_settings(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Text("Ни один Documentum-репозиторий ещё не подключён.", variant="body")
    rows = []
    for c in connections:
        rows.append(ui.Stack(direction="h", gap=2, align="center", children=[
            ui.Text(f"{c.get('label') or c.get('repository_name', '')}", variant="body"),
            ui.Button("Отключить", variant="destructive", on_click=ui.Call("disconnect_documentum", {"connection_id": c.get("id", "")})),
        ]))
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Подключённые репозитории", level=2),
        *rows,
    ])
