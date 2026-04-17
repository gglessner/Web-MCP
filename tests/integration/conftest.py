"""Integration test fixtures: run the Flask fixture as a live server in a thread."""
from __future__ import annotations

import threading
import time
from collections.abc import Iterator

import httpx
import pytest
from werkzeug.serving import make_server

from tests.fixtures.target_app import create_app


@pytest.fixture(scope="session")
def live_target() -> Iterator[str]:
    app = create_app()
    server = make_server("127.0.0.1", 5055, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    for _ in range(50):
        try:
            httpx.get("http://127.0.0.1:5055/echo?q=1", timeout=0.5)
            break
        except Exception:
            time.sleep(0.1)
    else:
        pytest.fail("fixture target did not start")
    yield "http://127.0.0.1:5055"
    server.shutdown()
    thread.join(timeout=2)
