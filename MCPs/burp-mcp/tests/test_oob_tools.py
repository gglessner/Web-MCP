import pytest
from burp_mcp.tool_handlers import handle


class FakeOOB:
    def get_payload(self):
        return {"domain": "abc.oast.fun", "url": "http://abc.oast.fun/"}
    def poll(self, since_id=0):
        return [{"id": 1, "protocol": "dns", "remote_addr": "1.2.3.4",
                 "timestamp": "t", "raw_request": ""}]


@pytest.mark.asyncio
async def test_oob_get_payload_and_poll():
    oob = FakeOOB()
    r1 = await handle("oob_get_payload", {}, bridge_url="http://x", oob=oob)
    assert r1["ok"] and r1["data"]["domain"] == "abc.oast.fun"
    r2 = await handle("oob_poll", {"since_id": 0}, bridge_url="http://x", oob=oob)
    assert r2["ok"] and r2["data"][0]["protocol"] == "dns"


@pytest.mark.asyncio
async def test_oob_not_configured():
    r = await handle("oob_get_payload", {}, bridge_url="http://x", oob=None)
    assert r["ok"] is False
    assert r["error"]["code"] == "INTERNAL"
