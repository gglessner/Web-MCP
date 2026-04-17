import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from browser_mcp.tools import BrowserSession


@pytest.mark.asyncio
async def test_launch_resolves_binary_starts_chrome_and_connects(monkeypatch, tmp_path):
    # Stub the Chrome binary resolution and subprocess
    fake_proc = MagicMock()
    fake_proc.poll.return_value = None
    monkeypatch.setattr("browser_mcp.tools.launch_chrome", lambda argv: fake_proc)
    monkeypatch.setattr(
        "browser_mcp.tools.resolve_chrome_binary", lambda candidates: "/usr/bin/chromium"
    )

    # Stub the DevTools /json endpoint: return one page target
    async def fake_discover(_url):
        return [{"type": "page", "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/page/X"}]

    monkeypatch.setattr("browser_mcp.tools.discover_targets", fake_discover)

    # Stub CDPSession to avoid real websocket
    class FakeSess:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            pass

        async def send(self, method, params=None):
            return {}

    monkeypatch.setattr("browser_mcp.tools.CDPSession", lambda url, on_event=None: FakeSess())

    sess = BrowserSession(
        chrome_candidates=["chromium"],
        cdp_port=9222,
        default_proxy="127.0.0.1:8080",
        user_data_dir_root=str(tmp_path),
    )
    result = await sess.launch(headless=True, proxy=None)
    assert result["ok"] is True
    assert sess.is_attached()
    await sess.close()


@pytest.mark.asyncio
async def test_launch_returns_error_when_chrome_missing(monkeypatch, tmp_path):
    from browser_mcp.chrome_launcher import ChromeNotFoundError

    def raiser(_):
        raise ChromeNotFoundError("no chrome")

    monkeypatch.setattr("browser_mcp.tools.resolve_chrome_binary", raiser)
    sess = BrowserSession(
        chrome_candidates=["nope"],
        cdp_port=9222,
        default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    result = await sess.launch()
    assert result["ok"] is False
    assert result["error"]["code"] == "INTERNAL"
    assert "no chrome" in result["error"]["message"]
