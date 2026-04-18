import textwrap
import pytest
from browser_mcp.tools import BrowserSession
from common.engagement import Engagement


@pytest.mark.asyncio
async def test_capture_identity_writes_engagement(tmp_path):
    eng_path = tmp_path / "engagement.toml"
    eng_path.write_text(textwrap.dedent("""
        [scope]
        hosts = ["app.acme.com"]
    """))
    eng = Engagement.load(eng_path)

    sess = BrowserSession(
        chrome_candidates=["x"], cdp_port=0, default_proxy=None,
        user_data_dir_root=str(tmp_path), engagement=eng,
    )
    sess._current_host = "app.acme.com"

    class FakeCDP:
        async def send(self, method, params=None):
            if method == "Network.getAllCookies":
                return {"cookies": [
                    {"name": "sid", "value": "ABC", "domain": "app.acme.com"},
                    {"name": "x", "value": "Y", "domain": "evil.com"},
                ]}
            return {}
    sess._cdp = FakeCDP()
    sess._network_log.append({
        "seq": 1, "method": "Network.requestWillBeSent",
        "params": {"request": {"url": "https://app.acme.com/api",
                               "headers": {"Authorization": "Bearer TOK"}}},
    })

    result = await sess.capture_identity("user1")
    assert result["ok"]
    e2 = Engagement.load(eng_path)
    ident = e2.identity("user1")
    assert ident["cookies"] == [{"name": "sid", "value": "ABC", "domain": "app.acme.com"}]
    assert ident["headers"] == {"Authorization": "Bearer TOK"}


@pytest.mark.asyncio
async def test_apply_identity_sets_cookies(tmp_path):
    eng_path = tmp_path / "engagement.toml"
    eng_path.write_text(textwrap.dedent("""
        [scope]
        hosts = ["app.acme.com"]
        [identities.user1]
        cookies = [{name="sid", value="ABC", domain="app.acme.com"}]
        headers = {}
    """))
    eng = Engagement.load(eng_path)
    sess = BrowserSession(
        chrome_candidates=["x"], cdp_port=0, default_proxy=None,
        user_data_dir_root=str(tmp_path), engagement=eng,
    )
    sent = []
    class FakeCDP:
        async def send(self, method, params=None):
            sent.append((method, params)); return {}
    sess._cdp = FakeCDP()
    r = await sess.apply_identity("user1")
    assert r["ok"]
    assert ("Network.setCookies", {"cookies": [
        {"name": "sid", "value": "ABC", "domain": "app.acme.com"}
    ]}) in sent


@pytest.mark.asyncio
async def test_capture_identity_no_engagement(tmp_path):
    sess = BrowserSession(
        chrome_candidates=["x"], cdp_port=0, default_proxy=None,
        user_data_dir_root=str(tmp_path), engagement=None,
    )
    r = await sess.capture_identity("user1")
    assert r["ok"] is False
    assert r["error"]["code"] == "BAD_INPUT"
