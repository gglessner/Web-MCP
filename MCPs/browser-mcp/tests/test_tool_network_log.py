import pytest

from browser_mcp.tools import BrowserSession


def _sess(tmp_path):
    s = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    s._cdp = object()
    s._proc = type("P", (), {"poll": lambda self: None})()
    return s


def test_network_log_returns_entries_since_seq(tmp_path):
    sess = _sess(tmp_path)
    for i in range(5):
        sess._on_event("Network.requestWillBeSent", {"requestId": str(i)})

    result = sess.network_log()
    assert result["ok"] is True
    assert len(result["data"]["events"]) == 5
    assert result["data"]["next_seq"] == 5

    result2 = sess.network_log(since_seq=3)
    assert [e["seq"] for e in result2["data"]["events"]] == [4, 5]


def test_network_log_requires_attached(tmp_path):
    s = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    result = s.network_log()
    assert result["error"]["code"] == "TARGET_NOT_ATTACHED"
