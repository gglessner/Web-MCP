"""Real Chrome + real fixture target; requires chromium on PATH."""
from __future__ import annotations

import shutil
import tempfile

import pytest

from browser_mcp.tools import BrowserSession


pytestmark = pytest.mark.integration


def _chrome_available() -> bool:
    return any(shutil.which(n) for n in ("chromium", "chromium-browser", "google-chrome", "chrome"))


@pytest.mark.skipif(not _chrome_available(), reason="no Chrome binary on PATH")
@pytest.mark.asyncio
async def test_launch_navigate_snapshot(live_target: str):
    with tempfile.TemporaryDirectory() as udd:
        sess = BrowserSession(
            chrome_candidates=["chromium", "chromium-browser", "google-chrome", "chrome"],
            cdp_port=9222,
            default_proxy=None,
            user_data_dir_root=udd,
            navigation_timeout_s=15,
        )
        try:
            r_launch = await sess.launch(headless=True, proxy=None)
            assert r_launch["ok"] is True, r_launch
            r_nav = await sess.navigate(f"{live_target}/search?q=<script>alert(1)</script>")
            assert r_nav["ok"] is True, r_nav
            r_snap = await sess.snapshot()
            assert r_snap["ok"] is True
            import json as _j
            blob = _j.dumps(r_snap["data"])
            assert "script" in blob.lower()
        finally:
            await sess.close()
