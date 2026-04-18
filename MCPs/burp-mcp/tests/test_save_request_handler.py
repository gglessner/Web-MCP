import base64
from pathlib import Path

import httpx
import pytest
import respx

from burp_mcp.tool_handlers import handle

BRIDGE = "http://127.0.0.1:8775"


@pytest.mark.asyncio
async def test_save_request_writes_two_files(tmp_path: Path):
    root = tmp_path / "evidence"
    async with respx.mock(base_url=BRIDGE) as mock:
        mock.get("/proxy/request/12").mock(return_value=httpx.Response(200, json={
            "ok": True, "data": {
                "id": 12,
                "request": {"raw_base64": base64.b64encode(b"GET / HTTP/1.1\r\n\r\n").decode()},
                "response": {"status": 200,
                             "raw_base64": base64.b64encode(b"HTTP/1.1 200 OK\r\n\r\nhi").decode()},
            }
        }))
        result = await handle("burp_save_request",
            {"id": 12, "save_to": "F-001/baseline"},
            bridge_url=BRIDGE, evidence_root=root)
    assert result["ok"] is True
    assert (root / "F-001" / "baseline.request.http").read_bytes().startswith(b"GET /")
    assert (root / "F-001" / "baseline.response.http").read_bytes().startswith(b"HTTP/1.1")
    assert result["data"]["saved"]["response"].endswith("baseline.response.http")


@pytest.mark.asyncio
async def test_save_request_no_response_writes_request_only(tmp_path: Path):
    root = tmp_path / "evidence"
    async with respx.mock(base_url=BRIDGE) as mock:
        mock.get("/proxy/request/13").mock(return_value=httpx.Response(200, json={
            "ok": True, "data": {
                "id": 13,
                "request": {"raw_base64": base64.b64encode(b"GET / HTTP/1.1\r\n\r\n").decode()},
                "response": None,
            }
        }))
        result = await handle("burp_save_request",
            {"id": 13, "save_to": "F-002/noresp"},
            bridge_url=BRIDGE, evidence_root=root)
    assert result["ok"] is True
    assert (root / "F-002" / "noresp.request.http").read_bytes().startswith(b"GET /")
    assert not (root / "F-002" / "noresp.response.http").exists()
    assert result["data"]["saved"]["response"] is None
