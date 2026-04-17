import pytest

from browser_mcp.tools import BrowserSession


class _FakeCDP:
    def __init__(self):
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        if method == "DOM.getDocument":
            return {"root": {"nodeId": 1, "nodeName": "#document"}}
        if method == "Accessibility.getFullAXTree":
            return {"nodes": [{"role": {"value": "WebArea"}}]}
        return {}


@pytest.mark.asyncio
async def test_snapshot_returns_dom_and_ax(monkeypatch, tmp_path):
    sess = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    sess._cdp = _FakeCDP()
    sess._proc = type("P", (), {"poll": lambda self: None})()
    result = await sess.snapshot()
    assert result["ok"] is True
    assert result["data"]["dom"]["root"]["nodeName"] == "#document"
    assert result["data"]["accessibility"]["nodes"][0]["role"]["value"] == "WebArea"


@pytest.mark.asyncio
async def test_snapshot_requires_attachment(tmp_path):
    sess = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    result = await sess.snapshot()
    assert result["error"]["code"] == "TARGET_NOT_ATTACHED"
