import io
import json
import pytest
from common.oob import OOBReceiver


class FakeProc:
    def __init__(self, lines):
        self.stdout = io.StringIO("\n".join(lines) + "\n")
        self.returncode = None
    def poll(self):
        return None
    def terminate(self):
        pass


def test_parses_payload_and_interactions(monkeypatch):
    lines = [
        json.dumps({"type": "payload", "domain": "abc123.oast.fun"}),
        json.dumps({"type": "interaction", "protocol": "dns",
                    "remote_address": "1.2.3.4", "timestamp": "t1", "raw": "..."}),
        json.dumps({"type": "interaction", "protocol": "http",
                    "remote_address": "5.6.7.8", "timestamp": "t2", "raw": "GET /"}),
    ]
    monkeypatch.setattr("common.oob.OOBReceiver._spawn", lambda self: FakeProc(lines))
    r = OOBReceiver(provider="interactsh")
    p = r.get_payload()
    assert p["domain"] == "abc123.oast.fun"
    assert p["url"] == "http://abc123.oast.fun/"
    inter = r.poll(since_id=0)
    assert len(inter) == 2
    assert inter[0]["protocol"] == "dns" and inter[0]["id"] == 1
    assert inter[1]["protocol"] == "http" and inter[1]["id"] == 2
    assert r.poll(since_id=2) == []


def test_selfhost_not_implemented_yet():
    with pytest.raises(NotImplementedError):
        OOBReceiver(provider="selfhost").get_payload()
