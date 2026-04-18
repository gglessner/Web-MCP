# Workhorse Tools (Cycle B) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Project note:** Git commits are **disabled** for this project per user instruction. Each task ends with a regression run instead of a commit. Do not run `git add` / `git commit`.

**Goal:** Add `burp_http_send`, `burp_save_request`, `browser_wait_for`, `browser_get_response_body`, and `save_to=` evidence persistence so the `testing-*` skill library has a real probe→response→capture loop.

**Architecture:** A new shared `common/evidence.py` provides traversal-guarded file writes under a config-driven `evidence/` dir. browser-mcp gains two tools and an extended `screenshot`. burp-mcp gains a new Kotlin `/http/send` bridge route plus two Python tools. Three skill files are updated to document the new tools.

**Tech Stack:** Python 3.13 · `mcp` SDK · `httpx` · `websockets` · pytest + pytest-asyncio + respx · Kotlin/JVM 17 + Montoya API + Gradle · Flask (test fixture).

**Spec:** `docs/superpowers/specs/2026-04-17-workhorse-tools-design.md`

**Working dir for all commands:** `/home/kali/Web-MCP` with `.venv` activated (`source .venv/bin/activate`).

---

## Task 1: Add `[evidence]` config section + `EvidenceConfig` dataclass

**Files:**
- Modify: `config.toml`
- Modify: `.gitignore`
- Modify: `common/config.py`
- Modify: `tests/test_common_config.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_common_config.py`:

```python
def test_load_config_reads_evidence_section(tmp_path: Path):
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
        level = "INFO"
        dir = "logs"
        [evidence]
        dir = "evidence"
        """
    )
    cfg = load_config(cfg_file)
    assert cfg.evidence.dir == "evidence"


def test_load_config_missing_evidence_raises(tmp_path: Path):
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
        level = "INFO"
        dir = "logs"
        """
    )
    with pytest.raises(ValueError, match="invalid config"):
        load_config(cfg_file)
```

Also add `[evidence]\ndir = "evidence"` to the TOML literals in the **three existing tests** in this file (`test_load_config_reads_toml`, `test_load_config_local_override`, `test_load_config_raises_valueerror_on_malformed_section`) so they don't start failing once the section is required.

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_common_config.py -v`
Expected: `test_load_config_reads_evidence_section` FAILS with `AttributeError: 'Config' object has no attribute 'evidence'` (or `ValueError`).

- [ ] **Step 3: Implement**

In `common/config.py`, add after `LoggingConfig`:

```python
@dataclass
class EvidenceConfig:
    dir: str
```

Add `evidence: EvidenceConfig` to the `Config` dataclass (before `source: Path`).

In `load_config()`, change the `return Config(...)` to include:

```python
        return Config(
            burp=BurpConfig(**data["burp"]),
            browser=BrowserConfig(**data["browser"]),
            logging=LoggingConfig(**data["logging"]),
            evidence=EvidenceConfig(**data["evidence"]),
            source=path,
        )
```

Append to `config.toml`:

```toml

[evidence]
dir = "evidence"
```

Append to `.gitignore`:

```
# Per-engagement evidence captures
evidence/
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_common_config.py -v`
Expected: all PASS (8 tests).

- [ ] **Step 5: Regression check**

Run: `pytest -q`
Expected: all existing tests still pass.

---

## Task 2: `common/evidence.py` — path guard + writer

**Files:**
- Create: `common/evidence.py`
- Create: `tests/test_common_evidence.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_common_evidence.py`:

```python
from pathlib import Path

import pytest

from common.evidence import EvidencePathError, resolve_evidence_path, write_evidence


def test_resolve_happy_path(tmp_path: Path):
    root = tmp_path / "evidence"
    p = resolve_evidence_path(root, "F-001/shot.png")
    assert p == (root / "F-001" / "shot.png").resolve()
    assert p.parent.exists()


def test_resolve_rejects_absolute(tmp_path: Path):
    root = tmp_path / "evidence"
    with pytest.raises(EvidencePathError):
        resolve_evidence_path(root, "/etc/passwd")


def test_resolve_rejects_dotdot_escape(tmp_path: Path):
    root = tmp_path / "evidence"
    with pytest.raises(EvidencePathError):
        resolve_evidence_path(root, "../outside.txt")


def test_resolve_rejects_symlink_escape(tmp_path: Path):
    root = tmp_path / "evidence"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "link").symlink_to(outside)
    with pytest.raises(EvidencePathError):
        resolve_evidence_path(root, "link/x.txt")


def test_write_evidence_writes_bytes(tmp_path: Path):
    root = tmp_path / "evidence"
    p = write_evidence(root, "F-001/req.http", b"GET / HTTP/1.1\r\n\r\n")
    assert p.read_bytes() == b"GET / HTTP/1.1\r\n\r\n"
    assert p.is_relative_to(root.resolve())


def test_write_evidence_atomic_no_partial_on_resolve_error(tmp_path: Path):
    root = tmp_path / "evidence"
    with pytest.raises(EvidencePathError):
        write_evidence(root, "../x", b"data")
    assert not (tmp_path / "x").exists()
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_common_evidence.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'common.evidence'`.

- [ ] **Step 3: Implement**

Create `common/evidence.py`:

```python
"""Traversal-guarded evidence-file writer shared by browser-mcp and burp-mcp."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


class EvidencePathError(ValueError):
    """save_to is absolute or escapes the configured evidence dir."""


def resolve_evidence_path(evidence_root: Path, rel: str) -> Path:
    if os.path.isabs(rel):
        raise EvidencePathError(f"save_to must be relative, got absolute: {rel!r}")
    root = Path(evidence_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    p = (root / rel).resolve()
    if not p.is_relative_to(root):
        raise EvidencePathError(
            f"save_to escapes evidence dir {root}: {rel!r}"
        )
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def write_evidence(evidence_root: Path, rel: str, data: bytes) -> Path:
    p = resolve_evidence_path(evidence_root, rel)
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".evidence-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp, p)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return p
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_common_evidence.py -v`
Expected: 6 PASS.

- [ ] **Step 5: Regression check**

Run: `pytest -q`
Expected: all pass.

---

## Task 3: Thread `evidence_root` into `BrowserSession` + `screenshot(save_to=)`

**Files:**
- Modify: `MCPs/browser-mcp/browser_mcp/tools.py`
- Modify: `MCPs/browser-mcp/tests/test_tool_screenshot.py`

- [ ] **Step 1: Write failing tests**

Append to `MCPs/browser-mcp/tests/test_tool_screenshot.py`:

```python
@pytest.mark.asyncio
async def test_screenshot_save_to_writes_file_and_omits_base64(tmp_path):
    evidence_root = tmp_path / "evidence"
    sess = _sess(_FakeCDP(), tmp_path)
    sess._evidence_root = evidence_root
    result = await sess.screenshot(full_page=False, save_to="F-001/shot.png")
    assert result["ok"] is True
    assert "base64" not in result["data"]
    assert result["data"]["saved"].endswith("F-001/shot.png")
    written = evidence_root / "F-001" / "shot.png"
    assert written.exists()
    assert written.read_bytes().startswith(b"\x89PNG")


@pytest.mark.asyncio
async def test_screenshot_save_to_traversal_rejected(tmp_path):
    sess = _sess(_FakeCDP(), tmp_path)
    sess._evidence_root = tmp_path / "evidence"
    result = await sess.screenshot(save_to="../escape.png")
    assert result["ok"] is False
    assert result["error"]["code"] == "BAD_INPUT"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest MCPs/browser-mcp/tests/test_tool_screenshot.py -v`
Expected: new tests FAIL (`TypeError: screenshot() got an unexpected keyword argument 'save_to'`).

- [ ] **Step 3: Implement**

In `MCPs/browser-mcp/browser_mcp/tools.py`:

Add imports at top:

```python
from pathlib import Path
from common.evidence import EvidencePathError, write_evidence
```

In `BrowserSession.__init__`, add parameter `evidence_root: Path | None = None,` and store `self._evidence_root = evidence_root`.

Replace the `screenshot` method:

```python
    async def screenshot(self, *, full_page: bool = False,
                         save_to: str | None = None) -> dict:
        err = self._require_attached()
        if err:
            return err
        params = {"format": "png", "captureBeyondViewport": full_page}
        resp = await self._cdp.send("Page.captureScreenshot", params)
        b64 = resp.get("data", "")
        if save_to:
            if self._evidence_root is None:
                return error_envelope(ErrorCode.INTERNAL, "evidence_root not configured")
            try:
                png = base64.b64decode(b64)
                path = write_evidence(self._evidence_root, save_to, png)
            except EvidencePathError as e:
                return error_envelope(ErrorCode.BAD_INPUT, str(e))
            rel = str(path.relative_to(Path(self._evidence_root).resolve().parent))
            return ok_envelope({"format": "png", "bytes": len(png), "saved": rel})
        return ok_envelope({"format": "png", "base64": b64})
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest MCPs/browser-mcp/tests/test_tool_screenshot.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Regression check**

Run: `pytest -q`
Expected: all pass.

---

## Task 4: `browser_wait_for(selector, timeout_s, state)`

**Files:**
- Modify: `MCPs/browser-mcp/browser_mcp/tools.py`
- Create: `MCPs/browser-mcp/tests/test_tool_wait_for.py`

- [ ] **Step 1: Write failing tests**

Create `MCPs/browser-mcp/tests/test_tool_wait_for.py`:

```python
import pytest

from browser_mcp.tools import BrowserSession


class _FakeCDP:
    def __init__(self, node_ids: list[int], has_box: bool = True):
        self._node_ids = list(node_ids)
        self._has_box = has_box
        self.sent = []

    async def send(self, method, params=None):
        self.sent.append((method, params))
        if method == "DOM.getDocument":
            return {"root": {"nodeId": 1}}
        if method == "DOM.querySelector":
            nid = self._node_ids.pop(0) if self._node_ids else 0
            return {"nodeId": nid}
        if method == "DOM.getBoxModel":
            if self._has_box:
                return {"model": {"content": [0, 0, 1, 0, 1, 1, 0, 1]}}
            raise RuntimeError("No box model")
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
async def test_wait_for_attached_eventually(tmp_path):
    sess = _sess(_FakeCDP(node_ids=[0, 0, 42]), tmp_path)
    result = await sess.wait_for("#x", timeout_s=2.0, state="attached")
    assert result["ok"] is True
    assert result["data"]["nodeId"] == 42


@pytest.mark.asyncio
async def test_wait_for_timeout(tmp_path):
    sess = _sess(_FakeCDP(node_ids=[]), tmp_path)
    result = await sess.wait_for("#nope", timeout_s=0.3)
    assert result["ok"] is False
    assert result["error"]["code"] == "TIMEOUT"
    assert result["error"]["detail"]["selector"] == "#nope"


@pytest.mark.asyncio
async def test_wait_for_visible_requires_box_model(tmp_path):
    sess = _sess(_FakeCDP(node_ids=[42, 42], has_box=False), tmp_path)
    result = await sess.wait_for("#x", timeout_s=0.3, state="visible")
    assert result["ok"] is False
    assert result["error"]["code"] == "TIMEOUT"


@pytest.mark.asyncio
async def test_wait_for_requires_attached_session(tmp_path):
    s = BrowserSession(chrome_candidates=[], cdp_port=9222, default_proxy=None,
                       user_data_dir_root=str(tmp_path))
    result = await s.wait_for("#x")
    assert result["error"]["code"] == "TARGET_NOT_ATTACHED"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest MCPs/browser-mcp/tests/test_tool_wait_for.py -v`
Expected: FAIL — `AttributeError: 'BrowserSession' object has no attribute 'wait_for'`.

- [ ] **Step 3: Implement**

In `MCPs/browser-mcp/browser_mcp/tools.py`, add after the `navigate` method:

```python
    async def wait_for(self, selector: str, *, timeout_s: float = 10.0,
                       state: str = "attached") -> dict:
        err = self._require_attached()
        if err:
            return err
        if state not in ("attached", "visible"):
            return error_envelope(ErrorCode.BAD_INPUT,
                                  f"state must be 'attached' or 'visible', got {state!r}")
        deadline = time.monotonic() + timeout_s
        interval = 0.1
        while time.monotonic() < deadline:
            root = await self._root_node_id()
            found = await self._cdp.send(
                "DOM.querySelector", {"nodeId": root, "selector": selector}
            )
            node_id = found.get("nodeId", 0)
            if node_id:
                if state == "attached":
                    return ok_envelope({"nodeId": node_id, "selector": selector})
                try:
                    await self._cdp.send("DOM.getBoxModel", {"nodeId": node_id})
                    return ok_envelope({"nodeId": node_id, "selector": selector})
                except Exception:
                    pass
            await asyncio.sleep(interval)
            interval = min(interval * 1.5, 0.5)
        return error_envelope(
            ErrorCode.TIMEOUT,
            f"selector not {state} within {timeout_s}s",
            detail={"selector": selector},
        )
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest MCPs/browser-mcp/tests/test_tool_wait_for.py -v`
Expected: 4 PASS.

- [ ] **Step 5: Regression check**

Run: `pytest -q`
Expected: all pass.

---

## Task 5: `browser_get_response_body(request_id)`

**Files:**
- Modify: `MCPs/browser-mcp/browser_mcp/tools.py`
- Create: `MCPs/browser-mcp/tests/test_tool_response_body.py`

- [ ] **Step 1: Write failing tests**

Create `MCPs/browser-mcp/tests/test_tool_response_body.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest MCPs/browser-mcp/tests/test_tool_response_body.py -v`
Expected: FAIL — `AttributeError: 'BrowserSession' object has no attribute 'get_response_body'`.

- [ ] **Step 3: Implement**

In `MCPs/browser-mcp/browser_mcp/tools.py`, add `from common.cdp import CDPError` to the existing `from common.cdp import ...` line, then add after `network_log`:

```python
    async def get_response_body(self, request_id: str) -> dict:
        err = self._require_attached()
        if err:
            return err
        try:
            resp = await self._cdp.send(
                "Network.getResponseBody", {"requestId": request_id}
            )
        except CDPError as e:
            return error_envelope(
                ErrorCode.BAD_INPUT,
                f"response body unavailable for requestId={request_id}: {e}",
                detail={"hint": "body is only retrievable while the originating page is loaded"},
            )
        body = resp.get("body", "")
        return ok_envelope({
            "request_id": request_id,
            "base64_encoded": resp.get("base64Encoded", False),
            "body": body,
            "length": len(body),
        })
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest MCPs/browser-mcp/tests/test_tool_response_body.py -v`
Expected: 2 PASS.

- [ ] **Step 5: Regression check**

Run: `pytest -q`
Expected: all pass.

---

## Task 6: Register new browser-mcp tools in `server.py`

**Files:**
- Modify: `MCPs/browser-mcp/browser_mcp/server.py`

- [ ] **Step 1: Edit `_tool_schemas()`**

Add two new `Tool(...)` entries and extend `browser_screenshot`:

```python
        Tool(
            name="browser_wait_for",
            description="Poll until a CSS selector is attached (or visible) in the DOM, or time out.",
            inputSchema={"type": "object", "required": ["selector"], "properties": {
                "selector": {"type": "string"},
                "timeout_s": {"type": "number"},
                "state": {"type": "string", "enum": ["attached", "visible"]},
            }},
        ),
        Tool(
            name="browser_get_response_body",
            description=("Return the response body for a CDP Network requestId from "
                         "browser_network_log. Only works while the page that made the "
                         "request is still loaded."),
            inputSchema={"type": "object", "required": ["request_id"],
                         "properties": {"request_id": {"type": "string"}}},
        ),
```

Change the existing `browser_screenshot` entry's `inputSchema` to:

```python
            inputSchema={"type": "object", "properties": {
                "full_page": {"type": "boolean"},
                "save_to": {"type": "string",
                            "description": "relative path under evidence/, e.g. 'F-001/shot.png'"},
            }},
```

- [ ] **Step 2: Wire `evidence_root` into `BrowserSession`**

In `_async_main()`, change the `session = BrowserSession(...)` call to add:

```python
        evidence_root=WORKSPACE / cfg.evidence.dir,
```

- [ ] **Step 3: Add dispatch branches in `call_tool()`**

After the `browser_navigate` branch:

```python
            elif name == "browser_wait_for":
                result = await session.wait_for(
                    arguments["selector"],
                    timeout_s=float(arguments.get("timeout_s", 10.0)),
                    state=arguments.get("state", "attached"),
                )
            elif name == "browser_get_response_body":
                result = await session.get_response_body(arguments["request_id"])
```

Change the `browser_screenshot` branch to:

```python
            elif name == "browser_screenshot":
                result = await session.screenshot(
                    full_page=bool(arguments.get("full_page", False)),
                    save_to=arguments.get("save_to"),
                )
```

- [ ] **Step 4: Import-smoke verification**

Run: `python -c "import browser_mcp.server"`
Expected: no traceback.

- [ ] **Step 5: Regression check**

Run: `pytest -q`
Expected: all pass.

---

## Task 7: Kotlin `/http/send` route

**Files:**
- Create: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/HttpSendRoutes.kt`
- Modify: `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/HttpBridgeServer.kt`
- Modify: `MCPs/burp-mcp/burp-ext/src/test/kotlin/webmcp/RoutesTest.kt`

- [ ] **Step 1: Write failing Kotlin test**

In `RoutesTest.kt`, add inside `class RoutesTest`:

```kotlin
    @Test
    fun `http send route registered and validates body`() {
        val router = Router(api = FakeApi())
        registerHttpSendRoutes(router)
        val r = router.dispatch("POST", "/http/send", emptyMap(), "{}")
        assertEquals(400, r.status)
        assertTrue(r.body().contains("BAD_INPUT"))
    }
```

- [ ] **Step 2: Run tests to verify failure**

Run: `(cd MCPs/burp-mcp/burp-ext && ./gradlew test)`
Expected: compile error — `Unresolved reference: registerHttpSendRoutes`.

- [ ] **Step 3: Implement route**

Create `MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/HttpSendRoutes.kt`:

```kotlin
package webmcp

import burp.api.montoya.core.ByteArray as MByteArray
import burp.api.montoya.http.HttpService
import burp.api.montoya.http.message.requests.HttpRequest
import java.util.Base64

private fun badInput(msg: String) = mapOf(
    "ok" to false, "error" to mapOf("code" to "BAD_INPUT", "message" to msg)
)

fun registerHttpSendRoutes(router: Router) {
    router.register("POST", "/http/send") { ctx ->
        val body = ctx.bodyJson
            ?: return@register Response(400, badInput("JSON body required"))
        val rawB64 = body["raw_base64"] as? String
        val host = body["host"] as? String
        val port = (body["port"] as? Number)?.toInt()
        val secure = body["secure"] as? Boolean ?: true
        if (rawB64 == null || host == null || port == null) {
            return@register Response(400, badInput("raw_base64, host, port required"))
        }
        val rawBytes = Base64.getDecoder().decode(rawB64)
        val service = HttpService.httpService(host, port, secure)
        val req = HttpRequest.httpRequest(service, MByteArray.byteArray(*rawBytes))
        val t0 = System.nanoTime()
        val rr = ctx.api.http().sendRequest(req)
        val ms = (System.nanoTime() - t0) / 1_000_000
        val resp = rr.response()
        Response(200, mapOf(
            "ok" to true,
            "data" to mapOf(
                "status" to resp?.statusCode()?.toInt(),
                "headers" to resp?.headers()?.map {
                    mapOf("name" to it.name(), "value" to it.value())
                },
                "body_base64" to resp?.body()?.let {
                    Base64.getEncoder().encodeToString(it.bytes)
                },
                "body_len" to (resp?.body()?.length() ?: 0),
                "request_base64" to Base64.getEncoder()
                    .encodeToString(req.toByteArray().bytes),
                "time_ms" to ms,
            ),
        ))
    }
}
```

In `HttpBridgeServer.kt` `init` block, add after `registerMatchReplaceRoutes(router)`:

```kotlin
        registerHttpSendRoutes(router)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `(cd MCPs/burp-mcp/burp-ext && ./gradlew test)`
Expected: BUILD SUCCESSFUL, all tests pass. (The new test exercises only the BAD_INPUT path so `FakeApi.http()` is never called.)

- [ ] **Step 5: Build the jar**

Run: `(cd MCPs/burp-mcp/burp-ext && ./gradlew shadowJar)`
Expected: `BUILD SUCCESSFUL`, `build/libs/burp-mcp-bridge.jar` updated.

---

## Task 8: `BurpClient.http_send()`

**Files:**
- Modify: `common/burp_client.py`
- Modify: `tests/test_common_burp_client.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_common_burp_client.py`:

```python
@pytest.mark.asyncio
async def test_http_send_returns_data():
    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        mock.post("/http/send").mock(
            return_value=httpx.Response(200, json={
                "ok": True, "data": {
                    "status": 200, "headers": [{"name": "X", "value": "y"}],
                    "body_base64": "aGk=", "body_len": 2,
                    "request_base64": "R0VUIC8=", "time_ms": 5,
                }
            })
        )
        async with BurpClient("http://127.0.0.1:8775") as c:
            data = await c.http_send(raw_base64="R0VUIC8=", host="x", port=80, secure=False)
        assert data["status"] == 200
        assert data["body_len"] == 2
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_common_burp_client.py::test_http_send_returns_data -v`
Expected: FAIL — `AttributeError: 'BurpClient' object has no attribute 'http_send'`.

- [ ] **Step 3: Implement**

In `common/burp_client.py`, add after `meta()`:

```python
    async def http_send(
        self, *, raw_base64: str, host: str, port: int,
        secure: bool = True, timeout_ms: int = 30000,
    ) -> dict:
        return await self._request("POST", "/http/send", json={
            "raw_base64": raw_base64, "host": host, "port": port,
            "secure": secure, "timeout_ms": timeout_ms,
        })
```

- [ ] **Step 4: Run test to verify pass**

Run: `pytest tests/test_common_burp_client.py -v`
Expected: 5 PASS.

- [ ] **Step 5: Regression check**

Run: `pytest -q`
Expected: all pass.

---

## Task 9: `burp_http_send` tool handler

**Files:**
- Modify: `MCPs/burp-mcp/burp_mcp/tool_handlers.py`
- Create: `MCPs/burp-mcp/tests/test_http_send_handler.py`

- [ ] **Step 1: Write failing tests**

Create `MCPs/burp-mcp/tests/test_http_send_handler.py`:

```python
import base64
from pathlib import Path

import httpx
import pytest
import respx

from burp_mcp.tool_handlers import handle


BRIDGE = "http://127.0.0.1:8775"


def _bridge_response(body: bytes = b"<html>hello world</html>", status: int = 200):
    return httpx.Response(200, json={
        "ok": True, "data": {
            "status": status,
            "headers": [{"name": "Content-Type", "value": "text/html"}],
            "body_base64": base64.b64encode(body).decode(),
            "body_len": len(body),
            "request_base64": base64.b64encode(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n").decode(),
            "time_ms": 12,
        }
    })


@pytest.mark.asyncio
async def test_http_send_preview_truncates(tmp_path: Path):
    async with respx.mock(base_url=BRIDGE) as mock:
        mock.post("/http/send").mock(return_value=_bridge_response(body=b"A" * 9000))
        result = await handle("burp_http_send",
            {"raw_base64": "R0VUIC8=", "host": "x", "port": 80,
             "secure": False, "preview_bytes": 100},
            bridge_url=BRIDGE, evidence_root=tmp_path / "evidence")
    assert result["ok"] is True
    assert result["data"]["status"] == 200
    assert len(result["data"]["body_preview"]) == 100
    assert result["data"]["body_len"] == 9000
    assert "body_base64" not in result["data"]


@pytest.mark.asyncio
async def test_http_send_include_body(tmp_path: Path):
    async with respx.mock(base_url=BRIDGE) as mock:
        mock.post("/http/send").mock(return_value=_bridge_response())
        result = await handle("burp_http_send",
            {"raw_base64": "R0VUIC8=", "host": "x", "port": 80, "include_body": True},
            bridge_url=BRIDGE, evidence_root=tmp_path / "evidence")
    assert "body_base64" in result["data"]


@pytest.mark.asyncio
async def test_http_send_save_to_writes_two_files(tmp_path: Path):
    root = tmp_path / "evidence"
    async with respx.mock(base_url=BRIDGE) as mock:
        mock.post("/http/send").mock(return_value=_bridge_response())
        result = await handle("burp_http_send",
            {"raw_base64": "R0VUIC8=", "host": "x", "port": 80,
             "save_to": "F-001/probe"},
            bridge_url=BRIDGE, evidence_root=root)
    assert result["ok"] is True
    assert (root / "F-001" / "probe.request.http").exists()
    assert (root / "F-001" / "probe.response.http").exists()
    assert result["data"]["saved"]["request"].endswith("F-001/probe.request.http")


@pytest.mark.asyncio
async def test_http_send_save_to_traversal_rejected(tmp_path: Path):
    async with respx.mock(base_url=BRIDGE) as mock:
        mock.post("/http/send").mock(return_value=_bridge_response())
        result = await handle("burp_http_send",
            {"raw_base64": "R0VUIC8=", "host": "x", "port": 80, "save_to": "../escape"},
            bridge_url=BRIDGE, evidence_root=tmp_path / "evidence")
    assert result["ok"] is False
    assert result["error"]["code"] == "BAD_INPUT"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest MCPs/burp-mcp/tests/test_http_send_handler.py -v`
Expected: FAIL — `TypeError: handle() got an unexpected keyword argument 'evidence_root'`.

- [ ] **Step 3: Implement**

In `MCPs/burp-mcp/burp_mcp/tool_handlers.py`:

Add imports at top:

```python
import base64
from pathlib import Path

from common.evidence import EvidencePathError, write_evidence
```

Change the signature:

```python
async def handle(tool: str, args: dict, *, bridge_url: str,
                 evidence_root: Path | None = None) -> dict:
```

Add helper above `handle`:

```python
def _reconstruct_response(status: int | None, headers: list[dict] | None,
                          body: bytes) -> bytes:
    lines = [f"HTTP/1.1 {status if status is not None else 0}"]
    for h in headers or []:
        lines.append(f"{h.get('name')}: {h.get('value')}")
    head = ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8")
    return head + body
```

Inside the `try / async with BurpClient(...)` block, add before `return error_envelope(ErrorCode.BAD_INPUT, f"unknown tool: {tool}")`:

```python
            if tool == "burp_http_send":
                data = await c.http_send(
                    raw_base64=args["raw_base64"], host=args["host"],
                    port=int(args["port"]),
                    secure=bool(args.get("secure", True)),
                    timeout_ms=int(args.get("timeout_ms", 30000)),
                )
                body_b64 = data.get("body_base64") or ""
                body = base64.b64decode(body_b64) if body_b64 else b""
                preview_bytes = int(args.get("preview_bytes", 4096))
                preview = body[:preview_bytes].decode("utf-8", "replace")
                out: dict = {
                    "status": data.get("status"),
                    "time_ms": data.get("time_ms"),
                    "body_len": data.get("body_len", len(body)),
                    "headers": data.get("headers"),
                    "body_preview": preview,
                }
                if bool(args.get("include_body", False)):
                    out["body_base64"] = body_b64
                save_to = args.get("save_to")
                if save_to:
                    if evidence_root is None:
                        return error_envelope(ErrorCode.INTERNAL,
                                              "evidence_root not configured")
                    req_bytes = base64.b64decode(data.get("request_base64") or "")
                    resp_bytes = _reconstruct_response(
                        data.get("status"), data.get("headers"), body)
                    rp = write_evidence(evidence_root,
                                        f"{save_to}.request.http", req_bytes)
                    sp = write_evidence(evidence_root,
                                        f"{save_to}.response.http", resp_bytes)
                    root_parent = Path(evidence_root).resolve().parent
                    out["saved"] = {
                        "request": str(rp.relative_to(root_parent)),
                        "response": str(sp.relative_to(root_parent)),
                    }
                return ok_envelope(out)
```

Add a new `except` clause **before** `except Exception as e:`:

```python
    except EvidencePathError as e:
        return error_envelope(ErrorCode.BAD_INPUT, str(e))
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest MCPs/burp-mcp/tests/test_http_send_handler.py -v`
Expected: 4 PASS.

- [ ] **Step 5: Regression — fix existing handler tests**

The three existing test files in `MCPs/burp-mcp/tests/` call `handle(..., bridge_url=...)` without `evidence_root`. Since the new param defaults to `None`, they still pass unchanged. Verify:

Run: `pytest MCPs/burp-mcp/tests/ -v`
Expected: all PASS (existing 10 + new 4).

---

## Task 10: `burp_save_request` tool handler

**Files:**
- Modify: `MCPs/burp-mcp/burp_mcp/tool_handlers.py`
- Create: `MCPs/burp-mcp/tests/test_save_request_handler.py`

- [ ] **Step 1: Write failing tests**

Create `MCPs/burp-mcp/tests/test_save_request_handler.py`:

```python
import base64
from pathlib import Path

import httpx
import pytest
import respx

from burp_mcp.tool_handlers import handle

BRIDGE = "http://127.0.0.1:8775"


@pytest.mark.asyncio
async def test_save_request_writes_two_files(tmp_path: Path):
    root = tmp_path / "evidence"
    async with respx.mock(base_url=BRIDGE) as mock:
        mock.get("/proxy/request/12").mock(return_value=httpx.Response(200, json={
            "ok": True, "data": {
                "id": 12,
                "request": {"raw_base64": base64.b64encode(b"GET / HTTP/1.1\r\n\r\n").decode()},
                "response": {"status": 200,
                             "raw_base64": base64.b64encode(b"HTTP/1.1 200 OK\r\n\r\nhi").decode()},
            }
        }))
        result = await handle("burp_save_request",
            {"id": 12, "save_to": "F-001/baseline"},
            bridge_url=BRIDGE, evidence_root=root)
    assert result["ok"] is True
    assert (root / "F-001" / "baseline.request.http").read_bytes().startswith(b"GET /")
    assert (root / "F-001" / "baseline.response.http").read_bytes().startswith(b"HTTP/1.1")
    assert result["data"]["saved"]["response"].endswith("baseline.response.http")


@pytest.mark.asyncio
async def test_save_request_no_response_writes_request_only(tmp_path: Path):
    root = tmp_path / "evidence"
    async with respx.mock(base_url=BRIDGE) as mock:
        mock.get("/proxy/request/13").mock(return_value=httpx.Response(200, json={
            "ok": True, "data": {
                "id": 13,
                "request": {"raw_base64": base64.b64encode(b"GET / HTTP/1.1\r\n\r\n").decode()},
                "response": None,
            }
        }))
        result = await handle("burp_save_request",
            {"id": 13, "save_to": "F-002/noresp"},
            bridge_url=BRIDGE, evidence_root=root)
    assert result["ok"] is True
    assert (root / "F-002" / "noresp.request.http").exists()
    assert not (root / "F-002" / "noresp.response.http").exists()
    assert result["data"]["saved"]["response"] is None
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest MCPs/burp-mcp/tests/test_save_request_handler.py -v`
Expected: FAIL — `unknown tool: burp_save_request` envelope.

- [ ] **Step 3: Implement**

In `tool_handlers.py`, add after the `burp_http_send` block:

```python
            if tool == "burp_save_request":
                if evidence_root is None:
                    return error_envelope(ErrorCode.INTERNAL,
                                          "evidence_root not configured")
                save_to = args["save_to"]
                data = await c.proxy_request(int(args["id"]))
                req_b64 = (data.get("request") or {}).get("raw_base64") or ""
                rp = write_evidence(evidence_root,
                                    f"{save_to}.request.http",
                                    base64.b64decode(req_b64))
                root_parent = Path(evidence_root).resolve().parent
                saved: dict = {"request": str(rp.relative_to(root_parent)),
                               "response": None}
                resp = data.get("response")
                if resp and resp.get("raw_base64"):
                    sp = write_evidence(evidence_root,
                                        f"{save_to}.response.http",
                                        base64.b64decode(resp["raw_base64"]))
                    saved["response"] = str(sp.relative_to(root_parent))
                return ok_envelope({"saved": saved})
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest MCPs/burp-mcp/tests/test_save_request_handler.py -v`
Expected: 2 PASS.

- [ ] **Step 5: Regression check**

Run: `pytest -q`
Expected: all pass.

---

## Task 11: Register new burp-mcp tools in `server.py`

**Files:**
- Modify: `MCPs/burp-mcp/burp_mcp/server.py`

- [ ] **Step 1: Add tool schemas**

In `_tool_schemas()`, add after `burp_meta`:

```python
        Tool(
            name="burp_http_send",
            description=("Send a raw HTTP request through Burp and return the response "
                         "(status, headers, timing, body preview). Optional save_to "
                         "writes <stem>.request.http / <stem>.response.http under the "
                         "configured evidence dir."),
            inputSchema={"type": "object", "required": ["raw_base64", "host", "port"],
                         "properties": {
                "raw_base64": {"type": "string"}, "host": {"type": "string"},
                "port": {"type": "integer"}, "secure": {"type": "boolean"},
                "timeout_ms": {"type": "integer"},
                "preview_bytes": {"type": "integer"},
                "include_body": {"type": "boolean"},
                "save_to": {"type": "string",
                            "description": "relative path stem under evidence/, e.g. 'F-001/idor-probe'"},
            }},
        ),
        Tool(
            name="burp_save_request",
            description=("Write a proxy-history entry's raw request/response to "
                         "<stem>.request.http / <stem>.response.http under the evidence dir."),
            inputSchema={"type": "object", "required": ["id", "save_to"], "properties": {
                "id": {"type": "integer"}, "save_to": {"type": "string"},
            }},
        ),
```

- [ ] **Step 2: Thread `evidence_root` into `handle()`**

In `_async_main()`, after `cfg = load_config(...)`, add:

```python
    evidence_root = WORKSPACE / cfg.evidence.dir
```

Change the `call_tool` body:

```python
        result = await handle(name, arguments or {},
                              bridge_url=cfg.burp.bridge_url,
                              evidence_root=evidence_root)
```

- [ ] **Step 3: Import-smoke verification**

Run: `python -c "import burp_mcp.server"`
Expected: no traceback.

- [ ] **Step 4: Regression check**

Run: `pytest -q`
Expected: all pass.

---

## Task 12: Extend integration chain test with `burp_http_send`

**Files:**
- Modify: `tests/integration/test_chain_browser_burp.py`

- [ ] **Step 1: Add test function**

Append to the file:

```python
@pytest.mark.skipif(not _bridge_available(),
                    reason="burp-mcp-bridge not responding on 127.0.0.1:8775")
@pytest.mark.asyncio
async def test_burp_http_send_against_fixture(live_target: str, tmp_path):
    import base64
    from burp_mcp.tool_handlers import handle

    raw = (b"GET /echo?q=chain-probe HTTP/1.1\r\n"
           b"Host: 127.0.0.1:5055\r\nConnection: close\r\n\r\n")
    result = await handle(
        "burp_http_send",
        {"raw_base64": base64.b64encode(raw).decode(),
         "host": "127.0.0.1", "port": 5055, "secure": False},
        bridge_url="http://127.0.0.1:8775",
        evidence_root=tmp_path / "evidence",
    )
    assert result["ok"] is True, result
    assert result["data"]["status"] == 200
    assert "chain-probe" in result["data"]["body_preview"]
```

- [ ] **Step 2: Verify it skips without live Burp**

Run: `pytest tests/integration/test_chain_browser_burp.py -v -m integration`
Expected: SKIPPED (bridge not responding) — confirms no syntax errors. Full run requires live Burp (manual bring-up per `to-do.md`).

---

## Task 13: Update `mcp-burp` skill

**Files:**
- Modify: `.claude/skills/mcp-burp/SKILL.md`

- [ ] **Step 1: Insert `burp_http_send` as primary probe in Test steps**

Replace step 5 (the `echo -n ... | base64` Repeater pattern) with:

```markdown
5. Send a probe and read the response in one call:
   `burp_http_send(raw_base64=<b64>, host="target.example.com", port=443, secure=true, save_to="F-001/probe-1")`
   — returns `{status, headers, body_preview, body_len, time_ms, saved}`. Use this
   for all automated probing (boolean diffs, error-string detection, timing).
6. (Optional) Open the same request in the Burp UI for manual follow-up:
   `burp_repeater_send(raw_base64=<b64>, host=..., port=443, secure=true, tab_name="probe-1")`.
```

Renumber the remaining steps and add at the end:

```markdown
12. Persist a proxy-history entry as evidence:
    `burp_save_request(id=<N>, save_to="F-001/baseline")` — writes
    `evidence/F-001/baseline.request.http` and `.response.http`.
```

- [ ] **Step 2: Add Tool commands entries**

Insert after the `burp_meta()` example in `## Tool commands`:

```markdown
# Probe + capture in one call (workhorse)
burp_http_send(raw_base64="R0VUIC9hcGkvdXNlcnMgSFRUUC8xLjENCkhvc3Q6IHRhcmdldC5leGFtcGxlLmNvbQ0KDQo=",
               host="target.example.com", port=443, secure=true,
               preview_bytes=4096, save_to="F-001/idor-probe")
# Success: {"ok": true, "data": {"status": 200, "time_ms": 87, "body_len": 14302,
#   "headers": [...], "body_preview": "<!doctype html>...",
#   "saved": {"request": "evidence/F-001/idor-probe.request.http",
#             "response": "evidence/F-001/idor-probe.response.http"}}}
# Target unreachable: {"ok": true, "data": {"status": null, "body_len": 0, ...}}

# Persist an existing history entry
burp_save_request(id=12, save_to="F-001/baseline")
# Success: {"ok": true, "data": {"saved": {"request": "evidence/F-001/baseline.request.http",
#                                           "response": "evidence/F-001/baseline.response.http"}}}
```

- [ ] **Step 3: Fix `burp_scope_check` documented response shape**

Change the example to:

```markdown
burp_scope_check(urls=["https://target.example.com/admin"])
# Success: {"ok": true, "data": {"checks": {"https://target.example.com/admin": true}}}
```

- [ ] **Step 4: Conventions check**

Verify per `docs/skill-conventions.md`: `name` matches dir, `description` ≤180 chars, all 8 sections present, ≤400 lines, authorization note present.

---

## Task 14: Update `mcp-browser` skill

**Files:**
- Modify: `.claude/skills/mcp-browser/SKILL.md`

- [ ] **Step 1: Insert `browser_wait_for` and `browser_get_response_body` in Test steps**

After step 2 (`browser_navigate`), insert:

```markdown
3. `browser_wait_for(selector="<css-selector>", timeout_s=10, state="visible")` —
   for SPAs and async-rendered content, block until the element is in the DOM
   (and visible) before snapshotting or interacting.
```

Renumber remaining steps. After the `browser_network_log` step, insert:

```markdown
8. `browser_get_response_body(request_id="<id-from-network-log>")` — fetch the
   body of an XHR/fetch response. The `request_id` comes from
   `params.requestId` on `Network.responseReceived` events in
   `browser_network_log`. Only works while the page that made the request is
   still loaded.
```

- [ ] **Step 2: Update screenshot example to use `save_to`**

Replace the `browser_screenshot` example in `## Tool commands` with:

```markdown
# 8. Capture evidence to disk (no base64 in context)
browser_screenshot(full_page=true, save_to="F-001/login.png")
# Success: {"ok": true, "data": {"format": "png", "bytes": 48211,
#                                 "saved": "evidence/F-001/login.png"}}
# Omit save_to for inline base64 (legacy behaviour).
```

Add after the network-log example:

```markdown
# Read an XHR response body
browser_get_response_body(request_id="12345.67")
# Success: {"ok": true, "data": {"request_id": "12345.67", "base64_encoded": false,
#                                 "body": "{\"users\":[...]}", "length": 812}}
# Failure: {"ok": false, "error": {"code": "BAD_INPUT", "detail":
#           {"hint": "body is only retrievable while the originating page is loaded"}}}

# Wait for an SPA element
browser_wait_for(selector="div.results", timeout_s=10, state="visible")
# Success: {"ok": true, "data": {"nodeId": 42, "selector": "div.results"}}
# Failure: {"ok": false, "error": {"code": "TIMEOUT", "detail": {"selector": "div.results"}}}
```

- [ ] **Step 3: Conventions check**

Same checklist as Task 13 Step 4.

---

## Task 15: Update `methodology-evidence-capture` skill

**Files:**
- Modify: `.claude/skills/methodology-evidence-capture/SKILL.md`

- [ ] **Step 1: Replace Tool commands section**

Replace the bullet list in `## Tool commands` with:

```markdown
- `burp_http_send(raw_base64=<b64>, host=..., port=443, secure=true, save_to="F-001/probe")`
  — sends the probe **and** writes `evidence/F-001/probe.request.http` +
  `evidence/F-001/probe.response.http` in one call. The returned
  `body_preview` lets Claude diff without dumping the full body into context.
- `burp_save_request(id=12, save_to="F-001/baseline")` — persist an existing
  proxy-history entry as `.request.http` / `.response.http`.
- `browser_screenshot(full_page=true, save_to="F-001/screenshot.png")` — writes
  the PNG to disk; response contains the path and byte count, not the base64.
- `get_file_contents(repo_url="https://github.com/org/name", path="src/api/export.py", ref="<sha>")`
  — source-side evidence (unchanged).

The evidence root is `[evidence] dir` in `config.toml` (default `evidence/`,
gitignored). Set a per-engagement path in `config.local.toml`. `save_to` is
always **relative** to that root; absolute paths and `..` are rejected with
`BAD_INPUT`.
```

- [ ] **Step 2: Update Test steps**

Replace step 1 with:

```markdown
1. Persist the raw exchange: either
   `burp_http_send(..., save_to="F-NNN/<label>")` (for probes you send) or
   `burp_save_request(id=N, save_to="F-NNN/<label>")` (for history entries).
```

Replace step 2 with:

```markdown
2. Capture the rendered state:
   `browser_screenshot(full_page=true, save_to="F-NNN/<label>.png")`.
```

- [ ] **Step 3: Conventions check**

Same checklist as Task 13 Step 4.

---

## Task 16: README + to-do smoke-test additions

**Files:**
- Modify: `README.md`
- Modify: `to-do.md`

- [ ] **Step 1: README — Smoke-test checklist**

Add two checkboxes after the existing browser→Burp probe item:

```markdown
- [ ] `curl -s -X POST http://127.0.0.1:8775/http/send -H 'Content-Type: application/json' \
      -d '{"raw_base64":"R0VUIC9lY2hvP3E9aGkgSFRUUC8xLjENCkhvc3Q6IDEyNy4wLjAuMTo1MDU1DQpDb25uZWN0aW9uOiBjbG9zZQ0KDQo=","host":"127.0.0.1","port":5055,"secure":false}'`
      → `{"ok": true, "data": {"status": 200, ...}}` (fixture must be running).
- [ ] Claude Code prompt: *"Use burp_http_send to GET http://127.0.0.1:5055/echo?q=hello
      with save_to='smoke/echo', then list the evidence dir."* — `evidence/smoke/echo.request.http`
      and `.response.http` appear on disk.
```

- [ ] **Step 2: to-do.md — Manual bring-up**

Under `### 1. Build + load the Burp extension`, add:

```markdown
- [ ] After loading the rebuilt jar: `curl -s -X POST http://127.0.0.1:8775/http/send -H 'Content-Type: application/json' -d '{"raw_base64":"R0VUIC8gSFRUUC8xLjENCkhvc3Q6IGV4YW1wbGUuY29tDQoNCg==","host":"example.com","port":80,"secure":false}'` returns `{"ok": true, ...}` — confirms the new `/http/send` route.
```

- [ ] **Step 3: Full-suite final check**

Run: `pytest -q`
Expected: ≥79 passed (61 baseline + ~18 new), 0 failed. Integration tests SKIPPED unless Burp/Chrome live.

Run: `(cd MCPs/burp-mcp/burp-ext && ./gradlew test)`
Expected: BUILD SUCCESSFUL.

---

## Done criteria

- [ ] All 16 tasks' steps checked off.
- [ ] `pytest -q` ≥79 passed, 0 failed.
- [ ] `./gradlew test` + `./gradlew shadowJar` succeed in `burp-ext/`.
- [ ] `evidence/` gitignored; `save_to="../x"` returns `BAD_INPUT` with no file written.
- [ ] Three skill files pass `docs/skill-conventions.md` checklist.
- [ ] README + to-do updated.
- [ ] Manual smoke (requires live Burp + fixture): `/http/send` curl works; Claude prompt produces files under `evidence/smoke/`.
