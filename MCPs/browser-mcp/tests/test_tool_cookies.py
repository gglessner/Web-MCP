import pytest

from browser_mcp.tools import BrowserSession


class _FakeCDP:
    def __init__(self):
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        if method == "Network.getCookies":
            return {"cookies": [{"name": "SID", "value": "abc", "domain": "example.com"}]}
        if method == "Network.setCookie":
            return {"success": True}
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
async def test_cookies_list(tmp_path):
    sess = _sess(_FakeCDP(), tmp_path)
    result = await sess.cookies()
    assert result["ok"] is True
    assert result["data"]["cookies"][0]["name"] == "SID"


@pytest.mark.asyncio
async def test_set_cookie(tmp_path):
    cdp = _FakeCDP()
    sess = _sess(cdp, tmp_path)
    result = await sess.set_cookie(
        name="X", value="1", domain="example.com", path="/", secure=True
    )
    assert result["ok"] is True
    sent = next(p for m, p in cdp.sent if m == "Network.setCookie")
    assert sent["name"] == "X"
    assert sent["domain"] == "example.com"
    assert sent["secure"] is True
