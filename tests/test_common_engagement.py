import textwrap
import pytest
from common.engagement import Engagement


def write(tmp_path, body):
    p = tmp_path / "engagement.toml"
    p.write_text(textwrap.dedent(body))
    return p


def test_load_absent_returns_none(tmp_path):
    assert Engagement.load(tmp_path / "nope.toml") is None


def test_in_scope_exact_wildcard_cidr(tmp_path):
    p = write(tmp_path, """
        [scope]
        hosts = ["app.acme.com", "*.api.acme.com", "10.20.0.0/16"]
    """)
    e = Engagement.load(p)
    assert e.in_scope("app.acme.com")
    assert e.in_scope("https://app.acme.com/login")
    assert e.in_scope("v2.api.acme.com")
    assert not e.in_scope("api.acme.com")
    assert e.in_scope("10.20.5.1")
    assert not e.in_scope("10.21.0.1")
    assert not e.in_scope("evil.com")


def test_empty_hosts_fail_closed(tmp_path):
    p = write(tmp_path, "[scope]\nhosts = []\n")
    e = Engagement.load(p)
    assert not e.in_scope("anything.com")


def test_credentials_and_identities_accessors(tmp_path):
    p = write(tmp_path, """
        [credentials.user1]
        username = "alice"
        password = "s3cr3t"
        [identities.user1]
        cookies = [{name="sid", value="abc", domain="app.acme.com"}]
        headers = {Authorization = "Bearer xyz"}
    """)
    e = Engagement.load(p)
    assert e.credential("user1", "password") == "s3cr3t"
    assert e.credential("user1", "nope") is None
    ident = e.identity("user1")
    assert ident["cookies"][0]["value"] == "abc"
    assert ident["headers"]["Authorization"] == "Bearer xyz"
    assert e.identity("ghost") is None


def test_info_has_names_but_no_values(tmp_path):
    p = write(tmp_path, """
        [engagement]
        name = "acme"
        [scope]
        hosts = ["app.acme.com"]
        [credentials.user1]
        username = "alice"
        password = "s3cr3t"
        [identities.user1]
        cookies = [{name="sid", value="SESSIONABC", domain="x"}]
        headers = {Authorization = "Bearer TOK"}
        captured_at = "2026-04-18T00:00:00Z"
    """)
    e = Engagement.load(p)
    info = e.info()
    assert info["name"] == "acme"
    assert info["scope_hosts"] == ["app.acme.com"]
    assert info["credentials"] == {"user1": ["password", "username"]}
    assert info["identities"]["user1"]["cookies"] == 1
    assert info["identities"]["user1"]["headers"] == ["Authorization"]
    import json as _json
    blob = _json.dumps(info)
    assert "s3cr3t" not in blob
    assert "SESSIONABC" not in blob
    assert "TOK" not in blob


def test_write_identity_roundtrip(tmp_path):
    p = write(tmp_path, """
        [scope]
        hosts = ["app.acme.com"]
        [credentials.user1]
        username = "alice"
    """)
    e = Engagement.load(p)
    e.write_identity("user1",
        cookies=[{"name": "sid", "value": "NEW", "domain": "app.acme.com"}],
        headers={"Authorization": "Bearer NEW"})
    e2 = Engagement.load(p)
    assert e2.identity("user1")["cookies"][0]["value"] == "NEW"
    assert e2.identity("user1")["headers"]["Authorization"] == "Bearer NEW"
    assert "captured_at" in e2.identity("user1")
    assert e2.credential("user1", "username") == "alice"
