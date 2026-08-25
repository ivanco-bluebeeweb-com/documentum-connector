"""Search and content-audit handlers for Documentum Connector."""
from __future__ import annotations

from imperal_sdk import ActionResult

import documentum_client as dc
from app import chat
from handlers_connection import _client_for, _resolve_connection
from handlers_objects import _object_entity
from schemas import (
    AuditContentParams, ContentAudit, ContentAuditFinding, SearchDocumentsParams,
    SearchDqlParams, SearchResults,
)


@chat.function(
    "search_documents",
    action_type="read",
    event="documentum-connector.search_documents",
    data_model=SearchResults,
    description="Free-text search across object names and content in the repository.",
)
async def fn_search_documents(ctx, params: SearchDocumentsParams) -> ActionResult:
    """Free-text search a Documentum repository."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", "/objects", query={"q": params.query, "items-per-page": params.limit})
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    entries = (data or {}).get("entries", []) or (data or {}).get("results", [])
    objects = [_object_entity(e.get("content", e)) for e in entries]
    return ActionResult.success(
        data=SearchResults(objects=objects, total_found=len(objects)).model_dump(),
        summary=f"{len(objects)} result(s) for '{params.query}'.",
    )


@chat.function(
    "search_dql",
    action_type="read",
    event="documentum-connector.search_dql",
    data_model=SearchResults,
    description="Run a raw Documentum Query Language (DQL) SELECT statement for advanced/precise searches.",
)
async def fn_search_dql(ctx, params: SearchDqlParams) -> ActionResult:
    """Run a raw DQL query against a Documentum repository."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", "/objects", query={"dql": params.dql})
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    entries = (data or {}).get("entries", []) or (data or {}).get("results", [])
    objects = [_object_entity(e.get("content", e)) for e in entries]
    return ActionResult.success(
        data=SearchResults(objects=objects, total_found=len(objects)).model_dump(),
        summary=f"{len(objects)} row(s) returned.",
    )


@chat.function(
    "audit_content_health",
    action_type="read",
    event="documentum-connector.audit_content_health",
    data_model=ContentAudit,
    description="Scan a folder and flag content-health issues: long-checked-out documents, empty documents, and very large files.",
)
async def fn_audit_content_health(ctx, params: AuditContentParams) -> ActionResult:
    """Audit a Documentum folder for common content-health issues (one level deep)."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/folders/{params.folder_id}/contents", query={"items-per-page": 200})
    except dc.DocumentumError as exc:
        return ActionResult.error(str(exc))
    entries = (data or {}).get("entries", []) or (data or {}).get("results", [])
    findings: list[ContentAuditFinding] = []
    scanned = 0
    for e in entries:
        obj = _object_entity(e.get("content", e))
        scanned += 1
        if obj.object_type == "dm_document" and obj.size_bytes == 0:
            findings.append(ContentAuditFinding(finding_type="empty_document", item_name=obj.name, detail="Document has zero bytes of content."))
        if obj.size_bytes > 100 * 1024 * 1024:
            findings.append(ContentAuditFinding(finding_type="large_file", item_name=obj.name, detail=f"File is {obj.size_bytes // (1024*1024)} MB -- consider archiving."))
        if obj.checked_out_by:
            findings.append(ContentAuditFinding(finding_type="checked_out", item_name=obj.name, detail=f"Currently checked out by {obj.checked_out_by}."))
    return ActionResult.success(
        data=ContentAudit(folder_id=params.folder_id, items_scanned=scanned, findings=findings).model_dump(),
        summary=f"Scanned {scanned} item(s), {len(findings)} finding(s).",
    )
