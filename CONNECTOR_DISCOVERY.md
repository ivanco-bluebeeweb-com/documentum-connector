# Documentum Connector -- Discovery

## Product
OpenText (formerly EMC) Documentum Content Server -- enterprise ECM/repository platform.
Modern integration surface: **Documentum REST Services** (D2-REST / Documentum REST),
base path typically `https://{host}:{port}/dctm-rest/repositories/{repository_name}`.

## Auth model
HTTP Basic Auth over HTTPS (Documentum REST's baseline auth) -- username + password sent
on every request via the `Authorization: Basic ...` header. No separate token/ticket concept
at this layer (unlike OTCS's ticket auth); some tenants front it with OAuth2, but Basic Auth
against the repository is the universal baseline every Content Server exposes.

Stored per connection: `base_url`, `repository_name`, `username`, `password`.

## Core resources
- **Repositories** -- `GET /dctm-rest/repositories` lists repositories visible to the user;
  every other call is scoped to one repository in the URL path.
- **Cabinets** -- top-level containers (Documentum's root folder concept), effectively
  folders with `r_object_type = cabinet`. `GET /repositories/{repo}/cabinets`.
- **Folders & sysobjects** -- the universal object model: every folder/document is a
  "sysobject" identified by `r_object_id` (a 16-char hex id, Documentum's classic ID format).
  `GET /repositories/{repo}/folders/{id}` (folder metadata + `/contents` for children),
  `GET /repositories/{repo}/objects/{id}` (any sysobject by id),
  `POST /repositories/{repo}/folders` (create folder), `PUT .../objects/{id}` (rename/move),
  `DELETE .../objects/{id}` (delete).
- **Document content** -- `GET /repositories/{repo}/objects/{id}/content` (download, primary
  content), `POST /repositories/{repo}/objects` multipart (create document with file),
  `PUT /repositories/{repo}/objects/{id}/versions?version-label=CURRENT` (checkin new version).
- **Versions** -- `GET /repositories/{repo}/objects/{id}/versions` lists the version tree
  (Documentum's `i_chronicle_id`-linked version history); `POST .../versions` with
  `checkout`/`checkin` semantics is how Documentum enforces edit locking (checkout locks
  the object to one user; checkin releases and bumps the version).
- **Permissions (ACLs)** -- `GET /repositories/{repo}/objects/{id}/permissions` reads the
  object's ACL entries (accessor name + permission level: NONE/BROWSE/READ/RELATE/VERSION/
  WRITE/DELETE); `POST` adds an accessor grant.
- **Lifecycles** -- Documentum's distinguishing ECM feature: sysobjects can be attached to a
  named Lifecycle (a state machine, e.g. Draft -> Review -> Approved -> Obsolete).
  `GET /repositories/{repo}/objects/{id}/lifecycle` reads current state;
  `POST .../lifecycle/promote` / `.../demote` moves the object forward/back a state --
  this is the killer feature to expose as first-class actions (no other portfolio ECM app
  has this concept -- Box/SharePoint/OTCS use flat metadata, not state machines).
- **Search (DQL)** -- Documentum Query Language, a SQL-like language over the repository
  (`SELECT r_object_id, object_name FROM dm_document WHERE ...`).
  `POST /repositories/{repo}/dql` executes an ad-hoc DQL query -- exposed as `search_dql` for
  power users, alongside a friendlier `search_documents` (free-text, no DQL knowledge needed).

## Value-add
`audit_content_health`: scan a cabinet/folder one level deep and flag zero-byte documents,
documents still checked out by someone (locked, `r_lock_owner` set) for longer than a
configurable threshold, and documents with no lifecycle attached where the repository
otherwise expects one -- a genuinely Documentum-specific governance signal.
