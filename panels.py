"""Documentum Connector -- left sidebar panel.

Follows the recorded UI standard: no decorated cards in the sidebar,
every input has an explicit label via _field(), the form container
stretches to the sidebar's full width with contents stretched inside
it, and no setup instructions are duplicated between the sidebar and
the "How do I connect?" overlay.
"""
from __future__ import annotations

from imperal_sdk import ui

import handlers_connection as h
from app import ext


def _field(label: str, node: ui.UINode) -> ui.UINode:
    return ui.Stack(direction="v", gap=1, align="stretch", children=[
        ui.Text(label, variant="caption"),
        node,
    ])


def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings", variant="secondary", size="sm", icon="Settings", on_click=ui.Call("__panel__documentum_settings"),
    )


@ext.panel("documentum_sidebar", slot="left", title="Documentum")
async def documentum_sidebar(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Stack(direction="v", gap=3, align="stretch", children=[
            ui.Button("Как подключить?", variant="ghost", size="sm", icon="HelpCircle",
                      on_click=ui.Call("__panel__documentum_connect_help")),
            ui.Form(action="connect_documentum", submit_label="Подключить", children=[
                ui.Stack(direction="v", gap=3, align="stretch", children=[
                    _field("Название (необязательно)", ui.Input(param_name="label", placeholder="например, Acme Documentum")),
                    _field("Base URL", ui.Input(param_name="base_url", placeholder="https://dctm.acme.com:8080/dctm-rest")),
                    _field("Имя репозитория", ui.Input(param_name="repository_name", placeholder="например, acme_prod")),
                    _field("Имя пользователя", ui.Input(param_name="username", placeholder="ваш логин Documentum")),
                    _field("Пароль", ui.Password(param_name="password", placeholder="ваш пароль Documentum")),
                ]),
            ]),
        ])
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Text(f"Подключено: {connections[0].get('label') or connections[0].get('repository_name', '')}", variant="body"),
        ui.Button("Cabinets", variant="secondary", size="sm", icon="Folder",
                  on_click=ui.Call("__panel__documentum_cabinets")),
        ui.Button("Content audit", variant="secondary", size="sm", icon="ShieldCheck",
                  on_click=ui.Call("__panel__documentum_audit")),
        _settings_button(),
    ])


@ext.panel("documentum_connect_help", slot="center", title="Как подключить Documentum?", icon="HelpCircle", center_overlay=True)
async def documentum_connect_help(ctx, **kwargs) -> ui.UINode:
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Как подключить Documentum", level=2),
        ui.Text("1. Узнайте базовый URL Documentum REST Services у своего администратора, например https://dctm.acme.com:8080/dctm-rest.", variant="body"),
        ui.Text("2. Узнайте имя нужного репозитория (docbase), например acme_prod.", variant="body"),
        ui.Text("3. Введите логин и пароль пользователя с доступом к REST API этого репозитория.", variant="body"),
        ui.Text("Отдельный API-ключ или OAuth-приложение не нужны — используется обычная Basic-авторизация.", variant="caption"),
    ])
