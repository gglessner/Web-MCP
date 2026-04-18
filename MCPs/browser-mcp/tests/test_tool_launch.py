import asyncio
import json
from pathlib import Path
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
async def test_launch_with_ephemeral_port_reads_devtools_file(monkeypatch, tmp_path):
    fake_proc = MagicMock()
    fake_proc.poll.return_value = None

    def fake_launch(argv):
        udd = next(a.split("=", 1)[1] for a in argv if a.startswith("--user-data-dir="))
        (Path(udd) / "DevToolsActivePort").write_text("41555\n/devtools/browser/x\n")
        assert "--remote-debugging-port=0" in argv
        return fake_proc

    monkeypatch.setattr("browser_mcp.tools.launch_chrome", fake_launch)
    monkeypatch.setattr(
        "browser_mcp.tools.resolve_chrome_binary", lambda candidates: "/usr/bin/chromium"
    )

    seen_urls = []

    async def fake_discover(url):
        seen_urls.append(url)
        return [{"type": "page", "webSocketDebuggerUrl": "ws://127.0.0.1:41555/devtools/page/X"}]

    monkeypatch.setattr("browser_mcp.tools.discover_targets", fake_discover)

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
        cdp_port=0,
        default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    result = await sess.launch(headless=True)
    assert result["ok"] is True
    assert result["data"]["cdp_port"] == 41555
    assert seen_urls == ["http://127.0.0.1:41555"]
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
