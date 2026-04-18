import base64

import pytest

from browser_mcp.tools import BrowserSession


class _FakeCDP:
    def __init__(self):
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        if method == "Page.captureScreenshot":
            return {"data": base64.b64encode(b"\x89PNG...fake").decode()}
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
async def test_screenshot_returns_base64_png(tmp_path):
    sess = _sess(_FakeCDP(), tmp_path)
    result = await sess.screenshot(full_page=True)
    assert result["ok"] is True
    assert result["data"]["format"] == "png"
    assert base64.b64decode(result["data"]["base64"]).startswith(b"\x89PNG")


@pytest.mark.asyncio
async def test_screenshot_save_to_writes_file_and_omits_base64(tmp_path):
    evidence_root = tmp_path / "evidence"
    sess = _sess(_FakeCDP(), tmp_path)
    sess._evidence_root = evidence_root
    result = await sess.screenshot(full_page=False, save_to="F-001/shot.png")
    assert result["ok"] is True
    assert "base64" not in result["data"]
    assert result["data"]["saved"].endswith("F-001/shot.png")
    written = evidence_root / "F-001" / "shot.png"
    assert written.exists()
    assert written.read_bytes().startswith(b"\x89PNG")


@pytest.mark.asyncio
async def test_screenshot_save_to_traversal_rejected(tmp_path):
    sess = _sess(_FakeCDP(), tmp_path)
    sess._evidence_root = tmp_path / "evidence"
    result = await sess.screenshot(save_to="../escape.png")
    assert result["ok"] is False
    assert result["error"]["code"] == "BAD_INPUT"
