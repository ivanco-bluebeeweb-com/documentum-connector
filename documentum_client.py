"""Thin Documentum REST Services client.

Auth model: HTTP Basic Auth over HTTPS -- username+password sent on every
request. No token/ticket to cache or refresh (unlike Box's OAuth or OTCS's
session ticket), so this client is deliberately simpler: build the auth
header once and reuse it.
"""
from __future__ import annotations

import base64
from typing import Any

import httpx


class DocumentumError(RuntimeError):
    """A safe provider-facing error; never includes credentials."""

    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class DocumentumClient:
    """REST client for one Documentum repository."""

    def __init__(self, base_url: str, repository_name: str, username: str, password: str, *, timeout: float = 30.0):
        base = (base_url or "").strip().rstrip("/")
        if not base:
            raise DocumentumError("Base URL is required.")
        if not repository_name:
            raise DocumentumError("Repository name is required.")
        if not username or not password:
            raise DocumentumError("Username and password are required.")
        self.base_url = base
        self.repository_name = repository_name
        self.username = username
        self.password = password
        self.timeout = timeout

    def _repo_url(self, path: str) -> str:
        return f"{self.base_url}/repositories/{self.repository_name}{path}"

    def _auth_header(self) -> dict:
        token = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        return {"Authorization": f"Basic {token}"}

    async def request(self, method: str, path: str, *, query: dict | None = None, json_body: dict | None = None) -> Any:
        """Call a repository-scoped endpoint, e.g. path='/cabinets'."""
        headers = self._auth_header()
        headers["Accept"] = "application/json"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.request(method, self._repo_url(path), params=query, json=json_body, headers=headers)
            except httpx.RequestError as exc:
                raise DocumentumError(f"Could not reach Documentum: {exc}", retryable=True) from exc
        return await self._handle_response(resp)

    async def request_absolute(self, method: str, path: str, *, query: dict | None = None) -> Any:
        """Call a non-repository-scoped endpoint, e.g. path='/repositories'."""
        headers = self._auth_header()
        headers["Accept"] = "application/json"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.request(method, f"{self.base_url}{path}", params=query, headers=headers)
            except httpx.RequestError as exc:
                raise DocumentumError(f"Could not reach Documentum: {exc}", retryable=True) from exc
        return await self._handle_response(resp)

    async def download(self, object_id: str) -> bytes:
        """Download an object's primary content bytes."""
        headers = self._auth_header()
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                resp = await client.get(self._repo_url(f"/objects/{object_id}/content"), headers=headers)
            except httpx.RequestError as exc:
                raise DocumentumError(f"Could not reach Documentum: {exc}", retryable=True) from exc
        if resp.status_code >= 400:
            await self._handle_response(resp)
        return resp.content

    async def upload(self, filename: str, parent_folder_id: str, content: bytes) -> dict:
        """Create a new document (sysobject) with the given file as primary content."""
        headers = self._auth_header()
        import json as _json
        properties = {"object_name": filename, "r_object_type": "dm_document"}
        files = {
            "properties": (None, _json.dumps(properties), "application/json"),
            "content": (filename, content, "application/octet-stream"),
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(
                    self._repo_url(f"/folders/{parent_folder_id}/documents"),
                    headers=headers, files=files,
                )
            except httpx.RequestError as exc:
                raise DocumentumError(f"Could not reach Documentum upload service: {exc}", retryable=True) from exc
        return await self._handle_response(resp)

    async def upload_version(self, object_id: str, filename: str, content: bytes) -> dict:
        """Checkin a new version of an existing document."""
        headers = self._auth_header()
        import json as _json
        files = {
            "properties": (None, _json.dumps({"object_name": filename}), "application/json"),
            "content": (filename, content, "application/octet-stream"),
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(
                    self._repo_url(f"/objects/{object_id}/versions"),
                    headers=headers, files=files,
                )
            except httpx.RequestError as exc:
                raise DocumentumError(f"Could not reach Documentum upload service: {exc}", retryable=True) from exc
        return await self._handle_response(resp)

    async def _handle_response(self, resp: httpx.Response) -> Any:
        if resp.status_code == 401:
            raise DocumentumError("Documentum rejected the username/password for this repository.")
        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After", "a few")
            raise DocumentumError(f"Rate limited by Documentum. Retry after {retry_after}s.", retryable=True)
        if resp.status_code >= 400:
            try:
                body = resp.json()
                detail = body.get("errors", [{}])[0].get("message") or body.get("message") or resp.text[:300]
            except Exception:  # noqa: BLE001
                detail = resp.text[:300]
            raise DocumentumError(f"Documentum error {resp.status_code}: {detail}")
        if resp.status_code == 204 or not resp.content:
            return {}
        try:
            return resp.json()
        except Exception:  # noqa: BLE001
            return {}
