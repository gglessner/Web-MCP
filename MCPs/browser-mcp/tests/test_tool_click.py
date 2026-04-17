import pytest

from browser_mcp.tools import BrowserSession


class _FakeCDP:
    def __init__(self, found_id=42, box=None):
        self._found = found_id
        self._box = box or {"model": {"content": [10, 20, 30, 20, 30, 40, 10, 40]}}
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        if method == "DOM.getDocument":
            return {"root": {"nodeId": 1}}
        if method == "DOM.querySelector":
            return {"nodeId": self._found}
        if method == "DOM.getBoxModel":
            return self._box
        if method == "Input.dispatchMouseEvent":
            return {}
        return {}


def _sess(cdp, tmp_path):
    s = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    s._cdp = cdp
    s._proc = type("P", (), {"poll": lambda self: None})()
    return s


@pytest.mark.asyncio
async def test_click_dispatches_mouse_events(tmp_path):
    cdp = _FakeCDP()
    sess = _sess(cdp, tmp_path)
    result = await sess.click("#btn")
    assert result["ok"] is True
    types = [p["type"] for m, p in cdp.sent if m == "Input.dispatchMouseEvent"]
    assert types == ["mousePressed", "mouseReleased"]


@pytest.mark.asyncio
async def test_click_not_found(tmp_path):
    sess = _sess(_FakeCDP(found_id=0), tmp_path)
    result = await sess.click("#nope")
    assert result["error"]["code"] == "BAD_INPUT"
