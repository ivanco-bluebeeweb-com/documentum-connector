"""Pydantic input contracts and SDL result entities for Documentum Connector."""
from __future__ import annotations

from imperal_sdk import sdl
from pydantic import BaseModel, Field


class NoParams(BaseModel):
    pass


class ConnectionRefParams(BaseModel):
    connection_id: str = Field("", description="Optional saved Documentum repository connection ID. Omit to use the first connected repository.")


class ConnectDocumentumParams(BaseModel):
    label: str = Field("", description="Friendly connection label, e.g. 'Acme Documentum'.")
    base_url: str = Field(..., description="Documentum REST Services base URL, e.g. 'https://dctm.acme.com:8080/dctm-rest'.")
    repository_name: str = Field(..., description="Repository (docbase) name, e.g. 'acme_prod'.")
    username: str = Field(..., description="Documentum username with REST access to this repository.")
    password: str = Field(..., description="Documentum password for that username.")


class DisconnectDocumentumParams(ConnectionRefParams):
    connection_id: str = Field(..., description="Saved Documentum connection ID to remove from Imperal.")


class ObjectIdParams(ConnectionRefParams):
    object_id: str = Field(..., description="Documentum object ID (r_object_id), a 16-character hex string.")


class ListCabinetsParams(ConnectionRefParams):
    pass


class ListFolderContentsParams(ObjectIdParams):
    limit: int = Field(100, description="Max child objects to return (1-500).")


class CreateFolderParams(ConnectionRefParams):
    name: str = Field(..., description="New folder name, e.g. 'Q3 Contracts'.")
    parent_id: str = Field(..., description="Parent folder/cabinet object ID to create the folder inside.")


class RenameOrMoveObjectParams(ObjectIdParams):
    name: str = Field("", description="New object name. Leave blank to keep the current name.")
    new_parent_id: str = Field("", description="Destination parent folder object ID to move into. Leave blank to keep in place.")


class DownloadDocumentParams(ObjectIdParams):
    pass


class UploadDocumentParams(ConnectionRefParams):
    name: str = Field(..., description="Document file name, e.g. 'contract.pdf'.")
    parent_folder_id: str = Field(..., description="Folder object ID to upload the document into.")
    content_base64: str = Field(..., description="File content, base64-encoded.")


class UploadVersionParams(ObjectIdParams):
    name: str = Field(..., description="File name for this new version.")
    content_base64: str = Field(..., description="New version's file content, base64-encoded.")


class SearchDocumentsParams(ConnectionRefParams):
    query: str = Field(..., description="Free-text search across object names and content, e.g. 'contract 2026'.")
    limit: int = Field(25, description="Max results to return (1-100).")


class SearchDqlParams(ConnectionRefParams):
    dql: str = Field(..., description="Raw Documentum Query Language (DQL) statement, e.g. \"SELECT r_object_id, object_name FROM dm_document WHERE folder('/Contracts')\".")


class ListVersionsParams(ObjectIdParams):
    pass


class CheckoutParams(ObjectIdParams):
    pass


class CheckinParams(ObjectIdParams):
    keep_checked_out: bool = Field(False, description="If true, keep the document checked out after this checkin (for iterative saves).")


class CancelCheckoutParams(ObjectIdParams):
    pass


class ListPermissionsParams(ObjectIdParams):
    pass


class GrantPermissionParams(ObjectIdParams):
    accessor_name: str = Field(..., description="User or group name to grant access to.")
    permission_level: str = Field(..., description="Permission level: NONE, BROWSE, READ, RELATE, VERSION, WRITE, or DELETE.")


class RevokePermissionParams(ObjectIdParams):
    accessor_name: str = Field(..., description="User or group name to revoke access from.")


class GetLifecycleStateParams(ObjectIdParams):
    pass


class PromoteLifecycleParams(ObjectIdParams):
    pass


class DemoteLifecycleParams(ObjectIdParams):
    pass


class AuditContentParams(ConnectionRefParams):
    folder_id: str = Field(..., description="Folder or cabinet object ID to audit.")
    checkout_days: int = Field(30, description="Flag documents checked out longer than this many days.")


# ---- SDL result entities ----

class DeleteResult(sdl.Entity):
    id: str = ""
    title: str = ""
    deleted: bool
    item_id: str = ""


class DocumentumConnection(sdl.Entity):
    id: str = ""
    title: str = ""
    connection_id: str
    label: str
    repository_name: str


class ConnectionList(sdl.Entity):
    id: str = ""
    title: str = ""
    connections: list[DocumentumConnection]


class DocumentumObject(sdl.Entity):
    id: str = ""
    title: str = ""
    object_id: str
    name: str
    object_type: str = ""
    parent_id: str = ""
    size_bytes: int = 0
    modify_date: str = ""
    checked_out_by: str = ""


class ObjectList(sdl.Entity):
    id: str = ""
    title: str = ""
    objects: list[DocumentumObject]


class UploadResult(sdl.Entity):
    id: str = ""
    title: str = ""
    object_id: str
    name: str


class DownloadResult(sdl.Entity):
    id: str = ""
    title: str = ""
    name: str
    content_base64: str
    content_type: str = "application/octet-stream"


class DocumentumVersion(sdl.Entity):
    id: str = ""
    title: str = ""
    version_label: str
    object_id: str
    modify_date: str = ""
    modified_by: str = ""


class VersionList(sdl.Entity):
    id: str = ""
    title: str = ""
    versions: list[DocumentumVersion]


class CheckoutResult(sdl.Entity):
    id: str = ""
    title: str = ""
    object_id: str
    checked_out: bool
    checked_out_by: str = ""


class DocumentumPermission(sdl.Entity):
    id: str = ""
    title: str = ""
    accessor_name: str
    permission_level: str


class PermissionList(sdl.Entity):
    id: str = ""
    title: str = ""
    permissions: list[DocumentumPermission]


class LifecycleState(sdl.Entity):
    id: str = ""
    title: str = ""
    object_id: str
    lifecycle_name: str = ""
    current_state: str = ""


class SearchResults(sdl.Entity):
    id: str = ""
    title: str = ""
    objects: list[DocumentumObject]
    total_found: int = 0


class ContentAuditFinding(sdl.Entity):
    id: str = ""
    title: str = ""
    finding_type: str
    item_name: str
    detail: str


class ContentAudit(sdl.Entity):
    id: str = ""
    title: str = ""
    folder_id: str
    items_scanned: int
    findings: list[ContentAuditFinding]
