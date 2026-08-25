# Documentum Connector -- UI Component Plan

Follows the recorded platform-wide UI standard: every input has an explicit label above it
via a `_field()` wrapper, placeholders are contextual, the sidebar form container is forced
to the full width of the left sidebar with its contents stretched inside it, `ui.Input`/
`ui.Password` use `param_name=` (not `name=`), and setup instructions live ONLY in the
"How do I connect?" overlay -- never duplicated in the sidebar itself.

## Sidebar (`panels.py`, slot="left")
Not connected:
- Ghost button "Как подключить?" -> opens `documentum_connect_help` overlay (all instructions
  live there).
- `ui.Form(action="connect_documentum", submit_label="Подключить")` containing a
  `ui.Stack` (full width, gap=3) with:
  - _field("Название (необязательно)", Input(param_name="label", placeholder="например, Acme Documentum"))
  - _field("Base URL", Input(param_name="base_url", placeholder="https://dctm.acme.com:8080/dctm-rest"))
  - _field("Имя репозитория", Input(param_name="repository_name", placeholder="например, acme_prod"))
  - _field("Имя пользователя", Input(param_name="username", placeholder="ваш логин Documentum"))
  - _field("Пароль", Password(param_name="password", placeholder="ваш пароль Documentum"))

Connected:
- "App settings" secondary button -> `documentum_settings` overlay.
- Quick actions: "Cabinets" -> `documentum_cabinets` overlay, "Content audit" ->
  `documentum_audit` overlay.

## Center overlays (`panels_center.py`)
- `documentum_cabinets`: DataTable of top-level cabinets (name, object_id) for the active
  connection; ui.Empty when none.
- `documentum_audit`: renders `audit_content_health` findings as a DataTable (finding_type,
  item_name, detail); ui.Empty when clean.

## Settings overlay (`panels_settings.py`)
`documentum_settings`: list of connected repositories with a "Отключить" destructive button
per row, calling `disconnect_documentum`.

## Connect-help overlay (`panels_help.py` or inline in `panels.py`)
`documentum_connect_help`: step-by-step -- get your base_url from your Documentum admin,
find the repository (docbase) name, use your normal Documentum login. No duplication of
this content in the sidebar itself.
