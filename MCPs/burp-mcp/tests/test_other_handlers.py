import base64

import httpx
import pytest
import respx

from burp_mcp.tool_handlers import handle


@pytest.mark.asyncio
async def test_repeater_send():
    raw = base64.b64encode(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n").decode()
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.post("/repeater/send").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"tab": "t"}})
        )
        result = await handle(
            "burp_repeater_send",
            {"raw_base64": raw, "host": "x.com", "port": 443},
            bridge_url="http://127.0.0.1:8775",
        )
        assert result["ok"] is True
        assert result["data"]["tab"] == "t"


@pytest.mark.asyncio
async def test_scope_modify():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.post("/scope").mock(
            return_value=httpx.Response(200, json={
                "ok": True, "data": {"added": ["https://x.com"], "removed": []}
            })
        )
        result = await handle(
            "burp_scope_modify",
            {"add": ["https://x.com"]},
            bridge_url="http://127.0.0.1:8775",
        )
        assert result["data"]["added"] == ["https://x.com"]


@pytest.mark.asyncio
async def test_sitemap():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.get("/sitemap").mock(
            return_value=httpx.Response(200, json={
                "ok": True, "data": {"entries": [{"id": 0, "url": "https://x.com/"}],
                                     "next_cursor": None, "total": 1}
            })
        )
        result = await handle(
            "burp_sitemap", {"prefix": "https://x.com"},
            bridge_url="http://127.0.0.1:8775",
        )
        assert result["data"]["total"] == 1
