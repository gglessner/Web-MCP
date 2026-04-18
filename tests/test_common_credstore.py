import base64
import textwrap
import pytest
from common.engagement import Engagement
from common.credstore import CredStore, UnknownPlaceholder


def make(tmp_path):
    p = tmp_path / "engagement.toml"
    p.write_text(textwrap.dedent("""
        [credentials.user1]
        username = "alice@acme.com"
        password = "p@ss/w0rd"
        [identities.user1]
        cookies = [{name="sid", value="SESSIONABC", domain="x"}]
        headers = {Authorization = "Bearer TOKEN123"}
    """))
    return CredStore(Engagement.load(p))


def test_expand_string_and_nested(tmp_path):
    cs = make(tmp_path)
    assert cs.expand("u={{CRED:user1.username}}") == "u=alice@acme.com"
    out = cs.expand({"a": ["{{CRED:user1.password}}", 1], "b": {"c": "{{CRED:user1.username}}"}})
    assert out == {"a": ["p@ss/w0rd", 1], "b": {"c": "alice@acme.com"}}


def test_expand_unknown_raises(tmp_path):
    cs = make(tmp_path)
    with pytest.raises(UnknownPlaceholder):
        cs.expand("{{CRED:ghost.password}}")


def test_expand_raw_base64_roundtrip(tmp_path):
    cs = make(tmp_path)
    raw = base64.b64encode(b"POST / HTTP/1.1\r\npass={{CRED:user1.password}}\r\n").decode()
    out = cs.expand({"raw_base64": raw})
    decoded = base64.b64decode(out["raw_base64"])
    assert b"pass=p@ss/w0rd" in decoded


def test_filter_redacts_cred_and_identity(tmp_path):
    cs = make(tmp_path)
    out = cs.filter({"body": "pw=p@ss/w0rd sid=SESSIONABC tok=Bearer TOKEN123"})
    assert "p@ss/w0rd" not in out["body"]
    assert "SESSIONABC" not in out["body"]
    assert "TOKEN123" not in out["body"]
    assert "[REDACTED:CRED:user1.password]" in out["body"]
    assert "[REDACTED:IDENT:user1.cookie]" in out["body"]
    assert "[REDACTED:IDENT:user1.header]" in out["body"]


def test_no_engagement_is_noop():
    cs = CredStore(None)
    assert cs.expand({"x": "{{CRED:a.b}}"}) == {"x": "{{CRED:a.b}}"}
    assert cs.filter({"x": "secret"}) == {"x": "secret"}
