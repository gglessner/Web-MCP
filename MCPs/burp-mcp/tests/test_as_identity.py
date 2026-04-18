import base64
import json
import textwrap
import httpx
import pytest
import respx
from common.engagement import Engagement
from burp_mcp.tool_handlers import handle


@pytest.mark.asyncio
async def test_http_send_as_identity_injects_cookie_and_header(tmp_path):
    p = tmp_path / "engagement.toml"
    p.write_text(textwrap.dedent("""
        [scope]
        hosts = ["app.acme.com"]
        [identities.user1]
        cookies = [{name="sid", value="ABC", domain="app.acme.com"}]
        headers = {Authorization = "Bearer TOK"}
    """))
    eng = Engagement.load(p)

    raw = b"GET /x HTTP/1.1\r\nHost: app.acme.com\r\nCookie: old=1\r\n\r\n"
    captured = {}

    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        def cap(request):
            captured["body"] = request.content
            return httpx.Response(200, json={"ok": True, "data": {
                "status": 200, "time_ms": 1, "headers": [], "body_base64": "",
                "body_len": 0, "request_base64": "",
            }})
        mock.post("/http/send").mock(side_effect=cap)

        r = await handle("burp_http_send",
            {"raw_base64": base64.b64encode(raw).decode(), "host": "app.acme.com",
             "port": 443, "as_identity": "user1"},
            bridge_url="http://127.0.0.1:8775", engagement=eng)
    assert r["ok"], r
    sent = base64.b64decode(json.loads(captured["body"])["raw_base64"])
    assert b"Cookie: sid=ABC" in sent
    assert b"Authorization: Bearer TOK" in sent
    assert b"old=1" not in sent


@pytest.mark.asyncio
async def test_as_identity_unknown_errors():
    r = await handle("burp_http_send",
        {"raw_base64": "AA==", "host": "x", "port": 1, "as_identity": "ghost"},
        bridge_url="http://x", engagement=None)
    assert r["ok"] is False
    assert r["error"]["code"] == "BAD_INPUT"
