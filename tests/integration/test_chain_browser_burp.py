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
from common.burp_client import BurpClient, BurpUnavailable


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
