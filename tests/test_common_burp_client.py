import httpx
import pytest
import respx

from common.burp_client import (
    BurpBadInput,
    BurpClient,
    BurpProRequired,
    BurpUnavailable,
)


@pytest.mark.asyncio
async def test_meta_returns_edition_and_version():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.get("/meta").mock(
            return_value=httpx.Response(
                200,
                json={"ok": True, "data": {
                    "edition": "COMMUNITY_EDITION", "version": "2026.2.4", "bridge_version": "0.1.0"
                }},
            )
        )
        async with BurpClient("http://127.0.0.1:8775") as c:
            meta = await c.meta()
        assert meta["edition"] == "COMMUNITY_EDITION"


@pytest.mark.asyncio
async def test_pro_required_maps_to_exception():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.post("/scanner/scan").mock(
            return_value=httpx.Response(
                503,
                json={"ok": False, "error": {"code": "PRO_REQUIRED", "message": "needs pro"}},
            )
        )
        async with BurpClient("http://127.0.0.1:8775") as c:
            with pytest.raises(BurpProRequired):
                await c.scanner_scan(url="https://t.example", mode="active")


@pytest.mark.asyncio
async def test_connection_refused_maps_to_unavailable():
    async with BurpClient("http://127.0.0.1:59999") as c:
        with pytest.raises(BurpUnavailable):
            await c.meta()


@pytest.mark.asyncio
async def test_bad_input_maps():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.get("/proxy/request/999").mock(
            return_value=httpx.Response(404, json={
                "ok": False, "error": {"code": "BAD_INPUT", "message": "out of range"}
            })
        )
        async with BurpClient("http://127.0.0.1:8775") as c:
            with pytest.raises(BurpBadInput):
                await c.proxy_request(999)
