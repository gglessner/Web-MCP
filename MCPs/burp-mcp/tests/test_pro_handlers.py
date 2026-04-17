import base64

import httpx
import pytest
import respx

from burp_mcp.tool_handlers import handle


@pytest.mark.asyncio
async def test_scanner_scan_on_community_returns_pro_required():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.post("/scanner/scan").mock(
            return_value=httpx.Response(503, json={
                "ok": False, "error": {"code": "PRO_REQUIRED", "message": "needs pro"}
            })
        )
        result = await handle(
            "burp_scanner_scan", {"url": "https://x.com"},
            bridge_url="http://127.0.0.1:8775",
        )
        assert result["error"]["code"] == "PRO_REQUIRED"


@pytest.mark.asyncio
async def test_scanner_issues_on_pro():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.get("/scanner/issues").mock(
            return_value=httpx.Response(200, json={
                "ok": True, "data": {"issues": [{"id": 0, "name": "Sec"}], "total": 1}
            })
        )
        result = await handle(
            "burp_scanner_issues", {}, bridge_url="http://127.0.0.1:8775",
        )
        assert result["data"]["total"] == 1


@pytest.mark.asyncio
async def test_intruder_launch_on_community():
    raw = base64.b64encode(b"GET /").decode()
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.post("/intruder/launch").mock(
            return_value=httpx.Response(503, json={
                "ok": False, "error": {"code": "PRO_REQUIRED", "message": "needs pro"}
            })
        )
        result = await handle(
            "burp_intruder_launch",
            {"raw_base64": raw, "host": "x.com", "port": 443},
            bridge_url="http://127.0.0.1:8775",
        )
        assert result["error"]["code"] == "PRO_REQUIRED"


@pytest.mark.asyncio
async def test_match_replace_get_and_set():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.get("/match-replace").mock(
            return_value=httpx.Response(200, json={
                "ok": True, "data": {"rules": []}
            })
        )
        mock.post("/match-replace").mock(
            return_value=httpx.Response(200, json={
                "ok": True, "data": {"applied": True}
            })
        )
        g = await handle("burp_match_replace_get", {}, bridge_url="http://127.0.0.1:8775")
        assert g["data"]["rules"] == []
        s = await handle(
            "burp_match_replace_set",
            {"rules": [{"enabled": True, "type": "request_header",
                        "match": "X-Test: old", "replace": "X-Test: new"}]},
            bridge_url="http://127.0.0.1:8775",
        )
        assert s["data"]["applied"] is True
