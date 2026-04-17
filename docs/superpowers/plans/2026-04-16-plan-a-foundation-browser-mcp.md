# Plan A — Foundation + browser-mcp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the Web-MCP workspace with shared utilities (`common/`) and a fully working browser-mcp that Claude Code can drive against any target via raw Chrome DevTools Protocol.

**Architecture:** Python 3.13 monorepo at `/home/kali/Web-MCP` with a single venv. `common/` provides config loading, JSON logging, a CDP websocket client, and MCP stdio scaffolding. `browser-mcp` is a stdio MCP server that launches Chrome as a subprocess with `--remote-debugging-port=9222` and drives it via CDP. No Node.js, no Playwright.

**Tech Stack:** Python 3.13, `mcp` SDK, `httpx`, `websockets`, `pytest`, `pytest-asyncio`, `respx` (for later plans), `ruff`. System deps: Chromium/Chrome.

**Spec:** `docs/superpowers/specs/2026-04-16-web-mcp-stack-design.md`

---

### Task 1: Workspace bootstrap

**Files:**
- Create: `/home/kali/Web-MCP/.gitignore`
- Create: `/home/kali/Web-MCP/README.md`
- Create: `/home/kali/Web-MCP/requirements.txt`
- Create: `/home/kali/Web-MCP/pyproject.toml`
- Create: `/home/kali/Web-MCP/config.toml`

- [ ] **Step 1: Initialize git and create directory skeleton**

```bash
cd /home/kali/Web-MCP
git init
mkdir -p common MCPs logs tests/integration tests/fixtures docs/superpowers/plans docs/superpowers/specs
touch common/__init__.py
```

- [ ] **Step 2: Write `.gitignore`**

```gitignore
.venv/
__pycache__/
*.pyc
*.pyo
*.egg-info/
logs/*.log
.pytest_cache/
.ruff_cache/
htmlcov/
.coverage
build/
dist/
# Burp extension build output (committed build/libs/ excluded from source ignores; produced in Plan B)
MCPs/burp-mcp/burp-ext/build/
# Per-tester overrides
config.local.toml
```

- [ ] **Step 3: Write top-level `requirements.txt`**

```
mcp>=1.0.0
httpx>=0.27
websockets>=12
```

- [ ] **Step 4: Write top-level `pyproject.toml`** (workspace root for dev deps / tooling)

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "web-mcp-workspace"
version = "0.1.0"
description = "Web-MCP: four-MCP stack for AI-driven web security auditing"
requires-python = ">=3.13"

[project.optional-dependencies]
dev = [
  "pytest>=8",
  "pytest-asyncio>=0.23",
  "pytest-cov>=5",
  "respx>=0.21",
  "ruff>=0.5",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
markers = [
  "integration: end-to-end tests requiring real Chrome/Burp (opt-in via -m integration)",
]

[tool.ruff]
line-length = 100
target-version = "py313"
```

- [ ] **Step 5: Write `config.toml`** (default config — tester overrides via `config.local.toml`)

```toml
[burp]
bridge_url = "http://127.0.0.1:8775"

[browser]
# Tried in order if absolute path not given
chrome_candidates = ["chromium", "chromium-browser", "google-chrome", "chrome"]
default_proxy = "127.0.0.1:8080"
headless = false
cdp_port = 9222
navigation_timeout_s = 30

[logging]
level = "INFO"
dir = "logs"
```

- [ ] **Step 6: Write minimal `README.md`**

```markdown
# Web-MCP

Four-MCP Python stack for AI-driven web security auditing and PoC validation.
See `docs/superpowers/specs/2026-04-16-web-mcp-stack-design.md` for the full design.

## Quick setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"
```

Claude Code MCP registration: see `claude_config.example.json` (generated in later plans).
```

- [ ] **Step 7: Create venv and install**

Run:
```bash
cd /home/kali/Web-MCP
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e ".[dev]"
```
Expected: install succeeds, `python -c "import mcp, httpx, websockets; print('ok')"` prints `ok`.

- [ ] **Step 8: Commit**

```bash
git add .gitignore README.md requirements.txt pyproject.toml config.toml common/__init__.py docs/
git commit -m "chore: bootstrap Web-MCP workspace (venv, config, skeleton)"
```

---

### Task 2: `common/logging.py` — structured JSON logger

**Files:**
- Create: `common/logging.py`
- Create: `tests/test_common_logging.py`

- [ ] **Step 1: Write the failing test**

`tests/test_common_logging.py`:
```python
import json
import logging
from pathlib import Path

from common.logging import setup_logger


def test_setup_logger_writes_json_to_file(tmp_path: Path):
    log_dir = tmp_path / "logs"
    logger = setup_logger("test-mcp", log_dir=log_dir, level="DEBUG")

    logger.info("hello", extra={"req_id": "abc"})

    log_file = log_dir / "test-mcp.log"
    assert log_file.exists()
    line = log_file.read_text().strip().splitlines()[-1]
    record = json.loads(line)
    assert record["msg"] == "hello"
    assert record["level"] == "INFO"
    assert record["logger"] == "test-mcp"
    assert record["req_id"] == "abc"


def test_setup_logger_is_idempotent(tmp_path: Path):
    log_dir = tmp_path / "logs"
    a = setup_logger("dup", log_dir=log_dir)
    b = setup_logger("dup", log_dir=log_dir)
    assert a is b
    # No duplicated handlers
    assert len(a.handlers) == 1, f"expected single file handler, got {a.handlers}"


def test_setup_logger_does_not_leak_taskname(tmp_path: Path):
    import asyncio

    async def _log_from_task():
        logger = setup_logger("async-mcp", log_dir=tmp_path)
        logger.info("hello")

    asyncio.run(_log_from_task())
    line = (tmp_path / "async-mcp.log").read_text().strip().splitlines()[-1]
    record = json.loads(line)
    assert "taskName" not in record, f"taskName leaked: keys={sorted(record.keys())}"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_common_logging.py -v
```
Expected: FAIL — `ModuleNotFoundError: common.logging` (or `ImportError: setup_logger`).

- [ ] **Step 3: Implement `common/logging.py`**

```python
"""Structured JSON logger shared by all MCPs."""
from __future__ import annotations

import json
import logging
from pathlib import Path


class _JsonFormatter(logging.Formatter):
    _STD_ATTRS = {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message", "asctime", "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for k, v in record.__dict__.items():
            if k not in self._STD_ATTRS and not k.startswith("_"):
                payload[k] = v
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


_configured: dict[str, logging.Logger] = {}


def setup_logger(
    name: str,
    *,
    log_dir: Path | str = "logs",
    level: str = "INFO",
) -> logging.Logger:
    """Return a structured JSON logger; idempotent per-name."""
    if name in _configured:
        return _configured[name]

    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    file_handler = logging.FileHandler(log_dir / f"{name}.log", encoding="utf-8")
    file_handler.setFormatter(_JsonFormatter())
    logger.addHandler(file_handler)

    _configured[name] = logger
    return logger
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_common_logging.py -v
```
Expected: PASS (both tests).

- [ ] **Step 5: Commit**

```bash
git add common/logging.py tests/test_common_logging.py
git commit -m "feat(common): structured JSON logger with per-logger file handler"
```

---

### Task 3: `common/config.py` — TOML config loader

**Files:**
- Create: `common/config.py`
- Create: `tests/test_common_config.py`

- [ ] **Step 1: Write the failing test**

`tests/test_common_config.py`:
```python
from pathlib import Path

import pytest

from common.config import Config, load_config


def test_load_config_reads_toml(tmp_path: Path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        """
        [burp]
        bridge_url = "http://127.0.0.1:9999"

        [browser]
        chrome_candidates = ["chromium"]
        default_proxy = "127.0.0.1:8080"
        headless = true
        cdp_port = 9222
        navigation_timeout_s = 10

        [logging]
        level = "DEBUG"
        dir = "logs"
        """
    )
    cfg = load_config(cfg_file)
    assert isinstance(cfg, Config)
    assert cfg.burp.bridge_url == "http://127.0.0.1:9999"
    assert cfg.browser.headless is True
    assert cfg.browser.navigation_timeout_s == 10
    assert cfg.logging.level == "DEBUG"


def test_load_config_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nope.toml")


def test_load_config_local_override(tmp_path: Path):
    base = tmp_path / "config.toml"
    base.write_text(
        """
        [burp]
        bridge_url = "http://127.0.0.1:8775"
        [browser]
        chrome_candidates = ["chromium"]
        default_proxy = "127.0.0.1:8080"
        headless = false
        cdp_port = 9222
        navigation_timeout_s = 30
        [logging]
        level = "INFO"
        dir = "logs"
        """
    )
    local = tmp_path / "config.local.toml"
    local.write_text(
        """
        [browser]
        headless = true
        """
    )
    cfg = load_config(base)
    assert cfg.browser.headless is True
    assert cfg.burp.bridge_url == "http://127.0.0.1:8775"  # unchanged


def test_deep_merge_recurses_past_one_level():
    from common.config import _deep_merge
    base = {"a": {"b": {"c": 1, "d": 2}, "e": 3}, "f": 4}
    override = {"a": {"b": {"c": 99}}}
    result = _deep_merge(base, override)
    assert result == {"a": {"b": {"c": 99, "d": 2}, "e": 3}, "f": 4}


def test_deep_merge_list_replaces_not_appends():
    from common.config import _deep_merge
    base = {"xs": [1, 2, 3]}
    override = {"xs": [4]}
    result = _deep_merge(base, override)
    assert result == {"xs": [4]}


def test_load_config_raises_valueerror_on_malformed_section(tmp_path: Path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        """
        [burp]
        bridge_url = "http://127.0.0.1:8775"
        [browser]
        chrome_candidates = ["chromium"]
        default_proxy = "127.0.0.1:8080"
        headless = false
        cdp_port = 9222
        navigation_timeout_s = 30
        [logging]
        wrong_key = "INFO"
        dir = "logs"
        """
    )
    with pytest.raises(ValueError, match="invalid config"):
        load_config(cfg_file)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_common_config.py -v
```
Expected: FAIL — `ModuleNotFoundError: common.config`.

- [ ] **Step 3: Implement `common/config.py`**

```python
"""TOML config loader with optional local overrides."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BurpConfig:
    bridge_url: str


@dataclass
class BrowserConfig:
    chrome_candidates: list[str]
    default_proxy: str
    headless: bool
    cdp_port: int
    navigation_timeout_s: int


@dataclass
class LoggingConfig:
    level: str
    dir: str


@dataclass
class Config:
    burp: BurpConfig
    browser: BrowserConfig
    logging: LoggingConfig
    source: Path


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path: str | Path = "config.toml") -> Config:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    with path.open("rb") as fh:
        data = tomllib.load(fh)

    local = path.with_name("config.local.toml")
    if local.exists():
        with local.open("rb") as fh:
            data = _deep_merge(data, tomllib.load(fh))

    try:
        return Config(
            burp=BurpConfig(**data["burp"]),
            browser=BrowserConfig(**data["browser"]),
            logging=LoggingConfig(**data["logging"]),
            source=path,
        )
    except (KeyError, TypeError) as e:
        raise ValueError(f"invalid config at {path}: {e}") from e
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_common_config.py -v
```
Expected: PASS (six tests).

- [ ] **Step 5: Commit**

```bash
git add common/config.py tests/test_common_config.py
git commit -m "feat(common): TOML config loader with local-override merge"
```

---

### Task 4: `common/mcp_base.py` — error envelope + shared MCP helpers

**Files:**
- Create: `common/mcp_base.py`
- Create: `tests/test_common_mcp_base.py`

- [ ] **Step 1: Write the failing test**

`tests/test_common_mcp_base.py`:
```python
from common.mcp_base import error_envelope, ok_envelope, ErrorCode


def test_ok_envelope_wraps_data():
    env = ok_envelope({"a": 1})
    assert env == {"ok": True, "data": {"a": 1}}


def test_error_envelope_shape():
    env = error_envelope(ErrorCode.BAD_INPUT, "bad x", detail={"x": 1})
    assert env == {
        "ok": False,
        "error": {"code": "BAD_INPUT", "message": "bad x", "detail": {"x": 1}},
    }


def test_error_envelope_no_detail_defaults_to_empty_dict():
    env = error_envelope(ErrorCode.TIMEOUT, "slow")
    assert env["error"]["detail"] == {}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_common_mcp_base.py -v
```
Expected: FAIL — `ModuleNotFoundError: common.mcp_base`.

- [ ] **Step 3: Implement `common/mcp_base.py`**

```python
"""Shared MCP helpers: error envelope + stdio server boilerplate."""
from __future__ import annotations

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    BURP_UNAVAILABLE = "BURP_UNAVAILABLE"
    TARGET_NOT_ATTACHED = "TARGET_NOT_ATTACHED"
    PRO_REQUIRED = "PRO_REQUIRED"
    TIMEOUT = "TIMEOUT"
    BAD_INPUT = "BAD_INPUT"
    UPSTREAM_HTTP = "UPSTREAM_HTTP"
    INTERNAL = "INTERNAL"


def ok_envelope(data: Any) -> dict:
    return {"ok": True, "data": data}


def error_envelope(code: ErrorCode, message: str, detail: dict | None = None) -> dict:
    return {
        "ok": False,
        "error": {
            "code": code.value,
            "message": message,
            "detail": detail or {},
        },
    }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_common_mcp_base.py -v
```
Expected: PASS (three tests).

- [ ] **Step 5: Commit**

```bash
git add common/mcp_base.py tests/test_common_mcp_base.py
git commit -m "feat(common): error envelope and shared MCP helpers"
```

---

### Task 5: `common/cdp.py` — Chrome DevTools Protocol websocket client

**Files:**
- Create: `common/cdp.py`
- Create: `tests/test_common_cdp.py`

- [ ] **Step 1: Write the failing test**

`tests/test_common_cdp.py`:
```python
import asyncio
import json

import pytest
import websockets

from common.cdp import CDPSession, CDPError


async def _fake_cdp(ws):
    """Fake CDP server: echo method name in result, emit loadEventFired on Page.enable."""
    async for raw in ws:
        msg = json.loads(raw)
        mid = msg["id"]
        method = msg["method"]
        if method == "Page.enable":
            await ws.send(json.dumps({"id": mid, "result": {}}))
            await ws.send(json.dumps({
                "method": "Page.loadEventFired",
                "params": {"timestamp": 1.0},
            }))
        else:
            await ws.send(json.dumps({"id": mid, "result": {"method": method}}))


@pytest.mark.asyncio
async def test_cdp_send_and_event():
    async with websockets.serve(_fake_cdp, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        url = f"ws://127.0.0.1:{port}"

        events = []

        def on_event(name, params):
            events.append((name, params))

        async with CDPSession(url, on_event=on_event) as sess:
            result = await sess.send("Page.enable")
            assert result == {}
            # Give event loop a tick to receive the event
            await asyncio.sleep(0.05)
            assert ("Page.loadEventFired", {"timestamp": 1.0}) in events


@pytest.mark.asyncio
async def test_cdp_send_returns_result():
    async with websockets.serve(_fake_cdp, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        url = f"ws://127.0.0.1:{port}"
        async with CDPSession(url) as sess:
            r = await sess.send("DOM.getDocument", {"depth": -1})
            assert r == {"method": "DOM.getDocument"}


@pytest.mark.asyncio
async def test_cdp_error_response_raises():
    async def err_server(ws):
        async for raw in ws:
            mid = json.loads(raw)["id"]
            await ws.send(json.dumps({
                "id": mid,
                "error": {"code": -32000, "message": "boom"},
            }))

    async with websockets.serve(err_server, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        async with CDPSession(f"ws://127.0.0.1:{port}") as sess:
            with pytest.raises(RuntimeError, match="boom"):
                await sess.send("X.y")


@pytest.mark.asyncio
async def test_cdp_server_disconnect_fails_pending_send():
    """Server that drops the connection without replying — send() must fail, not hang."""

    async def dropper(ws):
        await asyncio.sleep(0.05)  # let the client send its request
        await ws.close()

    async with websockets.serve(dropper, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        async with CDPSession(f"ws://127.0.0.1:{port}") as sess:
            with pytest.raises((ConnectionError, RuntimeError)):
                await asyncio.wait_for(sess.send("X.y"), timeout=1.0)


@pytest.mark.asyncio
async def test_cdp_clean_exit_with_pending_send():
    """Context manager exit while a send is awaiting — no hang, no warnings."""

    async def silent(ws):
        async for _ in ws:
            pass  # never reply

    async with websockets.serve(silent, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]

        async def run():
            async with CDPSession(f"ws://127.0.0.1:{port}") as sess:
                pending = asyncio.create_task(sess.send("X.y"))
                await asyncio.sleep(0.05)
                # Exiting the context manager should fail the pending send.
            with pytest.raises((ConnectionError, RuntimeError)):
                await pending

        await asyncio.wait_for(run(), timeout=2.0)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_common_cdp.py -v
```
Expected: FAIL — `ModuleNotFoundError: common.cdp`.

- [ ] **Step 3: Implement `common/cdp.py`**

```python
"""Chrome DevTools Protocol session over websocket."""
from __future__ import annotations

import asyncio
import itertools
import json
from typing import Any, Callable

import websockets
from websockets.asyncio.client import ClientConnection


EventCallback = Callable[[str, dict], None]


class CDPError(RuntimeError):
    """CDP protocol-level error. Subclass of RuntimeError for caller compatibility."""

    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(f"CDP error {code}: {message}")
        self.code = code
        self.data = data


class CDPSession:
    """Async CDP client over websocket.

    Use as `async with CDPSession(url, on_event=cb) as sess: await sess.send(...)`.

    The optional `on_event` callback is invoked synchronously from the reader
    coroutine for every non-reply CDP event. It must be fast and non-blocking
    (e.g. a deque append or queue put_nowait); anything slower will starve
    request/response correlation.
    """

    def __init__(self, ws_url: str, *, on_event: EventCallback | None = None) -> None:
        self._url = ws_url
        self._on_event = on_event
        self._ws: ClientConnection | None = None
        self._reader_task: asyncio.Task | None = None
        self._pending: dict[int, asyncio.Future] = {}
        self._id_seq = itertools.count(1)

    async def __aenter__(self) -> "CDPSession":
        self._ws = await websockets.connect(self._url, max_size=64 * 1024 * 1024)
        self._reader_task = asyncio.create_task(self._reader())
        return self

    async def __aexit__(self, *exc: Any) -> None:
        # Close ws first so reader's `async for` exits cleanly via ConnectionClosedOK.
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
        # Await the reader so it finalizes _pending; no "Task was destroyed" warnings.
        if self._reader_task is not None and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except (asyncio.CancelledError, Exception):
                pass
        # Safety net: if any futures survived reader finalization, fail them now.
        for fut in self._pending.values():
            if not fut.done():
                fut.set_exception(ConnectionError("CDP session closed"))
        self._pending.clear()

    async def send(self, method: str, params: dict | None = None) -> Any:
        assert self._ws is not None, "session not open"
        mid = next(self._id_seq)
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending[mid] = fut
        await self._ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        return await fut

    async def _reader(self) -> None:
        assert self._ws is not None
        try:
            async for raw in self._ws:
                msg = json.loads(raw)
                if "id" in msg:
                    fut = self._pending.pop(msg["id"], None)
                    if fut is None:
                        continue
                    if "error" in msg:
                        err = msg["error"]
                        fut.set_exception(
                            CDPError(
                                code=int(err.get("code", 0)),
                                message=err.get("message", "cdp error"),
                                data=err.get("data"),
                            )
                        )
                    else:
                        fut.set_result(msg.get("result", {}))
                else:
                    method = msg.get("method")
                    params = msg.get("params", {})
                    if method and self._on_event:
                        self._on_event(method, params)
        except (asyncio.CancelledError, websockets.ConnectionClosed):
            pass
        finally:
            # Whatever caused the reader to exit, fail in-flight callers.
            exc = ConnectionError("CDP websocket closed")
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(exc)
            self._pending.clear()


async def discover_targets(http_url: str = "http://127.0.0.1:9222") -> list[dict]:
    """Return CDP target list via DevTools HTTP endpoint."""
    import httpx
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.get(f"{http_url}/json")
        resp.raise_for_status()
        return resp.json()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_common_cdp.py -v
```
Expected: PASS (five tests).

- [ ] **Step 5: Commit**

```bash
git add common/cdp.py tests/test_common_cdp.py
git commit -m "feat(common): CDP websocket session with event callback + target discovery"
```

---

### Task 6: browser-mcp package skeleton

**Files:**
- Create: `MCPs/browser-mcp/pyproject.toml`
- Create: `MCPs/browser-mcp/browser_mcp/__init__.py`
- Create: `MCPs/browser-mcp/browser_mcp/server.py` (stub)
- Create: `MCPs/browser-mcp/browser_mcp/chrome_launcher.py` (stub)
- Create: `MCPs/browser-mcp/browser_mcp/tools.py` (stub)
- Create: `MCPs/browser-mcp/tests/__init__.py`

- [ ] **Step 1: Write `MCPs/browser-mcp/pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "browser-mcp"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = ["mcp>=1.0.0", "httpx>=0.27", "websockets>=12"]

[project.scripts]
browser-mcp = "browser_mcp.server:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["browser_mcp*"]
```

- [ ] **Step 2: Write stub modules**

`MCPs/browser-mcp/browser_mcp/__init__.py`:
```python
"""browser-mcp: Chrome DevTools Protocol MCP server."""
```

`MCPs/browser-mcp/browser_mcp/server.py`:
```python
"""MCP stdio server entry point. Filled in by later tasks."""


def main() -> None:
    raise NotImplementedError("implemented in Task 19")


if __name__ == "__main__":
    main()
```

`MCPs/browser-mcp/browser_mcp/chrome_launcher.py`:
```python
"""Chrome subprocess launcher. Filled in by Task 7."""
```

`MCPs/browser-mcp/browser_mcp/tools.py`:
```python
"""Tool implementations. Filled in by later tasks."""
```

`MCPs/browser-mcp/tests/__init__.py`: empty file.

- [ ] **Step 3: Install editable and verify import**

```bash
source /home/kali/Web-MCP/.venv/bin/activate
cd /home/kali/Web-MCP
pip install -e MCPs/browser-mcp
python -c "import browser_mcp; print('ok')"
```
Expected: `ok`.

- [ ] **Step 4: Commit**

```bash
git add MCPs/browser-mcp/
git commit -m "chore(browser-mcp): package skeleton with editable install"
```

---

### Task 7: Chrome launcher

**Files:**
- Modify: `MCPs/browser-mcp/browser_mcp/chrome_launcher.py`
- Create: `MCPs/browser-mcp/tests/test_chrome_launcher.py`

- [ ] **Step 1: Write the failing test**

`MCPs/browser-mcp/tests/test_chrome_launcher.py`:
```python
import shutil

import pytest

from browser_mcp.chrome_launcher import (
    ChromeNotFoundError,
    build_chrome_argv,
    resolve_chrome_binary,
)


def test_build_chrome_argv_minimal():
    argv = build_chrome_argv(
        binary="chromium",
        cdp_port=9222,
        proxy=None,
        headless=False,
        user_data_dir="/tmp/p",
    )
    assert argv[0] == "chromium"
    assert "--remote-debugging-port=9222" in argv
    assert "--user-data-dir=/tmp/p" in argv
    assert "--ignore-certificate-errors" in argv
    assert "--no-first-run" in argv
    assert not any(a.startswith("--proxy-server=") for a in argv)
    assert "--headless=new" not in argv


def test_build_chrome_argv_with_proxy_and_headless():
    argv = build_chrome_argv(
        binary="chromium",
        cdp_port=9222,
        proxy="127.0.0.1:8080",
        headless=True,
        user_data_dir="/tmp/p",
    )
    assert "--proxy-server=127.0.0.1:8080" in argv
    assert "--headless=new" in argv


def test_resolve_chrome_binary_finds_existing(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda x: f"/usr/bin/{x}" if x == "chromium" else None)
    assert resolve_chrome_binary(["nope", "chromium"]) == "/usr/bin/chromium"


def test_resolve_chrome_binary_raises_when_none_found(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda x: None)
    with pytest.raises(ChromeNotFoundError):
        resolve_chrome_binary(["nope1", "nope2"])
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest MCPs/browser-mcp/tests/test_chrome_launcher.py -v
```
Expected: FAIL — symbols not defined.

- [ ] **Step 3: Implement `chrome_launcher.py`**

```python
"""Resolve and launch Chrome for CDP-driven automation."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class ChromeNotFoundError(RuntimeError):
    """No Chrome-compatible binary found on PATH."""


def resolve_chrome_binary(candidates: list[str]) -> str:
    """Return the first candidate resolvable via `shutil.which`."""
    for name in candidates:
        if Path(name).is_absolute() and Path(name).exists():
            return name
        found = shutil.which(name)
        if found:
            return found
    raise ChromeNotFoundError(
        f"none of {candidates} found on PATH or as absolute paths"
    )


def build_chrome_argv(
    *,
    binary: str,
    cdp_port: int,
    proxy: str | None,
    headless: bool,
    user_data_dir: str,
) -> list[str]:
    argv = [
        binary,
        f"--remote-debugging-port={cdp_port}",
        f"--user-data-dir={user_data_dir}",
        "--ignore-certificate-errors",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=InterestFeedContentSuggestions,Translate",
        "about:blank",
    ]
    if proxy:
        argv.insert(1, f"--proxy-server={proxy}")
    if headless:
        argv.insert(1, "--headless=new")
    return argv


def launch_chrome(argv: list[str]) -> subprocess.Popen:
    """Spawn Chrome as a detached subprocess. Caller owns termination."""
    return subprocess.Popen(
        argv,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest MCPs/browser-mcp/tests/test_chrome_launcher.py -v
```
Expected: PASS (four tests).

- [ ] **Step 5: Commit**

```bash
git add MCPs/browser-mcp/browser_mcp/chrome_launcher.py MCPs/browser-mcp/tests/test_chrome_launcher.py
git commit -m "feat(browser-mcp): chrome binary resolver + argv builder"
```

---

### Task 8: `browser_launch` tool + session state

**Files:**
- Modify: `MCPs/browser-mcp/browser_mcp/tools.py`
- Create: `MCPs/browser-mcp/tests/test_tool_launch.py`

- [ ] **Step 1: Write the failing test**

`MCPs/browser-mcp/tests/test_tool_launch.py`:
```python
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from browser_mcp.tools import BrowserSession


@pytest.mark.asyncio
async def test_launch_resolves_binary_starts_chrome_and_connects(monkeypatch, tmp_path):
    # Stub the Chrome binary resolution and subprocess
    fake_proc = MagicMock()
    fake_proc.poll.return_value = None
    monkeypatch.setattr("browser_mcp.tools.launch_chrome", lambda argv: fake_proc)
    monkeypatch.setattr(
        "browser_mcp.tools.resolve_chrome_binary", lambda candidates: "/usr/bin/chromium"
    )

    # Stub the DevTools /json endpoint: return one page target
    async def fake_discover(_url):
        return [{"type": "page", "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/page/X"}]

    monkeypatch.setattr("browser_mcp.tools.discover_targets", fake_discover)

    # Stub CDPSession to avoid real websocket
    class FakeSess:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            pass

        async def send(self, method, params=None):
            return {}

    monkeypatch.setattr("browser_mcp.tools.CDPSession", lambda url, on_event=None: FakeSess())

    sess = BrowserSession(
        chrome_candidates=["chromium"],
        cdp_port=9222,
        default_proxy="127.0.0.1:8080",
        user_data_dir_root=str(tmp_path),
    )
    result = await sess.launch(headless=True, proxy=None)
    assert result["ok"] is True
    assert sess.is_attached()
    await sess.close()


@pytest.mark.asyncio
async def test_launch_returns_error_when_chrome_missing(monkeypatch, tmp_path):
    from browser_mcp.chrome_launcher import ChromeNotFoundError

    def raiser(_):
        raise ChromeNotFoundError("no chrome")

    monkeypatch.setattr("browser_mcp.tools.resolve_chrome_binary", raiser)
    sess = BrowserSession(
        chrome_candidates=["nope"],
        cdp_port=9222,
        default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    result = await sess.launch()
    assert result["ok"] is False
    assert result["error"]["code"] == "INTERNAL"
    assert "no chrome" in result["error"]["message"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest MCPs/browser-mcp/tests/test_tool_launch.py -v
```
Expected: FAIL — `BrowserSession` not defined.

- [ ] **Step 3: Implement `BrowserSession.launch`**

`MCPs/browser-mcp/browser_mcp/tools.py`:
```python
"""browser-mcp tool implementations."""
from __future__ import annotations

import asyncio
import base64
import os
import tempfile
import time
from collections import deque
from typing import Any

from common.cdp import CDPSession, discover_targets
from common.mcp_base import ErrorCode, error_envelope, ok_envelope

from .chrome_launcher import (
    ChromeNotFoundError,
    build_chrome_argv,
    launch_chrome,
    resolve_chrome_binary,
)


class BrowserSession:
    """Owns a single Chrome process + attached CDP session."""

    def __init__(
        self,
        *,
        chrome_candidates: list[str],
        cdp_port: int,
        default_proxy: str | None,
        user_data_dir_root: str,
        navigation_timeout_s: int = 30,
    ) -> None:
        self._candidates = chrome_candidates
        self._cdp_port = cdp_port
        self._default_proxy = default_proxy
        self._udd_root = user_data_dir_root
        self._nav_timeout = navigation_timeout_s

        self._proc = None
        self._cdp: CDPSession | None = None
        self._cdp_cm = None
        self._network_log: deque[dict] = deque(maxlen=5000)
        self._network_seq = 0
        self._load_events: asyncio.Queue[float] = asyncio.Queue()

    def is_attached(self) -> bool:
        return self._cdp is not None and self._proc is not None and self._proc.poll() is None

    def _on_event(self, method: str, params: dict) -> None:
        if method.startswith("Network."):
            self._network_seq += 1
            self._network_log.append({"seq": self._network_seq, "method": method, "params": params})
        elif method == "Page.loadEventFired":
            try:
                self._load_events.put_nowait(params.get("timestamp", time.time()))
            except asyncio.QueueFull:
                pass

    async def launch(
        self,
        *,
        headless: bool = False,
        proxy: str | None = None,
    ) -> dict:
        if self.is_attached():
            await self.close()

        try:
            binary = resolve_chrome_binary(self._candidates)
        except ChromeNotFoundError as e:
            return error_envelope(ErrorCode.INTERNAL, str(e))

        udd = tempfile.mkdtemp(prefix="web-mcp-chrome-", dir=self._udd_root)
        argv = build_chrome_argv(
            binary=binary,
            cdp_port=self._cdp_port,
            proxy=proxy if proxy is not None else self._default_proxy,
            headless=headless,
            user_data_dir=udd,
        )
        self._proc = launch_chrome(argv)

        # Poll for CDP ready
        ws_url: str | None = None
        for _ in range(50):
            try:
                targets = await discover_targets(f"http://127.0.0.1:{self._cdp_port}")
                for t in targets:
                    if t.get("type") == "page" and "webSocketDebuggerUrl" in t:
                        ws_url = t["webSocketDebuggerUrl"]
                        break
                if ws_url:
                    break
            except Exception:
                pass
            await asyncio.sleep(0.1)

        if not ws_url:
            await self.close()
            return error_envelope(
                ErrorCode.INTERNAL,
                "Chrome started but CDP target did not appear within 5s",
            )

        self._cdp_cm = CDPSession(ws_url, on_event=self._on_event)
        self._cdp = await self._cdp_cm.__aenter__()
        await self._cdp.send("Page.enable")
        await self._cdp.send("Network.enable")
        await self._cdp.send("Runtime.enable")
        await self._cdp.send("DOM.enable")

        return ok_envelope({"chrome_binary": binary, "cdp_url": ws_url})

    async def close(self) -> dict:
        if self._cdp_cm is not None:
            try:
                await self._cdp_cm.__aexit__(None, None, None)
            except Exception:
                pass
        self._cdp = None
        self._cdp_cm = None
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=5)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
        self._proc = None
        return ok_envelope({"closed": True})
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest MCPs/browser-mcp/tests/test_tool_launch.py -v
```
Expected: PASS (two tests).

- [ ] **Step 5: Commit**

```bash
git add MCPs/browser-mcp/browser_mcp/tools.py MCPs/browser-mcp/tests/test_tool_launch.py
git commit -m "feat(browser-mcp): BrowserSession with launch/close + event accumulation"
```

---

### Task 9: `browser_navigate` tool

**Files:**
- Modify: `MCPs/browser-mcp/browser_mcp/tools.py`
- Create: `MCPs/browser-mcp/tests/test_tool_navigate.py`

- [ ] **Step 1: Write the failing test**

`MCPs/browser-mcp/tests/test_tool_navigate.py`:
```python
import asyncio

import pytest

from browser_mcp.tools import BrowserSession


class _FakeCDP:
    def __init__(self, events):
        self._events = events
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        return {"frameId": "F"}


@pytest.mark.asyncio
async def test_navigate_success(monkeypatch, tmp_path):
    sess = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path), navigation_timeout_s=2,
    )
    fake = _FakeCDP(events=[])
    sess._cdp = fake
    sess._proc = type("P", (), {"poll": lambda self: None})()

    # Simulate load event arriving after send
    async def fire_event():
        await asyncio.sleep(0.01)
        await sess._load_events.put(1.0)

    asyncio.create_task(fire_event())
    result = await sess.navigate("https://example.com")
    assert result["ok"] is True
    assert fake.sent[0][0] == "Page.navigate"
    assert fake.sent[0][1] == {"url": "https://example.com"}


@pytest.mark.asyncio
async def test_navigate_timeout(monkeypatch, tmp_path):
    sess = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path), navigation_timeout_s=0,
    )
    sess._cdp = _FakeCDP(events=[])
    sess._proc = type("P", (), {"poll": lambda self: None})()

    result = await sess.navigate("https://example.com")
    assert result["ok"] is False
    assert result["error"]["code"] == "TIMEOUT"


@pytest.mark.asyncio
async def test_navigate_without_attach(tmp_path):
    sess = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    result = await sess.navigate("https://example.com")
    assert result["error"]["code"] == "TARGET_NOT_ATTACHED"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest MCPs/browser-mcp/tests/test_tool_navigate.py -v
```
Expected: FAIL — `navigate` not defined.

- [ ] **Step 3: Add `navigate` method to `BrowserSession`**

Append to `MCPs/browser-mcp/browser_mcp/tools.py` inside `BrowserSession`:
```python
    def _require_attached(self) -> dict | None:
        if not self.is_attached():
            return error_envelope(
                ErrorCode.TARGET_NOT_ATTACHED,
                "no browser session; call browser_launch first",
            )
        return None

    async def _drain_load_events(self) -> None:
        while not self._load_events.empty():
            try:
                self._load_events.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def navigate(self, url: str) -> dict:
        err = self._require_attached()
        if err:
            return err
        await self._drain_load_events()
        try:
            await self._cdp.send("Page.navigate", {"url": url})
        except Exception as e:
            return error_envelope(ErrorCode.INTERNAL, f"Page.navigate failed: {e}")
        try:
            await asyncio.wait_for(self._load_events.get(), timeout=self._nav_timeout)
        except asyncio.TimeoutError:
            return error_envelope(
                ErrorCode.TIMEOUT,
                f"load event not received within {self._nav_timeout}s",
                detail={"url": url},
            )
        return ok_envelope({"url": url})
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest MCPs/browser-mcp/tests/test_tool_navigate.py -v
```
Expected: PASS (three tests).

- [ ] **Step 5: Commit**

```bash
git add MCPs/browser-mcp/browser_mcp/tools.py MCPs/browser-mcp/tests/test_tool_navigate.py
git commit -m "feat(browser-mcp): navigate tool with load-event timeout"
```

---

### Task 10: `browser_snapshot` tool (DOM + a11y tree)

**Files:**
- Modify: `MCPs/browser-mcp/browser_mcp/tools.py`
- Create: `MCPs/browser-mcp/tests/test_tool_snapshot.py`

- [ ] **Step 1: Write the failing test**

`MCPs/browser-mcp/tests/test_tool_snapshot.py`:
```python
import pytest

from browser_mcp.tools import BrowserSession


class _FakeCDP:
    def __init__(self):
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        if method == "DOM.getDocument":
            return {"root": {"nodeId": 1, "nodeName": "#document"}}
        if method == "Accessibility.getFullAXTree":
            return {"nodes": [{"role": {"value": "WebArea"}}]}
        return {}


@pytest.mark.asyncio
async def test_snapshot_returns_dom_and_ax(monkeypatch, tmp_path):
    sess = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    sess._cdp = _FakeCDP()
    sess._proc = type("P", (), {"poll": lambda self: None})()
    result = await sess.snapshot()
    assert result["ok"] is True
    assert result["data"]["dom"]["root"]["nodeName"] == "#document"
    assert result["data"]["accessibility"]["nodes"][0]["role"]["value"] == "WebArea"


@pytest.mark.asyncio
async def test_snapshot_requires_attachment(tmp_path):
    sess = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    result = await sess.snapshot()
    assert result["error"]["code"] == "TARGET_NOT_ATTACHED"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest MCPs/browser-mcp/tests/test_tool_snapshot.py -v
```
Expected: FAIL.

- [ ] **Step 3: Add `snapshot` method to `BrowserSession`**

```python
    async def snapshot(self) -> dict:
        err = self._require_attached()
        if err:
            return err
        dom = await self._cdp.send("DOM.getDocument", {"depth": -1})
        ax = await self._cdp.send("Accessibility.getFullAXTree")
        return ok_envelope({"dom": dom, "accessibility": ax})
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest MCPs/browser-mcp/tests/test_tool_snapshot.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add MCPs/browser-mcp/browser_mcp/tools.py MCPs/browser-mcp/tests/test_tool_snapshot.py
git commit -m "feat(browser-mcp): snapshot tool (DOM + accessibility tree)"
```

---

### Task 11: `browser_query` tool (selector → HTML)

**Files:**
- Modify: `MCPs/browser-mcp/browser_mcp/tools.py`
- Create: `MCPs/browser-mcp/tests/test_tool_query.py`

- [ ] **Step 1: Write the failing test**

`MCPs/browser-mcp/tests/test_tool_query.py`:
```python
import pytest

from browser_mcp.tools import BrowserSession


class _FakeCDP:
    def __init__(self, found_id=None):
        self._found = found_id
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        if method == "DOM.getDocument":
            return {"root": {"nodeId": 1}}
        if method == "DOM.querySelector":
            return {"nodeId": self._found if self._found is not None else 0}
        if method == "DOM.getOuterHTML":
            return {"outerHTML": "<div id='x'>hi</div>"}
        return {}


def _sess_with_cdp(cdp, tmp_path):
    sess = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    sess._cdp = cdp
    sess._proc = type("P", (), {"poll": lambda self: None})()
    return sess


@pytest.mark.asyncio
async def test_query_found(tmp_path):
    sess = _sess_with_cdp(_FakeCDP(found_id=42), tmp_path)
    result = await sess.query("#x")
    assert result["ok"] is True
    assert result["data"]["html"] == "<div id='x'>hi</div>"


@pytest.mark.asyncio
async def test_query_not_found(tmp_path):
    sess = _sess_with_cdp(_FakeCDP(found_id=0), tmp_path)
    result = await sess.query("#nope")
    assert result["ok"] is False
    assert result["error"]["code"] == "BAD_INPUT"
    assert result["error"]["detail"]["selector"] == "#nope"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest MCPs/browser-mcp/tests/test_tool_query.py -v
```
Expected: FAIL.

- [ ] **Step 3: Add `query` method**

```python
    async def _root_node_id(self) -> int:
        doc = await self._cdp.send("DOM.getDocument", {"depth": 0})
        return doc["root"]["nodeId"]

    async def query(self, selector: str) -> dict:
        err = self._require_attached()
        if err:
            return err
        root = await self._root_node_id()
        found = await self._cdp.send(
            "DOM.querySelector", {"nodeId": root, "selector": selector}
        )
        node_id = found.get("nodeId", 0)
        if not node_id:
            return error_envelope(
                ErrorCode.BAD_INPUT, "selector not found", detail={"selector": selector}
            )
        html = await self._cdp.send("DOM.getOuterHTML", {"nodeId": node_id})
        return ok_envelope({"html": html.get("outerHTML", ""), "nodeId": node_id})
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest MCPs/browser-mcp/tests/test_tool_query.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add MCPs/browser-mcp/browser_mcp/tools.py MCPs/browser-mcp/tests/test_tool_query.py
git commit -m "feat(browser-mcp): query tool (selector → outerHTML)"
```

---

### Task 12: `browser_click` tool

**Files:**
- Modify: `MCPs/browser-mcp/browser_mcp/tools.py`
- Create: `MCPs/browser-mcp/tests/test_tool_click.py`

- [ ] **Step 1: Write the failing test**

`MCPs/browser-mcp/tests/test_tool_click.py`:
```python
import pytest

from browser_mcp.tools import BrowserSession


class _FakeCDP:
    def __init__(self, found_id=42, box=None):
        self._found = found_id
        self._box = box or {"model": {"content": [10, 20, 30, 20, 30, 40, 10, 40]}}
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        if method == "DOM.getDocument":
            return {"root": {"nodeId": 1}}
        if method == "DOM.querySelector":
            return {"nodeId": self._found}
        if method == "DOM.getBoxModel":
            return self._box
        if method == "Input.dispatchMouseEvent":
            return {}
        return {}


def _sess(cdp, tmp_path):
    s = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    s._cdp = cdp
    s._proc = type("P", (), {"poll": lambda self: None})()
    return s


@pytest.mark.asyncio
async def test_click_dispatches_mouse_events(tmp_path):
    cdp = _FakeCDP()
    sess = _sess(cdp, tmp_path)
    result = await sess.click("#btn")
    assert result["ok"] is True
    types = [p["type"] for m, p in cdp.sent if m == "Input.dispatchMouseEvent"]
    assert types == ["mousePressed", "mouseReleased"]


@pytest.mark.asyncio
async def test_click_not_found(tmp_path):
    sess = _sess(_FakeCDP(found_id=0), tmp_path)
    result = await sess.click("#nope")
    assert result["error"]["code"] == "BAD_INPUT"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest MCPs/browser-mcp/tests/test_tool_click.py -v
```
Expected: FAIL.

- [ ] **Step 3: Add `click` method**

```python
    async def click(self, selector: str) -> dict:
        err = self._require_attached()
        if err:
            return err
        root = await self._root_node_id()
        found = await self._cdp.send(
            "DOM.querySelector", {"nodeId": root, "selector": selector}
        )
        node_id = found.get("nodeId", 0)
        if not node_id:
            return error_envelope(
                ErrorCode.BAD_INPUT, "selector not found", detail={"selector": selector}
            )
        box = await self._cdp.send("DOM.getBoxModel", {"nodeId": node_id})
        quad = box["model"]["content"]
        cx = (quad[0] + quad[4]) / 2
        cy = (quad[1] + quad[5]) / 2
        for phase in ("mousePressed", "mouseReleased"):
            await self._cdp.send(
                "Input.dispatchMouseEvent",
                {"type": phase, "x": cx, "y": cy, "button": "left", "clickCount": 1},
            )
        return ok_envelope({"clicked": selector, "x": cx, "y": cy})
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest MCPs/browser-mcp/tests/test_tool_click.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add MCPs/browser-mcp/browser_mcp/tools.py MCPs/browser-mcp/tests/test_tool_click.py
git commit -m "feat(browser-mcp): click tool via box-model centroid mouse events"
```

---

### Task 13: `browser_fill` tool

**Files:**
- Modify: `MCPs/browser-mcp/browser_mcp/tools.py`
- Create: `MCPs/browser-mcp/tests/test_tool_fill.py`

- [ ] **Step 1: Write the failing test**

`MCPs/browser-mcp/tests/test_tool_fill.py`:
```python
import pytest

from browser_mcp.tools import BrowserSession


class _FakeCDP:
    def __init__(self, found_id=7):
        self._found = found_id
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        if method == "DOM.getDocument":
            return {"root": {"nodeId": 1}}
        if method == "DOM.querySelector":
            return {"nodeId": self._found}
        return {}


def _sess(cdp, tmp_path):
    s = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    s._cdp = cdp
    s._proc = type("P", (), {"poll": lambda self: None})()
    return s


@pytest.mark.asyncio
async def test_fill_focuses_and_inserts_text(tmp_path):
    cdp = _FakeCDP()
    sess = _sess(cdp, tmp_path)
    result = await sess.fill("input[name=q]", "payload")
    assert result["ok"] is True
    methods = [m for m, _ in cdp.sent]
    assert "DOM.focus" in methods
    assert "Input.insertText" in methods
    insert = next(p for m, p in cdp.sent if m == "Input.insertText")
    assert insert == {"text": "payload"}


@pytest.mark.asyncio
async def test_fill_not_found(tmp_path):
    sess = _sess(_FakeCDP(found_id=0), tmp_path)
    result = await sess.fill("#nope", "x")
    assert result["error"]["code"] == "BAD_INPUT"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest MCPs/browser-mcp/tests/test_tool_fill.py -v
```
Expected: FAIL.

- [ ] **Step 3: Add `fill` method**

```python
    async def fill(self, selector: str, text: str) -> dict:
        err = self._require_attached()
        if err:
            return err
        root = await self._root_node_id()
        found = await self._cdp.send(
            "DOM.querySelector", {"nodeId": root, "selector": selector}
        )
        node_id = found.get("nodeId", 0)
        if not node_id:
            return error_envelope(
                ErrorCode.BAD_INPUT, "selector not found", detail={"selector": selector}
            )
        await self._cdp.send("DOM.focus", {"nodeId": node_id})
        await self._cdp.send("Input.insertText", {"text": text})
        return ok_envelope({"filled": selector, "length": len(text)})
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest MCPs/browser-mcp/tests/test_tool_fill.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add MCPs/browser-mcp/browser_mcp/tools.py MCPs/browser-mcp/tests/test_tool_fill.py
git commit -m "feat(browser-mcp): fill tool (focus + Input.insertText)"
```

---

### Task 14: `browser_eval` tool

**Files:**
- Modify: `MCPs/browser-mcp/browser_mcp/tools.py`
- Create: `MCPs/browser-mcp/tests/test_tool_eval.py`

- [ ] **Step 1: Write the failing test**

`MCPs/browser-mcp/tests/test_tool_eval.py`:
```python
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
    assert result["ok"] is True  # evaluation call itself succeeded
    assert result["data"]["exception"] is not None
    assert "ReferenceError" in result["data"]["exception"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest MCPs/browser-mcp/tests/test_tool_eval.py -v
```
Expected: FAIL.

- [ ] **Step 3: Add `eval_js` method**

```python
    async def eval_js(self, expression: str) -> dict:
        err = self._require_attached()
        if err:
            return err
        resp = await self._cdp.send(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
        )
        exc = resp.get("exceptionDetails")
        return ok_envelope(
            {
                "value": resp.get("result", {}).get("value"),
                "type": resp.get("result", {}).get("type"),
                "exception": exc.get("text") if exc else None,
            }
        )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest MCPs/browser-mcp/tests/test_tool_eval.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add MCPs/browser-mcp/browser_mcp/tools.py MCPs/browser-mcp/tests/test_tool_eval.py
git commit -m "feat(browser-mcp): eval_js tool returns value or exception text"
```

---

### Task 15: `browser_screenshot` tool

**Files:**
- Modify: `MCPs/browser-mcp/browser_mcp/tools.py`
- Create: `MCPs/browser-mcp/tests/test_tool_screenshot.py`

- [ ] **Step 1: Write the failing test**

`MCPs/browser-mcp/tests/test_tool_screenshot.py`:
```python
import base64

import pytest

from browser_mcp.tools import BrowserSession


class _FakeCDP:
    def __init__(self):
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        if method == "Page.captureScreenshot":
            return {"data": base64.b64encode(b"\x89PNG...fake").decode()}
        return {}


def _sess(cdp, tmp_path):
    s = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    s._cdp = cdp
    s._proc = type("P", (), {"poll": lambda self: None})()
    return s


@pytest.mark.asyncio
async def test_screenshot_returns_base64_png(tmp_path):
    sess = _sess(_FakeCDP(), tmp_path)
    result = await sess.screenshot(full_page=True)
    assert result["ok"] is True
    assert result["data"]["format"] == "png"
    assert base64.b64decode(result["data"]["base64"]).startswith(b"\x89PNG")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest MCPs/browser-mcp/tests/test_tool_screenshot.py -v
```
Expected: FAIL.

- [ ] **Step 3: Add `screenshot` method**

```python
    async def screenshot(self, *, full_page: bool = False) -> dict:
        err = self._require_attached()
        if err:
            return err
        params = {"format": "png", "captureBeyondViewport": full_page}
        resp = await self._cdp.send("Page.captureScreenshot", params)
        return ok_envelope({"format": "png", "base64": resp.get("data", "")})
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest MCPs/browser-mcp/tests/test_tool_screenshot.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add MCPs/browser-mcp/browser_mcp/tools.py MCPs/browser-mcp/tests/test_tool_screenshot.py
git commit -m "feat(browser-mcp): screenshot tool (base64 PNG)"
```

---

### Task 16: `browser_cookies` + `browser_set_cookie`

**Files:**
- Modify: `MCPs/browser-mcp/browser_mcp/tools.py`
- Create: `MCPs/browser-mcp/tests/test_tool_cookies.py`

- [ ] **Step 1: Write the failing test**

`MCPs/browser-mcp/tests/test_tool_cookies.py`:
```python
import pytest

from browser_mcp.tools import BrowserSession


class _FakeCDP:
    def __init__(self):
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        if method == "Network.getCookies":
            return {"cookies": [{"name": "SID", "value": "abc", "domain": "example.com"}]}
        if method == "Network.setCookie":
            return {"success": True}
        return {}


def _sess(cdp, tmp_path):
    s = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    s._cdp = cdp
    s._proc = type("P", (), {"poll": lambda self: None})()
    return s


@pytest.mark.asyncio
async def test_cookies_list(tmp_path):
    sess = _sess(_FakeCDP(), tmp_path)
    result = await sess.cookies()
    assert result["ok"] is True
    assert result["data"]["cookies"][0]["name"] == "SID"


@pytest.mark.asyncio
async def test_set_cookie(tmp_path):
    cdp = _FakeCDP()
    sess = _sess(cdp, tmp_path)
    result = await sess.set_cookie(
        name="X", value="1", domain="example.com", path="/", secure=True
    )
    assert result["ok"] is True
    sent = next(p for m, p in cdp.sent if m == "Network.setCookie")
    assert sent["name"] == "X"
    assert sent["domain"] == "example.com"
    assert sent["secure"] is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest MCPs/browser-mcp/tests/test_tool_cookies.py -v
```
Expected: FAIL.

- [ ] **Step 3: Add cookie methods**

```python
    async def cookies(self, urls: list[str] | None = None) -> dict:
        err = self._require_attached()
        if err:
            return err
        params = {"urls": urls} if urls else {}
        resp = await self._cdp.send("Network.getCookies", params)
        return ok_envelope({"cookies": resp.get("cookies", [])})

    async def set_cookie(
        self,
        *,
        name: str,
        value: str,
        domain: str,
        path: str = "/",
        secure: bool = False,
        http_only: bool = False,
        same_site: str | None = None,
    ) -> dict:
        err = self._require_attached()
        if err:
            return err
        params = {
            "name": name,
            "value": value,
            "domain": domain,
            "path": path,
            "secure": secure,
            "httpOnly": http_only,
        }
        if same_site:
            params["sameSite"] = same_site
        resp = await self._cdp.send("Network.setCookie", params)
        if not resp.get("success", False):
            return error_envelope(ErrorCode.INTERNAL, "setCookie returned success=false")
        return ok_envelope({"set": True})
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest MCPs/browser-mcp/tests/test_tool_cookies.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add MCPs/browser-mcp/browser_mcp/tools.py MCPs/browser-mcp/tests/test_tool_cookies.py
git commit -m "feat(browser-mcp): cookies + set_cookie tools"
```

---

### Task 17: `browser_network_log` tool

**Files:**
- Modify: `MCPs/browser-mcp/browser_mcp/tools.py`
- Create: `MCPs/browser-mcp/tests/test_tool_network_log.py`

- [ ] **Step 1: Write the failing test**

`MCPs/browser-mcp/tests/test_tool_network_log.py`:
```python
import pytest

from browser_mcp.tools import BrowserSession


def _sess(tmp_path):
    s = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    s._cdp = object()  # just need a truthy value; network_log doesn't call send
    s._proc = type("P", (), {"poll": lambda self: None})()
    return s


def test_network_log_returns_entries_since_seq(tmp_path):
    sess = _sess(tmp_path)
    # simulate events
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest MCPs/browser-mcp/tests/test_tool_network_log.py -v
```
Expected: FAIL.

- [ ] **Step 3: Add `network_log` method**

```python
    def network_log(self, since_seq: int = 0) -> dict:
        err = self._require_attached()
        if err:
            return err
        events = [e for e in self._network_log if e["seq"] > since_seq]
        return ok_envelope({"events": events, "next_seq": self._network_seq})
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest MCPs/browser-mcp/tests/test_tool_network_log.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add MCPs/browser-mcp/browser_mcp/tools.py MCPs/browser-mcp/tests/test_tool_network_log.py
git commit -m "feat(browser-mcp): network_log tool returning events since seq"
```

---

### Task 18: `browser_close` tool (explicit coverage)

**Files:**
- Create: `MCPs/browser-mcp/tests/test_tool_close.py`

- [ ] **Step 1: Write the test**

`MCPs/browser-mcp/tests/test_tool_close.py`:
```python
import pytest

from browser_mcp.tools import BrowserSession


class _FakeProc:
    def __init__(self):
        self.terminated = False
        self.killed = False
        self._alive = True

    def poll(self):
        return None if self._alive else 0

    def terminate(self):
        self.terminated = True
        self._alive = False

    def kill(self):
        self.killed = True
        self._alive = False

    def wait(self, timeout=None):
        self._alive = False


class _FakeCM:
    def __init__(self):
        self.exited = False

    async def __aexit__(self, *a):
        self.exited = True


@pytest.mark.asyncio
async def test_close_is_idempotent(tmp_path):
    sess = BrowserSession(
        chrome_candidates=[], cdp_port=9222, default_proxy=None,
        user_data_dir_root=str(tmp_path),
    )
    sess._proc = _FakeProc()
    cm = _FakeCM()
    sess._cdp_cm = cm
    sess._cdp = object()

    r1 = await sess.close()
    assert r1["ok"] is True
    assert cm.exited is True
    assert sess._proc is None
    # second close should still succeed with no errors
    r2 = await sess.close()
    assert r2["ok"] is True
```

- [ ] **Step 2: Run test**

```bash
pytest MCPs/browser-mcp/tests/test_tool_close.py -v
```
Expected: PASS (close was already implemented in Task 8).

- [ ] **Step 3: Commit**

```bash
git add MCPs/browser-mcp/tests/test_tool_close.py
git commit -m "test(browser-mcp): close is idempotent"
```

---

### Task 19: MCP server entry point + integration smoke + config example

**Files:**
- Modify: `MCPs/browser-mcp/browser_mcp/server.py`
- Create: `claude_config.example.json`
- Create: `MCPs/browser-mcp/README.md`

- [ ] **Step 1: Implement `server.py` using the `mcp` Python SDK**

```python
"""browser-mcp stdio server: registers tools and dispatches to BrowserSession."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from common.config import load_config
from common.logging import setup_logger

from .tools import BrowserSession


WORKSPACE = Path(__file__).resolve().parents[3]  # /home/kali/Web-MCP


def _tool_schemas() -> list[Tool]:
    return [
        Tool(
            name="browser_launch",
            description="Launch Chrome attached to CDP. Use before other browser_* tools.",
            inputSchema={
                "type": "object",
                "properties": {
                    "headless": {"type": "boolean"},
                    "proxy": {"type": ["string", "null"], "description": "host:port or null for config default"},
                },
            },
        ),
        Tool(name="browser_close", description="Close the browser session.", inputSchema={"type": "object"}),
        Tool(
            name="browser_navigate",
            description="Navigate the current tab to a URL and wait for load event.",
            inputSchema={"type": "object", "required": ["url"], "properties": {"url": {"type": "string"}}},
        ),
        Tool(name="browser_snapshot", description="DOM + accessibility tree snapshot.", inputSchema={"type": "object"}),
        Tool(
            name="browser_query",
            description="Return outerHTML of the first element matching a CSS selector.",
            inputSchema={"type": "object", "required": ["selector"], "properties": {"selector": {"type": "string"}}},
        ),
        Tool(
            name="browser_click",
            description="Click the first element matching a CSS selector (uses box-model centroid).",
            inputSchema={"type": "object", "required": ["selector"], "properties": {"selector": {"type": "string"}}},
        ),
        Tool(
            name="browser_fill",
            description="Focus an input and insert text.",
            inputSchema={
                "type": "object",
                "required": ["selector", "text"],
                "properties": {"selector": {"type": "string"}, "text": {"type": "string"}},
            },
        ),
        Tool(
            name="browser_eval",
            description="Evaluate a JavaScript expression in the page context.",
            inputSchema={"type": "object", "required": ["expression"], "properties": {"expression": {"type": "string"}}},
        ),
        Tool(
            name="browser_screenshot",
            description="Capture a PNG screenshot (base64 in response).",
            inputSchema={"type": "object", "properties": {"full_page": {"type": "boolean"}}},
        ),
        Tool(
            name="browser_cookies",
            description="List cookies (optionally scoped to URLs).",
            inputSchema={"type": "object", "properties": {"urls": {"type": "array", "items": {"type": "string"}}}},
        ),
        Tool(
            name="browser_set_cookie",
            description="Set a cookie.",
            inputSchema={
                "type": "object",
                "required": ["name", "value", "domain"],
                "properties": {
                    "name": {"type": "string"}, "value": {"type": "string"}, "domain": {"type": "string"},
                    "path": {"type": "string"}, "secure": {"type": "boolean"}, "http_only": {"type": "boolean"},
                    "same_site": {"type": "string", "enum": ["Strict", "Lax", "None"]},
                },
            },
        ),
        Tool(
            name="browser_network_log",
            description="Return Network.* CDP events captured since a sequence number.",
            inputSchema={"type": "object", "properties": {"since_seq": {"type": "integer"}}},
        ),
    ]


async def _async_main() -> None:
    cfg = load_config(WORKSPACE / "config.toml")
    logger = setup_logger("browser-mcp", log_dir=WORKSPACE / cfg.logging.dir, level=cfg.logging.level)
    logger.info("startup", extra={"cfg": str(cfg.source)})

    session = BrowserSession(
        chrome_candidates=cfg.browser.chrome_candidates,
        cdp_port=cfg.browser.cdp_port,
        default_proxy=cfg.browser.default_proxy,
        user_data_dir_root="/tmp",
        navigation_timeout_s=cfg.browser.navigation_timeout_s,
    )

    server = Server("browser-mcp")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return _tool_schemas()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            if name == "browser_launch":
                result = await session.launch(
                    headless=bool(arguments.get("headless", cfg.browser.headless)),
                    proxy=arguments.get("proxy"),
                )
            elif name == "browser_close":
                result = await session.close()
            elif name == "browser_navigate":
                result = await session.navigate(arguments["url"])
            elif name == "browser_snapshot":
                result = await session.snapshot()
            elif name == "browser_query":
                result = await session.query(arguments["selector"])
            elif name == "browser_click":
                result = await session.click(arguments["selector"])
            elif name == "browser_fill":
                result = await session.fill(arguments["selector"], arguments["text"])
            elif name == "browser_eval":
                result = await session.eval_js(arguments["expression"])
            elif name == "browser_screenshot":
                result = await session.screenshot(full_page=bool(arguments.get("full_page", False)))
            elif name == "browser_cookies":
                result = await session.cookies(urls=arguments.get("urls"))
            elif name == "browser_set_cookie":
                result = await session.set_cookie(
                    name=arguments["name"], value=arguments["value"], domain=arguments["domain"],
                    path=arguments.get("path", "/"),
                    secure=bool(arguments.get("secure", False)),
                    http_only=bool(arguments.get("http_only", False)),
                    same_site=arguments.get("same_site"),
                )
            elif name == "browser_network_log":
                result = session.network_log(since_seq=int(arguments.get("since_seq", 0)))
            else:
                from common.mcp_base import ErrorCode, error_envelope
                result = error_envelope(ErrorCode.BAD_INPUT, f"unknown tool: {name}")
        except Exception as e:
            logger.exception("tool crashed", extra={"tool": name})
            from common.mcp_base import ErrorCode, error_envelope
            result = error_envelope(ErrorCode.INTERNAL, f"{type(e).__name__}: {e}")
        return [TextContent(type="text", text=json.dumps(result))]

    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write `claude_config.example.json`**

`/home/kali/Web-MCP/claude_config.example.json`:
```json
{
  "mcpServers": {
    "browser-mcp": {
      "command": "/home/kali/Web-MCP/.venv/bin/python",
      "args": ["-m", "browser_mcp.server"]
    }
  }
}
```

- [ ] **Step 3: Write per-MCP README**

`MCPs/browser-mcp/README.md`:
```markdown
# browser-mcp

CDP-driven browser MCP. Launches Chrome, attaches via `--remote-debugging-port`, exposes navigation, DOM query, click, fill, JS eval, screenshot, cookies, and network log as MCP tools.

## Tools
- `browser_launch(headless?, proxy?)` — Start Chrome (idempotent).
- `browser_close()` — Terminate Chrome.
- `browser_navigate(url)` — Load URL and wait for `Page.loadEventFired`.
- `browser_snapshot()` — DOM + accessibility tree.
- `browser_query(selector)` — First match → outerHTML.
- `browser_click(selector)` / `browser_fill(selector, text)` — Interaction.
- `browser_eval(expression)` — JS eval.
- `browser_screenshot(full_page?)` — PNG base64.
- `browser_cookies(urls?)` / `browser_set_cookie(name, value, domain, ...)` — Cookies.
- `browser_network_log(since_seq?)` — Captured CDP `Network.*` events.

## Smoke test
```bash
# In one terminal: Claude Code registered with browser-mcp
# Ask: "browser_launch then browser_navigate to https://example.com and screenshot"
# Then check logs/browser-mcp.log for structured startup line.
```
```

- [ ] **Step 4: Run full unit test suite**

```bash
cd /home/kali/Web-MCP
source .venv/bin/activate
pytest -v
```
Expected: all tests pass.

- [ ] **Step 5: Manual CDP smoke test (OPTIONAL; requires Chromium)**

Verify the entry point actually starts Chrome and accepts `browser_launch` via MCP:
```bash
# From another shell, ensure chromium is installed
which chromium || sudo apt-get install -y chromium

# Run the server directly and send a minimal initialize + tools/call over stdio.
# Simpler: register with Claude Code via claude_config.example.json, then in Claude:
#   "run browser_launch with headless=true, then navigate to https://httpbin.org/get, then close"
```
Expected in `logs/browser-mcp.log`: structured startup line, a `Page.navigate` call, and a `closed: true` result.

- [ ] **Step 6: Commit**

```bash
git add MCPs/browser-mcp/browser_mcp/server.py claude_config.example.json MCPs/browser-mcp/README.md
git commit -m "feat(browser-mcp): stdio MCP server entry point wiring all tools"
```

---

## Plan-end verification

- [ ] All tests pass: `pytest -v`
- [ ] `python -m browser_mcp.server` starts (kill with Ctrl-C; stdio waits for JSON-RPC from a client)
- [ ] Claude Code `/mcp` lists `browser-mcp` as connected after registering the example config
- [ ] Manual prompt "launch browser headless, navigate to example.com, screenshot, close" succeeds end-to-end
