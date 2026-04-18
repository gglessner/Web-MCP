# Hardening Pass (Cycle A) — Design

**Date:** 2026-04-17
**Author:** Garland Glessner (gglessner@gmail.com)
**Status:** Approved (fast-track — inventory pre-agreed, ceremony skipped)
**Track:** Web-MCP enhancement cycle A. Follows cycle B (workhorse tools).

## Purpose

Clear the bug-fix and code-quality backlog accumulated in `to-do.md` plus issues
found during the 2026-04-17 repo read and cycle-B final review. All items are
small, isolated, own-code changes with high test coverage. No new features.

## Scope (18 items)

### `common/` fixes
- **A1** `common/cdp.py` — replace the two `assert self._ws is not None` guards
  with explicit `RuntimeError("CDP session not open")` so they survive `python -O`.
- **A2** `common/cdp.py` — tighten typing: `EventCallback = Callable[[str, dict[str, Any]], None]`;
  `send(params: dict[str, Any] | None = None)`.
- **A3** `common/config.py` — add `frozen=True` to all five `@dataclass` decorators
  (`BurpConfig`, `BrowserConfig`, `LoggingConfig`, `EvidenceConfig`, `Config`).
- **A4** `common/logging.py` — timestamp format `"%Y-%m-%dT%H:%M:%S.%fZ"` for
  sub-second precision and explicit UTC suffix; record `datetime.now(UTC)` not
  local time.
- **A5** `common/logging.py` — switch `FileHandler` to `RotatingFileHandler`
  (`maxBytes=10*1024*1024`, `backupCount=3`).
- **A6** `common/burp_client.py` — replace `httpx.NetworkError` (removed in
  httpx ≥0.28) with `httpx.TransportError` in the `except` tuple.

### browser-mcp fixes
- **A7** `browser_mcp/tools.py` — store the `tempfile.mkdtemp` user-data-dir
  path on `self._udd`; `close()` calls `shutil.rmtree(self._udd, ignore_errors=True)`
  after process termination; clear `self._udd = None`.
- **A8** `browser_mcp/server.py` + `config.toml` + `common/config.py` — add
  `user_data_dir_root` to `[browser]` (default `"/tmp"`); `BrowserConfig` gains
  the field; `server.py` passes `cfg.browser.user_data_dir_root` instead of
  hardcoded `"/tmp"`.

### Kotlin fixes
- **A9** `ProxyRoutes.kt` — change `status` filter from `>= statusMin` to exact
  `== status` to match the MCP schema description and the `mcp-burp` skill docs.
- **A10** `RepeaterRoutes.kt`, `IntruderRoutes.kt`, `HttpSendRoutes.kt` — wrap
  `Base64.getDecoder().decode(rawB64)` in `runCatching { }.getOrElse { return ... BAD_INPUT "raw_base64 not valid base64" }`.
- **A11** `RoutesTest.kt` — add a happy-path test for `/http/send` using a
  minimal stub `Http` that returns a canned `HttpRequestResponse` (so the
  Montoya→JSON shaping is unit-covered, not just the validation path).

### Scripts
- **A12** `scripts/build-all.sh` — venv create-if-missing, pip installs per
  README, `./gradlew shadowJar`, `pytest -q`. Exit non-zero on any failure.
- **A13** `scripts/update-vendored.sh <parley|github>` — clone upstream to
  `/tmp`, copy over, regenerate `UPSTREAM.txt`, reinstall requirements. Prints
  a reminder to commit.
- **A14** `.pre-commit-config.yaml` + `pyproject.toml` ruff config — `ruff check`
  and `ruff format --check` hooks. README gains a one-liner install note.

### Vendored / deps
- **A15** `MCPs/github-mcp/requirements.txt` (new) — `fastmcp>=2`, `PyGithub>=2`,
  `pyyaml>=6`. README setup block already conditionally installs it.

### Docs
- **A16** `pyproject.toml` — one-line comment above `[tool.setuptools.packages.find]`
  explaining flat-layout auto-discovery failure with sibling non-package dirs.
- **A17** `docs/source-informed-workflow.md` — worked example combining
  `github-mcp` + `browser-mcp` + `burp-mcp` (the spec already describes the
  concept; this is the concrete walkthrough).
- **A18** `MCPs/burp-mcp/README.md` — note that `timeout_ms` on `burp_http_send`
  is currently advisory (Montoya uses Burp's project-level network timeout).

## Non-goals

- No new MCP tools or features.
- No edits to vendored `parley-mcp` source (only adding `github-mcp/requirements.txt`
  alongside, which upstream lacks).
- No `testing-*` skill sweep.
- No CI pipeline (pre-commit is local-only).

## Error handling

No new error codes. A1 raises `RuntimeError` (already a documented failure mode
for `CDPSession.send`). A3 makes config mutation raise `dataclasses.FrozenInstanceError`
— no callers currently mutate, so this is preventive only.

## Testing

| Item | Test |
|---|---|
| A1 | `tests/test_common_cdp.py` — new test: `send()` on un-entered session raises `RuntimeError` |
| A2 | Type-only; no runtime test (covered by existing cdp tests still passing) |
| A3 | `tests/test_common_config.py` — new test: mutating `cfg.burp.bridge_url` raises `FrozenInstanceError` |
| A4 | `tests/test_common_logging.py` — assert `ts` matches `r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z"` |
| A5 | `tests/test_common_logging.py` — assert handler is `RotatingFileHandler` with `maxBytes==10485760` |
| A6 | Existing `test_connection_refused_maps_to_unavailable` already covers; verify still passes |
| A7 | `MCPs/browser-mcp/tests/test_tool_close.py` — new test: udd dir removed after `close()` |
| A8 | `tests/test_common_config.py` — assert `cfg.browser.user_data_dir_root` parsed; import-smoke `browser_mcp.server` |
| A9 | `RoutesTest.kt` — extend with a `status` filter case (requires stubbed proxy) OR document as manual-verify; **decision: manual-verify** since stubbing `Proxy.history()` is heavy for a one-character fix |
| A10 | `RoutesTest.kt` — `/http/send` with `raw_base64="!!!not-b64"` → 400 BAD_INPUT |
| A11 | `RoutesTest.kt` — the new happy-path test itself |
| A12-A14 | Shell smoke: `bash scripts/build-all.sh` exits 0; `pre-commit run --all-files` exits 0 |
| A15 | `pip install -r MCPs/github-mcp/requirements.txt` succeeds |
| A16-A18 | Doc-only; no test |

## Acceptance criteria

1. `pytest -q` passes (≥ baseline 88 + new tests).
2. `(cd MCPs/burp-mcp/burp-ext && ./gradlew test && ./gradlew shadowJar)` succeeds.
3. `bash scripts/build-all.sh` exits 0 on a machine with the venv already present.
4. `ruff check .` reports 0 errors on `common/`, `MCPs/browser-mcp/browser_mcp/`,
   `MCPs/burp-mcp/burp_mcp/`, `tests/` (vendored dirs excluded via config).
5. `to-do.md` "Deferred / nice-to-have" items A1-A8, A12-A14, A16 are checked off
   or removed.

## Out of scope

`testing-*` skill sweep · CI/GitHub Actions · log shipping · Windows support
beyond A8's config knob.
