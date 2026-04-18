"""Chain test: browser drives through Burp (user-launched) → fixture target.

Preconditions (documented in README, enforced via a liveness check):
1. Burp Suite is running with the bridge extension loaded.
2. `curl http://127.0.0.1:8775/meta` succeeds.
3. Burp proxy is listening on 127.0.0.1:8080.
"""
from __future__ import annotations

import shutil
import tempfile

import httpx
import pytest

from browser_mcp.tools import BrowserSession
from common.burp_client import BurpClient


pytestmark = pytest.mark.integration


def _chrome_available() -> bool:
    return any(shutil.which(n) for n in ("chromium", "chromium-browser", "google-chrome", "chrome"))


def _bridge_available() -> bool:
    try:
        httpx.get("http://127.0.0.1:8775/meta", timeout=0.5)
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _chrome_available(), reason="no Chrome binary on PATH")
@pytest.mark.skipif(not _bridge_available(),
                    reason="burp-mcp-bridge not responding on 127.0.0.1:8775 — launch Burp + load extension")
@pytest.mark.asyncio
async def test_browser_through_burp_to_fixture(live_target: str):
    with tempfile.TemporaryDirectory() as udd:
        sess = BrowserSession(
            chrome_candidates=["chromium", "chromium-browser", "google-chrome", "chrome"],
            cdp_port=9222,
            default_proxy="127.0.0.1:8080",
            user_data_dir_root=udd,
            navigation_timeout_s=15,
        )
        try:
            assert (await sess.launch(headless=True))["ok"]
            marker = "xss-probe-9c2f"
            assert (await sess.navigate(f"{live_target}/search?q={marker}"))["ok"]
        finally:
            await sess.close()

        async with BurpClient("http://127.0.0.1:8775") as c:
            history = await c.proxy_history(contains=marker, limit=20)
        entries = history.get("entries", [])
        assert any(marker in (e.get("url") or "") for e in entries), \
            f"probe marker not found in proxy history; entries={entries}"


@pytest.mark.skipif(not _bridge_available(),
                    reason="burp-mcp-bridge not responding on 127.0.0.1:8775")
@pytest.mark.asyncio
async def test_burp_http_send_against_fixture(live_target: str, tmp_path):
    import base64
    from burp_mcp.tool_handlers import handle

    raw = (b"GET /echo?q=chain-probe HTTP/1.1\r\n"
           b"Host: 127.0.0.1:5055\r\nConnection: close\r\n\r\n")
    result = await handle(
        "burp_http_send",
        {"raw_base64": base64.b64encode(raw).decode(),
         "host": "127.0.0.1", "port": 5055, "secure": False},
        bridge_url="http://127.0.0.1:8775",
        evidence_root=tmp_path / "evidence",
    )
    assert result["ok"] is True, result
    assert result["data"]["status"] == 200
    assert "chain-probe" in result["data"]["body_preview"]
