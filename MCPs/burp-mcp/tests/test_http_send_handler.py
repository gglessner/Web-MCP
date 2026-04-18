import base64
from pathlib import Path

import httpx
import pytest
import respx

from burp_mcp.tool_handlers import handle


BRIDGE = "http://127.0.0.1:8775"


def _bridge_response(body: bytes = b"<html>hello world</html>", status: int = 200):
    return httpx.Response(200, json={
        "ok": True, "data": {
            "status": status,
            "headers": [{"name": "Content-Type", "value": "text/html"}],
            "body_base64": base64.b64encode(body).decode(),
            "body_len": len(body),
            "request_base64": base64.b64encode(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n").decode(),
            "time_ms": 12,
        }
    })


@pytest.mark.asyncio
async def test_http_send_preview_truncates(tmp_path: Path):
    async with respx.mock(base_url=BRIDGE) as mock:
        mock.post("/http/send").mock(return_value=_bridge_response(body=b"A" * 9000))
        result = await handle("burp_http_send",
            {"raw_base64": "R0VUIC8=", "host": "x", "port": 80,
             "secure": False, "preview_bytes": 100},
            bridge_url=BRIDGE, evidence_root=tmp_path / "evidence")
    assert result["ok"] is True
    assert result["data"]["status"] == 200
    assert len(result["data"]["body_preview"]) == 100
    assert result["data"]["body_len"] == 9000
    assert "body_base64" not in result["data"]


@pytest.mark.asyncio
async def test_http_send_include_body(tmp_path: Path):
    async with respx.mock(base_url=BRIDGE) as mock:
        mock.post("/http/send").mock(return_value=_bridge_response())
        result = await handle("burp_http_send",
            {"raw_base64": "R0VUIC8=", "host": "x", "port": 80, "include_body": True},
            bridge_url=BRIDGE, evidence_root=tmp_path / "evidence")
    assert "body_base64" in result["data"]


@pytest.mark.asyncio
async def test_http_send_save_to_writes_two_files(tmp_path: Path):
    root = tmp_path / "evidence"
    async with respx.mock(base_url=BRIDGE) as mock:
        mock.post("/http/send").mock(return_value=_bridge_response())
        result = await handle("burp_http_send",
            {"raw_base64": "R0VUIC8=", "host": "x", "port": 80,
             "save_to": "F-001/probe"},
            bridge_url=BRIDGE, evidence_root=root)
    assert result["ok"] is True
    assert (root / "F-001" / "probe.request.http").exists()
    assert (root / "F-001" / "probe.response.http").exists()
    assert result["data"]["saved"]["request"].endswith("F-001/probe.request.http")


@pytest.mark.asyncio
async def test_http_send_save_to_traversal_rejected(tmp_path: Path):
    async with respx.mock(base_url=BRIDGE) as mock:
        mock.post("/http/send").mock(return_value=_bridge_response())
        result = await handle("burp_http_send",
            {"raw_base64": "R0VUIC8=", "host": "x", "port": 80, "save_to": "../escape"},
            bridge_url=BRIDGE, evidence_root=tmp_path / "evidence")
    assert result["ok"] is False
    assert result["error"]["code"] == "BAD_INPUT"
