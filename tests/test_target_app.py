import pytest
from flask.testing import FlaskClient

from tests.fixtures.target_app import create_app


@pytest.fixture
def client() -> FlaskClient:
    return create_app().test_client()


def test_echo_returns_query(client: FlaskClient):
    r = client.get("/echo?q=hi")
    assert r.status_code == 200
    assert r.json == {"q": "hi"}


def test_reflected_xss_reflects_q_unsafely(client: FlaskClient):
    r = client.get("/search?q=%3Cscript%3Ealert(1)%3C/script%3E")
    assert r.status_code == 200
    assert "<script>alert(1)</script>" in r.get_data(as_text=True)


def test_login_accepts_hardcoded_creds(client: FlaskClient):
    r = client.post("/login", data={"user": "admin", "pass": "hunter2"})
    assert r.status_code == 200
    assert "welcome, admin" in r.get_data(as_text=True).lower()


def test_login_rejects_bad_creds(client: FlaskClient):
    r = client.post("/login", data={"user": "admin", "pass": "x"})
    assert r.status_code == 401
