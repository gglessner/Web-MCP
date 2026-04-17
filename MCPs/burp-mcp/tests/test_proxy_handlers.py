import httpx
import pytest
import respx

from burp_mcp.tool_handlers import handle


@pytest.mark.asyncio
async def test_burp_proxy_history():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.get("/proxy/history").mock(
            return_value=httpx.Response(200, json={
                "ok": True, "data": {"entries": [{"id": 0}], "next_cursor": None, "total": 1}
            })
        )
        result = await handle(
            "burp_proxy_history", {"host": "x.com", "limit": 10},
            bridge_url="http://127.0.0.1:8775",
        )
        assert result["ok"] is True
        assert result["data"]["total"] == 1


@pytest.mark.asyncio
async def test_burp_proxy_request_bad_id():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.get("/proxy/request/999").mock(
            return_value=httpx.Response(404, json={
                "ok": False, "error": {"code": "BAD_INPUT", "message": "out of range"}
            })
        )
        result = await handle(
            "burp_proxy_request", {"id": 999},
            bridge_url="http://127.0.0.1:8775",
        )
        assert result["ok"] is False
        assert result["error"]["code"] == "BAD_INPUT"


@pytest.mark.asyncio
async def test_burp_unreachable():
    result = await handle(
        "burp_proxy_history", {},
        bridge_url="http://127.0.0.1:59998",
    )
    assert result["ok"] is False
    assert result["error"]["code"] == "BURP_UNAVAILABLE"
