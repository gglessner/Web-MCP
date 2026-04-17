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
