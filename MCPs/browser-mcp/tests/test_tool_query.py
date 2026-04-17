import pytest

from browser_mcp.tools import BrowserSession


class _FakeCDP:
    def __init__(self, found_id=None):
        self._found = found_id
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        if method == "DOM.getDocument":
            return {"root": {"nodeId": 1}}
        if method == "DOM.querySelector":
            return {"nodeId": self._found if self._found is not None else 0}
        if method == "DOM.getOuterHTML":
            return {"outerHTML": "<div id='x'>hi</div>"}
        return {}


def _sess_with_cdp(cdp, tmp_path):
    sess = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    sess._cdp = cdp
    sess._proc = type("P", (), {"poll": lambda self: None})()
    return sess


@pytest.mark.asyncio
async def test_query_found(tmp_path):
    sess = _sess_with_cdp(_FakeCDP(found_id=42), tmp_path)
    result = await sess.query("#x")
    assert result["ok"] is True
    assert result["data"]["html"] == "<div id='x'>hi</div>"


@pytest.mark.asyncio
async def test_query_not_found(tmp_path):
    sess = _sess_with_cdp(_FakeCDP(found_id=0), tmp_path)
    result = await sess.query("#nope")
    assert result["ok"] is False
    assert result["error"]["code"] == "BAD_INPUT"
    assert result["error"]["detail"]["selector"] == "#nope"
