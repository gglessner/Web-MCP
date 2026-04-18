import pytest

from browser_mcp.tools import BrowserSession
from common.cdp import CDPError


class _FakeCDP:
    def __init__(self, *, raise_cdp: bool = False):
        self._raise = raise_cdp
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        if method == "Network.getResponseBody":
            if self._raise:
                raise CDPError(code=-32000, message="No data found for resource")
            return {"body": "{\"q\":\"hi\"}", "base64Encoded": False}
        return {}


def _sess(cdp, tmp_path):
    s = BrowserSession(chrome_candidates=[], cdp_port=9222, default_proxy=None,
                       user_data_dir_root=str(tmp_path))
    s._cdp = cdp
    s._proc = type("P", (), {"poll": lambda self: None})()
    return s


@pytest.mark.asyncio
async def test_get_response_body_returns_body(tmp_path):
    sess = _sess(_FakeCDP(), tmp_path)
    result = await sess.get_response_body("REQ-1")
    assert result["ok"] is True
    assert result["data"]["body"] == "{\"q\":\"hi\"}"
    assert result["data"]["base64_encoded"] is False
    assert result["data"]["length"] == len("{\"q\":\"hi\"}")


@pytest.mark.asyncio
async def test_get_response_body_evicted_maps_to_bad_input(tmp_path):
    sess = _sess(_FakeCDP(raise_cdp=True), tmp_path)
    result = await sess.get_response_body("REQ-1")
    assert result["ok"] is False
    assert result["error"]["code"] == "BAD_INPUT"
    assert "page" in result["error"]["detail"]["hint"]


@pytest.mark.asyncio
async def test_get_response_body_base64_length_is_decoded_bytes(tmp_path):
    import base64 as _b64

    class _B64CDP:
        async def send(self, method, params=None):
            return {"body": _b64.b64encode(b"\x00\x01\x02\x03").decode(),
                    "base64Encoded": True}

    sess = _sess(_B64CDP(), tmp_path)
    result = await sess.get_response_body("REQ-2")
    assert result["ok"] is True
    assert result["data"]["base64_encoded"] is True
    assert result["data"]["length"] == 4  # decoded bytes, not encoded chars (8)
