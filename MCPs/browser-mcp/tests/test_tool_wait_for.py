import pytest

from browser_mcp.tools import BrowserSession


class _FakeCDP:
    def __init__(self, node_ids: list[int], has_box: bool = True):
        self._node_ids = list(node_ids)
        self._has_box = has_box
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        if method == "DOM.getDocument":
            return {"root": {"nodeId": 1}}
        if method == "DOM.querySelector":
            nid = self._node_ids.pop(0) if self._node_ids else 0
            return {"nodeId": nid}
        if method == "DOM.getBoxModel":
            if self._has_box:
                return {"model": {"content": [0, 0, 1, 0, 1, 1, 0, 1]}}
            raise RuntimeError("No box model")
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
async def test_wait_for_attached_eventually(tmp_path):
    sess = _sess(_FakeCDP(node_ids=[0, 0, 42]), tmp_path)
    result = await sess.wait_for("#x", timeout_s=2.0, state="attached")
    assert result["ok"] is True
    assert result["data"]["nodeId"] == 42


@pytest.mark.asyncio
async def test_wait_for_timeout(tmp_path):
    sess = _sess(_FakeCDP(node_ids=[]), tmp_path)
    result = await sess.wait_for("#nope", timeout_s=0.3)
    assert result["ok"] is False
    assert result["error"]["code"] == "TIMEOUT"
    assert result["error"]["detail"]["selector"] == "#nope"


@pytest.mark.asyncio
async def test_wait_for_visible_requires_box_model(tmp_path):
    sess = _sess(_FakeCDP(node_ids=[42, 42], has_box=False), tmp_path)
    result = await sess.wait_for("#x", timeout_s=0.3, state="visible")
    assert result["ok"] is False
    assert result["error"]["code"] == "TIMEOUT"


@pytest.mark.asyncio
async def test_wait_for_requires_attached_session(tmp_path):
    s = BrowserSession(chrome_candidates=[], cdp_port=9222, default_proxy=None,
                       user_data_dir_root=str(tmp_path))
    result = await s.wait_for("#x")
    assert result["error"]["code"] == "TARGET_NOT_ATTACHED"


@pytest.mark.asyncio
async def test_wait_for_zero_timeout_still_probes_once(tmp_path):
    sess = _sess(_FakeCDP(node_ids=[42]), tmp_path)
    result = await sess.wait_for("#x", timeout_s=0, state="attached")
    assert result["ok"] is True
    assert result["data"]["nodeId"] == 42
