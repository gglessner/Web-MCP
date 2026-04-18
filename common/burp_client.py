"""Typed HTTP client for the burp-mcp-bridge extension."""
from __future__ import annotations

from typing import Any

import httpx


class BurpClientError(RuntimeError):
    """Base class for bridge errors."""


class BurpUnavailable(BurpClientError):
    """Bridge/Burp not reachable."""


class BurpProRequired(BurpClientError):
    """Operation requires Burp Suite Professional."""


class BurpBadInput(BurpClientError):
    """Bridge rejected input."""


class BurpUpstreamError(BurpClientError):
    """Bridge returned a non-standard error body."""


def _raise_for_error(resp: httpx.Response) -> dict:
    try:
        payload = resp.json()
    except Exception:
        raise BurpUpstreamError(f"non-JSON response (status={resp.status_code}): {resp.text[:200]}")
    if payload.get("ok") is True:
        return payload.get("data", {})
    err = payload.get("error", {})
    code = err.get("code")
    msg = err.get("message", "unknown error")
    if code == "PRO_REQUIRED":
        raise BurpProRequired(msg)
    if code == "BAD_INPUT":
        raise BurpBadInput(msg)
    raise BurpUpstreamError(f"{code}: {msg}")


class BurpClient:
    def __init__(self, base_url: str, *, timeout: float = 30.0) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "BurpClient":
        self._client = httpx.AsyncClient(base_url=self._base, timeout=self._timeout)
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        assert self._client is not None
        try:
            resp = await self._client.request(method, path, **kwargs)
        except (httpx.ConnectError, httpx.TimeoutException, httpx.TransportError) as e:
            raise BurpUnavailable(
                f"cannot reach bridge at {self._base}: {e} "
                f"— ensure Burp is running with burp-mcp-bridge.jar loaded"
            )
        return _raise_for_error(resp)

    # --- Endpoints ---

    async def meta(self) -> dict:
        return await self._request("GET", "/meta")

    async def proxy_history(
        self,
        *,
        host: str | None = None,
        method: str | None = None,
        status: int | None = None,
        contains: str | None = None,
        cursor: int = 0,
        limit: int = 50,
    ) -> dict:
        params: dict[str, Any] = {"cursor": cursor, "limit": limit}
        if host:
            params["host"] = host
        if method:
            params["method"] = method
        if status is not None:
            params["status"] = status
        if contains:
            params["contains"] = contains
        return await self._request("GET", "/proxy/history", params=params)

    async def proxy_request(self, request_id: int) -> dict:
        return await self._request("GET", f"/proxy/request/{request_id}")

    async def repeater_send(
        self, *, raw_base64: str, host: str, port: int, secure: bool = True, tab_name: str | None = None,
    ) -> dict:
        body = {"raw_base64": raw_base64, "host": host, "port": port, "secure": secure}
        if tab_name:
            body["tab_name"] = tab_name
        return await self._request("POST", "/repeater/send", json=body)

    async def scope_check(self, urls: list[str]) -> dict:
        return await self._request("GET", "/scope", params={"test": ",".join(urls)})

    async def scope_modify(self, *, add: list[str] | None = None, remove: list[str] | None = None) -> dict:
        return await self._request("POST", "/scope", json={"add": add or [], "remove": remove or []})

    async def sitemap(
        self, *, prefix: str | None = None, cursor: int = 0, limit: int = 200
    ) -> dict:
        params: dict[str, Any] = {"cursor": cursor, "limit": limit}
        if prefix:
            params["prefix"] = prefix
        return await self._request("GET", "/sitemap", params=params)

    async def scanner_scan(self, *, url: str, mode: str = "active") -> dict:
        return await self._request("POST", "/scanner/scan", json={"url": url, "mode": mode})

    async def scanner_issues(self) -> dict:
        return await self._request("GET", "/scanner/issues")

    async def intruder_launch(
        self, *, raw_base64: str, host: str, port: int, secure: bool = True, tab_name: str | None = None,
    ) -> dict:
        body = {"raw_base64": raw_base64, "host": host, "port": port, "secure": secure}
        if tab_name:
            body["tab_name"] = tab_name
        return await self._request("POST", "/intruder/launch", json=body)

    async def match_replace_get(self) -> dict:
        return await self._request("GET", "/match-replace")

    async def match_replace_set(self, rules: Any) -> dict:
        return await self._request("POST", "/match-replace", json={"rules": rules})

    async def http_send(
        self, *, raw_base64: str, host: str, port: int,
        secure: bool = True, timeout_ms: int = 30000,
    ) -> dict:
        return await self._request("POST", "/http/send", json={
            "raw_base64": raw_base64, "host": host, "port": port,
            "secure": secure, "timeout_ms": timeout_ms,
        })
