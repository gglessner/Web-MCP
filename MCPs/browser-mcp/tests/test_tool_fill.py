import pytest

from browser_mcp.tools import BrowserSession


class _FakeCDP:
    def __init__(self, found_id=7):
        self._found = found_id
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        if method == "DOM.getDocument":
            return {"root": {"nodeId": 1}}
        if method == "DOM.querySelector":
            return {"nodeId": self._found}
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
async def test_fill_focuses_and_inserts_text(tmp_path):
    cdp = _FakeCDP()
    sess = _sess(cdp, tmp_path)
    result = await sess.fill("input[name=q]", "payload")
    assert result["ok"] is True
    methods = [m for m, _ in cdp.sent]
    assert "DOM.focus" in methods
    assert "Input.insertText" in methods
    insert = next(p for m, p in cdp.sent if m == "Input.insertText")
    assert insert == {"text": "payload"}


@pytest.mark.asyncio
async def test_fill_not_found(tmp_path):
    sess = _sess(_FakeCDP(found_id=0), tmp_path)
    result = await sess.fill("#nope", "x")
    assert result["error"]["code"] == "BAD_INPUT"
