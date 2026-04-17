import asyncio

import pytest

from browser_mcp.tools import BrowserSession


class _FakeCDP:
    def __init__(self, events):
        self._events = events
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        return {"frameId": "F"}


@pytest.mark.asyncio
async def test_navigate_success(monkeypatch, tmp_path):
    sess = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path), navigation_timeout_s=2,
    )
    fake = _FakeCDP(events=[])
    sess._cdp = fake
    sess._proc = type("P", (), {"poll": lambda self: None})()

    # Simulate load event arriving after send
    async def fire_event():
        await asyncio.sleep(0.01)
        await sess._load_events.put(1.0)

    asyncio.create_task(fire_event())
    result = await sess.navigate("https://example.com")
    assert result["ok"] is True
    assert fake.sent[0][0] == "Page.navigate"
    assert fake.sent[0][1] == {"url": "https://example.com"}


@pytest.mark.asyncio
async def test_navigate_timeout(monkeypatch, tmp_path):
    sess = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path), navigation_timeout_s=0,
    )
    sess._cdp = _FakeCDP(events=[])
    sess._proc = type("P", (), {"poll": lambda self: None})()

    result = await sess.navigate("https://example.com")
    assert result["ok"] is False
    assert result["error"]["code"] == "TIMEOUT"


@pytest.mark.asyncio
async def test_navigate_without_attach(tmp_path):
    sess = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    result = await sess.navigate("https://example.com")
    assert result["error"]["code"] == "TARGET_NOT_ATTACHED"
