# Hardening Pass (Cycle A) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use `- [ ]` checkboxes.
>
> **Project note:** Git commits are **disabled** for this project per user instruction. Each task ends with a regression run, not a commit. Do not run `git`.

**Goal:** Clear the bug-fix / code-quality backlog (18 items A1-A18) so own-code modules are type-tight, leak-free, dep-upgrade-safe, and operationally scriptable.

**Architecture:** No structural change. Each item is an isolated edit to one module + one test, or a new script/doc.

**Tech Stack:** Python 3.13 · pytest · ruff · Kotlin/JVM 17 + Gradle · bash.

**Spec:** `docs/superpowers/specs/2026-04-17-hardening-pass-design.md`

**Working dir:** `/home/kali/Web-MCP`. Run pytest via `.venv/bin/python -m pytest`.

---

## Task 1: A1+A2 — `common/cdp.py` asserts → RuntimeError + typing

**Files:** `common/cdp.py`, `tests/test_common_cdp.py`

- [ ] **Step 1: Write failing test** — append to `tests/test_common_cdp.py`:
```python
@pytest.mark.asyncio
async def test_send_on_unopened_session_raises_runtimeerror():
    sess = CDPSession("ws://127.0.0.1:1")
    with pytest.raises(RuntimeError, match="not open"):
        await sess.send("X.y")
```
- [ ] **Step 2:** `.venv/bin/python -m pytest tests/test_common_cdp.py::test_send_on_unopened_session_raises_runtimeerror -v` → FAIL (AssertionError, not RuntimeError — `assert` raises `AssertionError`).
- [ ] **Step 3: Implement** — in `common/cdp.py`:
  - Change `EventCallback = Callable[[str, dict], None]` → `EventCallback = Callable[[str, dict[str, Any]], None]`.
  - In `send()`: replace `assert self._ws is not None, "session not open"` with:
    ```python
        if self._ws is None:
            raise RuntimeError("CDP session not open; use 'async with CDPSession(...)'")
    ```
  - In `_reader()`: replace `assert self._ws is not None` with the same `if self._ws is None: raise RuntimeError(...)`.
  - Change `send(self, method: str, params: dict | None = None)` → `params: dict[str, Any] | None = None`.
- [ ] **Step 4:** `.venv/bin/python -m pytest tests/test_common_cdp.py -v` → all PASS.
- [ ] **Step 5:** `.venv/bin/python -m pytest -q` → all pass.

---

## Task 2: A3 — Frozen config dataclasses

**Files:** `common/config.py`, `tests/test_common_config.py`

- [ ] **Step 1: Write failing test** — append to `tests/test_common_config.py`:
```python
def test_config_dataclasses_are_frozen(tmp_path: Path):
    import dataclasses
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        '[burp]\nbridge_url="x"\n[browser]\nchrome_candidates=["c"]\n'
        'default_proxy="p"\nheadless=false\ncdp_port=1\nnavigation_timeout_s=1\n'
        'user_data_dir_root="/tmp"\n'
        '[logging]\nlevel="INFO"\ndir="logs"\n[evidence]\ndir="evidence"\n'
    )
    cfg = load_config(cfg_file)
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.burp.bridge_url = "y"
```
  (Note: this test includes `user_data_dir_root` which Task 3 adds — if running before Task 3, omit that line and add it in Task 3.)
- [ ] **Step 2:** Run → FAIL (no error raised; mutation succeeds).
- [ ] **Step 3:** Change all five `@dataclass` decorators in `common/config.py` to `@dataclass(frozen=True)`.
- [ ] **Step 4:** `.venv/bin/python -m pytest tests/test_common_config.py -v` → PASS.
- [ ] **Step 5:** `.venv/bin/python -m pytest -q` → all pass.

---

## Task 3: A8 — `user_data_dir_root` config key

**Files:** `config.toml`, `common/config.py`, `MCPs/browser-mcp/browser_mcp/server.py`, `tests/test_common_config.py`

- [ ] **Step 1:** Append `user_data_dir_root = "/tmp"` under `[browser]` in `config.toml`.
- [ ] **Step 2:** Add `user_data_dir_root: str` field to `BrowserConfig` in `common/config.py`.
- [ ] **Step 3:** Update **every** TOML literal in `tests/test_common_config.py` that has a `[browser]` section to include `user_data_dir_root = "/tmp"`. Add an assertion `assert cfg.browser.user_data_dir_root == "/tmp"` to `test_load_config_reads_toml`.
- [ ] **Step 4:** In `MCPs/browser-mcp/browser_mcp/server.py`, change `user_data_dir_root="/tmp",` → `user_data_dir_root=cfg.browser.user_data_dir_root,`.
- [ ] **Step 5:** `.venv/bin/python -m pytest tests/test_common_config.py -v && .venv/bin/python -c "import browser_mcp.server"` → PASS / clean import.
- [ ] **Step 6:** `.venv/bin/python -m pytest -q` → all pass.

---

## Task 4: A7 — Clean up Chrome user-data-dir on `close()`

**Files:** `MCPs/browser-mcp/browser_mcp/tools.py`, `MCPs/browser-mcp/tests/test_tool_close.py`

- [ ] **Step 1: Write failing test** — append to `test_tool_close.py`:
```python
@pytest.mark.asyncio
async def test_close_removes_user_data_dir(tmp_path):
    import os
    sess = BrowserSession(chrome_candidates=[], cdp_port=9222, default_proxy=None,
                          user_data_dir_root=str(tmp_path))
    udd = tmp_path / "fake-udd"
    udd.mkdir()
    (udd / "leftover").write_text("x")
    sess._udd = str(udd)
    sess._proc = _FakeProc()
    await sess.close()
    assert not udd.exists()
    assert sess._udd is None
```
- [ ] **Step 2:** Run → FAIL (`AttributeError: ... has no attribute '_udd'`).
- [ ] **Step 3: Implement** — in `tools.py`:
  - Add `import shutil` at top (if not present).
  - In `__init__`: `self._udd: str | None = None`.
  - In `launch()`: after `udd = tempfile.mkdtemp(...)`, set `self._udd = udd`.
  - In `close()`, after `self._proc = None`, add:
    ```python
        if self._udd:
            shutil.rmtree(self._udd, ignore_errors=True)
        self._udd = None
    ```
- [ ] **Step 4:** `.venv/bin/python -m pytest MCPs/browser-mcp/tests/test_tool_close.py -v` → PASS.
- [ ] **Step 5:** `.venv/bin/python -m pytest -q` → all pass.

---

## Task 5: A4+A5 — Logging timestamp precision + rotation

**Files:** `common/logging.py`, `tests/test_common_logging.py`

- [ ] **Step 1: Write failing tests** — append to `tests/test_common_logging.py`:
```python
import re
from logging.handlers import RotatingFileHandler


def test_log_timestamp_has_microseconds_and_z(tmp_path):
    logger = setup_logger("ts-mcp", log_dir=tmp_path)
    logger.info("x")
    line = (tmp_path / "ts-mcp.log").read_text().splitlines()[-1]
    rec = json.loads(line)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z", rec["ts"])


def test_logger_uses_rotating_handler(tmp_path):
    logger = setup_logger("rot-mcp", log_dir=tmp_path)
    h = logger.handlers[0]
    assert isinstance(h, RotatingFileHandler)
    assert h.maxBytes == 10 * 1024 * 1024
    assert h.backupCount == 3
```
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3: Implement** — in `common/logging.py`:
  - Add `from datetime import datetime, timezone` and `from logging.handlers import RotatingFileHandler` to imports.
  - In `_JsonFormatter.format`, replace the `"ts"` line with:
    ```python
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc)
                  .strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    ```
  - In `setup_logger`, replace `file_handler = logging.FileHandler(...)` with:
    ```python
    file_handler = RotatingFileHandler(
        log_dir / f"{name}.log", maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    ```
- [ ] **Step 4:** `.venv/bin/python -m pytest tests/test_common_logging.py -v` → PASS.
- [ ] **Step 5:** `.venv/bin/python -m pytest -q` → all pass.

---

## Task 6: A6 — `httpx.NetworkError` → `httpx.TransportError`

**Files:** `common/burp_client.py`

- [ ] **Step 1:** In `_request()`, change the except tuple from `(httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)` → `(httpx.ConnectError, httpx.TimeoutException, httpx.TransportError)`.
- [ ] **Step 2:** `.venv/bin/python -m pytest tests/test_common_burp_client.py -v` → all PASS (existing `test_connection_refused_maps_to_unavailable` covers).
- [ ] **Step 3:** `.venv/bin/python -m pytest -q` → all pass.

---

## Task 7: A9+A10 — Kotlin status-filter + base64 validation

**Files:** `ProxyRoutes.kt`, `RepeaterRoutes.kt`, `IntruderRoutes.kt`, `HttpSendRoutes.kt`, `RoutesTest.kt`

- [ ] **Step 1: Write failing test** — in `RoutesTest.kt` add:
```kotlin
    @Test
    fun `http send rejects invalid base64`() {
        val router = Router(api = FakeApi())
        registerHttpSendRoutes(router)
        val r = router.dispatch("POST", "/http/send", emptyMap(),
            """{"raw_base64":"!!!not-b64","host":"x","port":80}""")
        assertEquals(400, r.status)
        assertTrue(r.body().contains("BAD_INPUT"))
    }
```
- [ ] **Step 2:** `(cd MCPs/burp-mcp/burp-ext && ./gradlew test)` → FAIL (currently returns 500 INTERNAL via the router catch-all, not 400 BAD_INPUT).
- [ ] **Step 3: Implement:**
  - **A9** `ProxyRoutes.kt`: rename `statusMin` → `status`; change filter line to `.filter { status == null || (it.originalResponse()?.statusCode()?.toInt() ?: -1) == status }`.
  - **A10** In each of `RepeaterRoutes.kt`, `IntruderRoutes.kt`, `HttpSendRoutes.kt`, replace `val rawBytes = Base64.getDecoder().decode(rawB64)` (or `val bytes = ...`) with:
    ```kotlin
        val rawBytes = runCatching { Base64.getDecoder().decode(rawB64) }.getOrElse {
            return@register Response(400, mapOf("ok" to false, "error" to mapOf(
                "code" to "BAD_INPUT", "message" to "raw_base64 is not valid base64")))
        }
    ```
    (In `HttpSendRoutes.kt` use the local `badInput("raw_base64 is not valid base64")` helper.)
- [ ] **Step 4:** `(cd MCPs/burp-mcp/burp-ext && ./gradlew test)` → BUILD SUCCESSFUL.
- [ ] **Step 5:** `(cd MCPs/burp-mcp/burp-ext && ./gradlew shadowJar)` → jar rebuilt.

---

## Task 8: A11 — Kotlin `/http/send` happy-path stub test

**Files:** `RoutesTest.kt`

- [ ] **Step 1:** Attempt to add a `FakeHttp` stub implementing `burp.api.montoya.http.Http` whose `sendRequest(req)` returns a canned `HttpRequestResponse` with a non-null `response()`. **If the Montoya `Http` interface has too many abstract methods to stub concisely (>~10), report DONE_WITH_CONCERNS and skip** — the integration test in `tests/integration/` already covers this path with live Burp.
- [ ] **Step 2:** If stub is feasible, add test asserting `status==200`, `body_base64` present, `time_ms >= 0`.
- [ ] **Step 3:** `./gradlew test` → BUILD SUCCESSFUL.

---

## Task 9: A12 — `scripts/build-all.sh`

**Files:** Create `scripts/build-all.sh`

- [ ] **Step 1:** Create the file:
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
pip install --upgrade pip -q
pip install -q -r requirements.txt
pip install -q -e ".[dev]"
pip install -q -e MCPs/browser-mcp
pip install -q -e MCPs/burp-mcp
pip install -q -r MCPs/parley-mcp/requirements.txt
[ -f MCPs/github-mcp/requirements.txt ] && pip install -q -r MCPs/github-mcp/requirements.txt
[ -f MCPs/github-mcp/MCPs/libs/mcp_armor/requirements.txt ] && \
  pip install -q -r MCPs/github-mcp/MCPs/libs/mcp_armor/requirements.txt

( cd MCPs/burp-mcp/burp-ext && ./gradlew shadowJar )

pytest -q
echo "build-all: OK"
```
- [ ] **Step 2:** `chmod +x scripts/build-all.sh`
- [ ] **Step 3:** `bash scripts/build-all.sh 2>&1 | tail -5` → ends with `build-all: OK`.

---

## Task 10: A13 — `scripts/update-vendored.sh`

**Files:** Create `scripts/update-vendored.sh`

- [ ] **Step 1:** Create the file:
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

case "${1:-}" in
  parley) DIR="MCPs/parley-mcp"; URL="https://github.com/gglessner/Parley-MCP" ;;
  github) DIR="MCPs/github-mcp"; URL="https://github.com/gglessner/github-MCP" ;;
  *) echo "usage: $0 <parley|github>" >&2; exit 1 ;;
esac

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
git clone --depth 1 "$URL" "$TMP/upstream"
SHA=$(cd "$TMP/upstream" && git rev-parse HEAD)

find "$DIR" -mindepth 1 -maxdepth 1 ! -name 'UPSTREAM.txt' -exec rm -rf {} +
cp -r "$TMP/upstream/." "$DIR/"
rm -rf "$DIR/.git"

{
  echo "upstream: $URL"
  echo "pinned_commit: $SHA"
  date -u +"pinned_at: %Y-%m-%dT%H:%M:%SZ"
} > "$DIR/UPSTREAM.txt"

echo "Updated $DIR to $SHA. Reinstall deps and review the diff before committing."
```
- [ ] **Step 2:** `chmod +x scripts/update-vendored.sh`
- [ ] **Step 3:** `bash scripts/update-vendored.sh 2>&1` → prints usage and exits 1 (verifies arg validation; do NOT actually run with an arg — that would mutate vendored dirs).

---

## Task 11: A14 — pre-commit + ruff config

**Files:** Create `.pre-commit-config.yaml`; modify `pyproject.toml`, `README.md`

- [ ] **Step 1:** Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.7
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```
- [ ] **Step 2:** In `pyproject.toml` under `[tool.ruff]`, add:
```toml
extend-exclude = ["MCPs/parley-mcp", "MCPs/github-mcp", "MCPs/burp-mcp/burp-ext"]
```
- [ ] **Step 3:** Run `.venv/bin/ruff check common/ MCPs/browser-mcp/browser_mcp/ MCPs/burp-mcp/burp_mcp/ tests/` — fix any reported errors in own code (likely a handful of unused imports; fix them).
- [ ] **Step 4:** Add to `README.md` Setup section: `pip install pre-commit && pre-commit install` one-liner.
- [ ] **Step 5:** `.venv/bin/python -m pytest -q` → all pass after any ruff-driven edits.

---

## Task 12: A15 — `MCPs/github-mcp/requirements.txt`

**Files:** Create `MCPs/github-mcp/requirements.txt`

- [ ] **Step 1:** Create the file:
```
fastmcp>=2
PyGithub>=2
pyyaml>=6
```
- [ ] **Step 2:** `.venv/bin/pip install -q -r MCPs/github-mcp/requirements.txt && .venv/bin/python -c "import fastmcp, github, yaml; print('ok')"` → `ok`.

---

## Task 13: A16+A18 — Small doc additions

**Files:** `pyproject.toml`, `MCPs/burp-mcp/README.md`

- [ ] **Step 1:** In `pyproject.toml`, add a comment line immediately above `[tool.setuptools.packages.find]`:
```toml
# Restrict discovery to common/* — setuptools flat-layout autodiscovery fails
# when sibling non-package dirs (MCPs/, docs/, tests/) exist at the root.
```
- [ ] **Step 2:** In `MCPs/burp-mcp/README.md`, add after the Tools list:
```markdown
**Note:** `burp_http_send`'s `timeout_ms` is currently advisory — the bridge
forwards it but Montoya's `sendRequest()` uses Burp's project-level network
timeout. Reserved for forward compatibility.
```
- [ ] **Step 3:** No tests; verify files read back correctly.

---

## Task 14: A17 — `docs/source-informed-workflow.md`

**Files:** Create `docs/source-informed-workflow.md`

- [ ] **Step 1:** Write a ~60-80 line worked example following the spec's "Example 2 — source-code-informed testing" data-flow (`docs/superpowers/specs/2026-04-16-web-mcp-stack-design.md` lines ~212-220), using concrete tool calls: `get_directory_tree` → `search_code` → `get_file_contents` → `burp_http_send` → `browser_navigate` → `burp_save_request`. Use `acmecorp/webapp` and `/api/export` as the running example. Include the expected response shapes from the actual implementations.
- [ ] **Step 2:** Link it from `README.md` under a new line in the intro: `See docs/source-informed-workflow.md for a worked example of source-aware testing.`

---

## Task 15: Update `to-do.md`

**Files:** `to-do.md`

- [ ] **Step 1:** Under "Deferred / nice-to-have", check off (change `[ ]` → `[x]`) the items now done: frozen dataclasses, cdp typing, cdp asserts, log timestamp, pyproject comment, source-informed-workflow doc, update-vendored script, build-all script, log rotation, pre-commit. Leave the Burp match-replace verification and jar-commit-decision items as-is (out of scope).
- [ ] **Step 2:** Under "Done (for reference)", add a line: `- ✅ Cycle A (hardening pass): 18 items — see docs/superpowers/specs/2026-04-17-hardening-pass-design.md`.

---

## Done criteria

- [ ] `.venv/bin/python -m pytest -q` ≥ 92 passed (88 baseline + ~4-6 new).
- [ ] `(cd MCPs/burp-mcp/burp-ext && ./gradlew test && ./gradlew shadowJar)` BUILD SUCCESSFUL.
- [ ] `bash scripts/build-all.sh` exits 0.
- [ ] `.venv/bin/ruff check common/ MCPs/browser-mcp/browser_mcp/ MCPs/burp-mcp/burp_mcp/ tests/` → 0 errors.
- [ ] `to-do.md` deferred items checked off.
