# Workhorse Tools (Sub-project B) — Design

**Date:** 2026-04-17
**Author:** Garland Glessner (gglessner@gmail.com)
**Status:** Approved for planning
**Track:** Web-MCP enhancement cycle B (feature pass). Cycle A (hardening backlog) is the planned fast-follow; nothing from A is folded in here.

## Purpose

Close the gap between what the 30 `testing-*` skills assume and what the MCP stack actually exposes. Today `burp_repeater_send` only opens a UI tab — there is no tool that sends a request through Burp and returns the response for Claude to diff. Screenshots and raw request/response captures land in Claude's context as multi-megabyte base64 blobs instead of files on disk. SPAs render after `browser_navigate` returns, with no way to wait for an element. XHR/fetch bodies are visible in the CDP network log metadata but not retrievable.

This sub-project adds four small, composable capabilities that make the existing skill library end-to-end usable:

- **B1** `burp_http_send` — send a raw request through Burp, return status / headers / body preview / timing; optionally persist `.http` files.
- **B2** `browser_wait_for` — poll until a selector is attached/visible or time out.
- **B3** `browser_get_response_body` — fetch a CDP `Network.*` response body by `requestId`.
- **B4** Evidence persistence — config-driven `evidence/` dir with traversal-guarded relative `save_to` on `browser_screenshot`, `burp_http_send`, and a new `burp_save_request`.

Plus minimal skill updates: `mcp-burp`, `mcp-browser`, `methodology-evidence-capture` (3 files). The 30 `testing-*` skills are **not** swept in this cycle.

## Non-goals

- No new MCP servers. All changes extend browser-mcp and burp-mcp.
- No edits to vendored `parley-mcp` or `github-mcp`.
- No `testing-*` skill sweep (separate follow-up after the new tool shapes are proven).
- No items from the hardening backlog (cycle A): `httpx.NetworkError`, cdp asserts, udd cleanup, log rotation, status-filter semantics, build/vendor scripts, github-mcp requirements.

## Architecture

No new processes. Evidence-writing and path-guarding live in a new shared module `common/evidence.py` (Approach 1) — both MCPs already import from `common/`, and a single tested implementation prevents drift.

```
Claude Code ──stdio──▶ browser-mcp ──CDP──▶ Chrome
            ──stdio──▶ burp-mcp ───HTTP──▶ burp-mcp-bridge.jar (Montoya)
                                     │
                                     └──▶ api.http().sendRequest()  [new: /http/send]

common/evidence.py ◀── imported by both MCPs
        │
        └──▶ <WORKSPACE>/<cfg.evidence.dir>/<save_to>   (traversal-guarded writes)
```

## File inventory

`[N]` = new, `[M]` = modified.

```
config.toml                                           [M] +[evidence]
.gitignore                                            [M] +evidence/
common/config.py                                      [M] +EvidenceConfig, wire into Config
common/evidence.py                                    [N]
common/burp_client.py                                 [M] +http_send()
MCPs/browser-mcp/browser_mcp/tools.py                 [M] +wait_for, +get_response_body, screenshot(save_to)
MCPs/browser-mcp/browser_mcp/server.py                [M] register 2 tools, extend screenshot schema, pass evidence_root
MCPs/burp-mcp/burp_mcp/tool_handlers.py               [M] +burp_http_send, +burp_save_request, accept evidence_root
MCPs/burp-mcp/burp_mcp/server.py                      [M] register 2 tools, pass evidence_root
MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/HttpSendRoutes.kt   [N]
MCPs/burp-mcp/burp-ext/src/main/kotlin/webmcp/HttpBridgeServer.kt [M] registerHttpSendRoutes()
tests/test_common_evidence.py                         [N]
tests/test_common_config.py                           [M]
MCPs/browser-mcp/tests/test_tool_wait_for.py          [N]
MCPs/browser-mcp/tests/test_tool_response_body.py     [N]
MCPs/browser-mcp/tests/test_tool_screenshot.py        [M]
MCPs/burp-mcp/tests/test_http_send_handler.py         [N]
MCPs/burp-mcp/tests/test_save_request_handler.py      [N]
MCPs/burp-mcp/burp-ext/src/test/kotlin/webmcp/RoutesTest.kt       [M]
tests/integration/test_chain_browser_burp.py          [M]
.claude/skills/mcp-burp/SKILL.md                      [M]
.claude/skills/mcp-browser/SKILL.md                   [M]
.claude/skills/methodology-evidence-capture/SKILL.md  [M]
README.md                                             [M] smoke-test additions
to-do.md                                              [M] manual bring-up additions
```

6 new source/test files, ~19 modified. **New MCP tools (4):** `burp_http_send`, `burp_save_request`, `browser_wait_for`, `browser_get_response_body`. **Extended (1):** `browser_screenshot` gains `save_to`.

## Components

### `common/` — config + evidence

**`config.toml`** gains:

```toml
[evidence]
dir = "evidence"
```

Per-engagement override goes in `config.local.toml` (already supported by `_deep_merge`). `.gitignore` gains `evidence/`.

**`common/config.py`** gains:

```python
@dataclass
class EvidenceConfig:
    dir: str
```

`Config` gains `evidence: EvidenceConfig`; `load_config()` reads `data["evidence"]` and raises `ValueError` on missing/malformed section, consistent with the other three.

**`common/evidence.py`** (new, ~40 LOC):

```python
class EvidencePathError(ValueError): ...

def resolve_evidence_path(evidence_root: Path, rel: str) -> Path:
    """Reject absolute `rel`; resolve under `evidence_root`; reject if the
    resolved path is not a descendant of evidence_root.resolve(); mkdir parents;
    return absolute Path."""

def write_evidence(evidence_root: Path, rel: str, data: bytes) -> Path:
    """resolve_evidence_path() then write via tmp+rename. Return the Path."""
```

Guard: `p = (evidence_root / rel).resolve(); if not p.is_relative_to(evidence_root.resolve()): raise EvidencePathError(...)`. Catches `..`, symlink escapes, and absolute `rel` in one check. Both MCPs compute `evidence_root = WORKSPACE / cfg.evidence.dir` once at startup (mirroring `WORKSPACE / cfg.logging.dir`).

### burp-mcp — `/http/send`, `burp_http_send`, `burp_save_request`

**Kotlin `HttpSendRoutes.kt`** (new):

```kotlin
fun registerHttpSendRoutes(router: Router) {
    router.register("POST", "/http/send") { ctx ->
        val body = ctx.bodyJson ?: return@register Response(400, badInput("JSON body required"))
        val rawB64 = body["raw_base64"] as? String
        val host   = body["host"] as? String
        val port   = (body["port"] as? Number)?.toInt()
        val secure = body["secure"] as? Boolean ?: true
        if (rawB64 == null || host == null || port == null)
            return@register Response(400, badInput("raw_base64, host, port required"))
        val req = HttpRequest.httpRequest(
            HttpService.httpService(host, port, secure),
            MByteArray.byteArray(*Base64.getDecoder().decode(rawB64)))
        val t0 = System.nanoTime()
        val rr = ctx.api.http().sendRequest(req)
        val ms = (System.nanoTime() - t0) / 1_000_000
        val resp = rr.response()
        Response(200, mapOf("ok" to true, "data" to mapOf(
            "status" to resp?.statusCode()?.toInt(),
            "headers" to resp?.headers()?.map { mapOf("name" to it.name(), "value" to it.value()) },
            "body_base64" to resp?.body()?.let { Base64.getEncoder().encodeToString(it.bytes) },
            "body_len" to (resp?.body()?.length() ?: 0),
            "request_base64" to Base64.getEncoder().encodeToString(req.toByteArray().bytes),
            "time_ms" to ms)))
    }
}
```

`api.http().sendRequest()` is available on Community and Pro — no `PRO_REQUIRED` gate. A `null` response (target unreachable) is returned as `ok:true` with `status:null, body_len:0` — the bridge call succeeded; Claude interprets the absent response. `HttpBridgeServer.kt` init block adds `registerHttpSendRoutes(router)`. `badInput(msg)` is a small local helper returning the standard `{"ok":false,"error":{"code":"BAD_INPUT",...}}` map.

**`common/burp_client.py`** gains:

```python
async def http_send(self, *, raw_base64: str, host: str, port: int,
                    secure: bool = True, timeout_ms: int = 30000) -> dict:
    return await self._request("POST", "/http/send",
        json={"raw_base64": raw_base64, "host": host, "port": port,
              "secure": secure, "timeout_ms": timeout_ms})
```

**`burp_mcp/tool_handlers.py`** — `handle()` signature becomes `handle(tool, args, *, bridge_url, evidence_root)`. Two new branches:

`burp_http_send`:
1. `data = await c.http_send(raw_base64, host, port, secure, timeout_ms)`.
2. `body = b64decode(data["body_base64"] or "")`; `preview = body[:args.get("preview_bytes", 4096)].decode("utf-8", "replace")`.
3. If `args.get("save_to")`: `write_evidence(evidence_root, f"{save_to}.request.http", b64decode(data["request_base64"]))`; reconstruct `HTTP/1.1 {status}\r\n{hdrs}\r\n\r\n{body}` and write as `f"{save_to}.response.http"`; collect both relative paths.
4. Return:
   ```json
   {"ok": true, "data": {
     "status": 200, "time_ms": 87, "body_len": 14302,
     "headers": [{"name":"Content-Type","value":"text/html"}, ...],
     "body_preview": "<!doctype html>...",
     "body_base64": "<present only if include_body=true>",
     "saved": {"request": "evidence/F-001/probe.request.http",
               "response": "evidence/F-001/probe.response.http"}
   }}
   ```
   `saved` key present only when `save_to` was supplied. `body_base64` key present only when `include_body=true`.

`burp_save_request`:
1. `data = await c.proxy_request(id)` — already returns `request.raw_base64` and `response.raw_base64`.
2. `write_evidence(evidence_root, f"{save_to}.request.http", b64decode(req))`; same for response (skip if `response is None`).
3. Return `{"ok": true, "data": {"saved": {"request": "...", "response": "..." | null}}}`.

**`burp_mcp/server.py`** — register both tools; pass `evidence_root` to `handle()`:

```python
Tool(name="burp_http_send",
     description="Send a raw HTTP request through Burp and return the response "
                 "(status, headers, timing, body preview). Optional save_to "
                 "writes <stem>.request.http / <stem>.response.http under the "
                 "configured evidence dir.",
     inputSchema={"type":"object","required":["raw_base64","host","port"],"properties":{
       "raw_base64":{"type":"string"},"host":{"type":"string"},"port":{"type":"integer"},
       "secure":{"type":"boolean"},"timeout_ms":{"type":"integer"},
       "preview_bytes":{"type":"integer"},"include_body":{"type":"boolean"},
       "save_to":{"type":"string",
                  "description":"relative path stem under evidence/, e.g. 'F-001/idor-probe'"}}})

Tool(name="burp_save_request",
     description="Write a proxy-history entry's raw request/response to "
                 "<stem>.request.http / <stem>.response.http under the evidence dir.",
     inputSchema={"type":"object","required":["id","save_to"],"properties":{
       "id":{"type":"integer"},"save_to":{"type":"string"}}})
```

### browser-mcp — `wait_for`, `get_response_body`, `screenshot(save_to=)`

`BrowserSession.__init__` gains `evidence_root: Path | None = None`; `server.py` passes `WORKSPACE / cfg.evidence.dir`.

**`wait_for(selector, timeout_s=10.0, state="attached")`** — polling loop with mild backoff:

```python
async def wait_for(self, selector: str, *, timeout_s: float = 10.0,
                   state: str = "attached") -> dict:
    err = self._require_attached()
    if err: return err
    deadline = time.monotonic() + timeout_s
    interval = 0.1
    while time.monotonic() < deadline:
        root = await self._root_node_id()
        found = await self._cdp.send("DOM.querySelector",
                                     {"nodeId": root, "selector": selector})
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
    return error_envelope(ErrorCode.TIMEOUT,
        f"selector not {state} within {timeout_s}s", detail={"selector": selector})
```

Polling chosen over CDP DOM mutation events: simpler, no subscription state to manage, 100–500 ms granularity is adequate for pentesting.

**`get_response_body(request_id)`**:

```python
async def get_response_body(self, request_id: str) -> dict:
    err = self._require_attached()
    if err: return err
    try:
        resp = await self._cdp.send("Network.getResponseBody", {"requestId": request_id})
    except CDPError as e:
        return error_envelope(ErrorCode.BAD_INPUT,
            f"response body unavailable for requestId={request_id}: {e}",
            detail={"hint": "body is only retrievable while the originating page is loaded"})
    return ok_envelope({"request_id": request_id,
                        "base64_encoded": resp.get("base64Encoded", False),
                        "body": resp.get("body", ""),
                        "length": len(resp.get("body", ""))})
```

`request_id` comes from `browser_network_log` entries — `params.requestId` on `Network.requestWillBeSent` / `Network.responseReceived` events. `CDPError` must be imported from `common.cdp`.

**`screenshot(full_page=False, save_to=None)`** — extended:

```python
async def screenshot(self, *, full_page: bool = False,
                     save_to: str | None = None) -> dict:
    err = self._require_attached()
    if err: return err
    resp = await self._cdp.send("Page.captureScreenshot",
                                {"format": "png", "captureBeyondViewport": full_page})
    if save_to:
        png = base64.b64decode(resp.get("data", ""))
        path = write_evidence(self._evidence_root, save_to, png)
        return ok_envelope({"format": "png", "bytes": len(png),
                            "saved": str(path.relative_to(self._evidence_root.parent))})
    return ok_envelope({"format": "png", "base64": resp.get("data", "")})
```

When `save_to` is set the response **omits `base64`** and returns only the path + byte count.

**`server.py`** schemas:

```python
Tool(name="browser_wait_for",
     description="Poll until a CSS selector is attached (or visible) in the DOM, or time out.",
     inputSchema={"type":"object","required":["selector"],"properties":{
       "selector":{"type":"string"},"timeout_s":{"type":"number"},
       "state":{"type":"string","enum":["attached","visible"]}}})

Tool(name="browser_get_response_body",
     description="Return the response body for a CDP Network requestId from "
                 "browser_network_log. Only works while the page that made the "
                 "request is still loaded.",
     inputSchema={"type":"object","required":["request_id"],
                  "properties":{"request_id":{"type":"string"}}})

# browser_screenshot inputSchema gains:
#   "save_to": {"type":"string",
#               "description":"relative path under evidence/, e.g. 'F-001/shot.png'"}
```

### Skill updates (3 files)

**`mcp-burp/SKILL.md`** — add `burp_http_send` and `burp_save_request` to Test steps and Tool commands. `burp_http_send` becomes the primary probe pattern; `burp_repeater_send` is retained as "open in Burp UI for manual follow-up." Add a `save_to` worked example. Correct the `burp_scope_check` documented response to `{"checks":{url:bool}}` (matches `ScopeRoutes.kt`).

**`mcp-browser/SKILL.md`** — insert `browser_wait_for` after navigate / before snapshot; add `browser_get_response_body` after `browser_network_log`; update `browser_screenshot` example to `save_to="F-001/login.png"` returning a path.

**`methodology-evidence-capture/SKILL.md`** — Tool commands become concrete one-liners: `burp_http_send(..., save_to="F-001/probe")`, `burp_save_request(id=N, save_to="F-001/baseline")`, `browser_screenshot(save_to="F-001/screenshot.png")`. Note `[evidence] dir` in `config.local.toml` sets the per-engagement root.

## Error handling

No new `ErrorCode` values.

| Condition | Envelope |
|---|---|
| `save_to` absolute / escapes evidence dir | `BAD_INPUT` — "save_to must be a relative path under `<dir>`" |
| `browser_wait_for` deadline | `TIMEOUT` — `detail={"selector": ...}` |
| `browser_get_response_body` CDP -32000 | `BAD_INPUT` — `detail={"hint": "page-lifetime constraint"}` |
| `/http/send` target refused / timed out | `ok:true`, `status:null`, `body_len:0`, `time_ms:<elapsed>` |
| `/http/send` bridge unreachable | `BURP_UNAVAILABLE` (existing `BurpClient` path) |
| Evidence disk write `OSError` | `INTERNAL` — message includes the OSError text |

## Testing

**Unit (pytest):**

| File | Cases |
|---|---|
| `tests/test_common_evidence.py` (new) | happy path; `..` rejected; absolute rejected; symlink-escape rejected; parent mkdir; tmp+rename |
| `tests/test_common_config.py` (extend) | `[evidence]` parsed; missing section → `ValueError` |
| `MCPs/browser-mcp/tests/test_tool_wait_for.py` (new) | nodeId 0→42 → ok; never found → `TIMEOUT`; `state="visible"` with/without box model |
| `MCPs/browser-mcp/tests/test_tool_response_body.py` (new) | body returned; `CDPError` → `BAD_INPUT` |
| `MCPs/browser-mcp/tests/test_tool_screenshot.py` (extend) | `save_to` writes file under tmp evidence root; response has `saved`, no `base64` |
| `MCPs/burp-mcp/tests/test_http_send_handler.py` (new) | respx `/http/send`; preview truncation at `preview_bytes`; `include_body` toggle; `save_to` writes two `.http` files; `EvidencePathError` → `BAD_INPUT` |
| `MCPs/burp-mcp/tests/test_save_request_handler.py` (new) | respx `/proxy/request/{id}`; two files written; response-absent case writes request only |

**Kotlin (JUnit):** `RoutesTest.kt` gains a `/http/send` dispatch test. `FakeApi` grows a minimal `http()` returning a stub `Http` whose `sendRequest()` returns a canned `HttpRequestResponse`.

**Integration (`@pytest.mark.integration`):** `tests/integration/test_chain_browser_burp.py` gains one assertion — after the existing navigate, call `handle("burp_http_send", {...})` against the Flask fixture's `/echo?q=chain-probe` and assert `body_preview` contains `chain-probe`.

**Manual smoke (README + to-do.md additions):**
- Rebuild jar (`./gradlew shadowJar`), reload in Burp.
- `curl -s -X POST http://127.0.0.1:8775/http/send -H 'Content-Type: application/json' -d '{"raw_base64":"R0VUIC9lY2hvP3E9aGkgSFRUUC8xLjENCkhvc3Q6IDEyNy4wLjAuMTo1MDU1DQoNCg==","host":"127.0.0.1","port":5055,"secure":false}'` → `{"ok":true,"data":{"status":200,...}}`.
- Claude prompt: *"Use burp_http_send to GET http://127.0.0.1:5055/echo?q=hello with save_to='smoke/echo', then list the evidence dir."* → two `.http` files appear under `evidence/smoke/`.

## Acceptance criteria

1. `pytest -q` passes with the new unit tests (≥ existing 61 + ~18 new).
2. `./gradlew test` passes in `MCPs/burp-mcp/burp-ext/`.
3. `./gradlew shadowJar` produces a jar; loading it in Burp exposes `/http/send` (verified via `curl`).
4. With Burp + bridge live, `pytest -m integration` passes including the new `burp_http_send` assertion.
5. `evidence/` is gitignored; `save_to="../x"` returns `BAD_INPUT` and writes nothing.
6. `mcp-burp`, `mcp-browser`, `methodology-evidence-capture` skills document the new tools and pass the `docs/skill-conventions.md` checklist.
7. README + to-do.md updated with rebuild + smoke-test steps.

## Out of scope (deferred)

`testing-*` skill sweep · cycle-A hardening items (`httpx.NetworkError`, cdp asserts, udd cleanup, status-filter semantics, log rotation/timestamps, frozen dataclasses, build/vendor scripts, github-mcp requirements, pre-commit).
