import pytest

from browser_mcp.tools import BrowserSession


class _FakeCDP:
    def __init__(self, response):
        self._resp = response
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        return self._resp


def _sess(cdp, tmp_path):
    s = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    s._cdp = cdp
    s._proc = type("P", (), {"poll": lambda self: None})()
    return s


@pytest.mark.asyncio
async def test_eval_returns_value(tmp_path):
    cdp = _FakeCDP({"result": {"type": "number", "value": 42}})
    sess = _sess(cdp, tmp_path)
    result = await sess.eval_js("1+41")
    assert result["ok"] is True
    assert result["data"]["value"] == 42
    assert result["data"]["exception"] is None


@pytest.mark.asyncio
async def test_eval_reports_exception(tmp_path):
    cdp = _FakeCDP(
        {
            "result": {"type": "object", "subtype": "error"},
            "exceptionDetails": {"text": "Uncaught ReferenceError: x is not defined"},
        }
    )
    sess = _sess(cdp, tmp_path)
    result = await sess.eval_js("x")
    assert result["ok"] is True
    assert result["data"]["exception"] is not None
    assert "ReferenceError" in result["data"]["exception"]
