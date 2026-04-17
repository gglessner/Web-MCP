# Web-MCP Stack — Design

**Date:** 2026-04-16
**Author:** Garland Glessner (gglessner@gmail.com)
**Status:** Approved for planning

## Purpose

A four-MCP Python stack for AI-driven web application security auditing and PoC validation. Provides Claude Code with equal-capability access to:

1. **Burp Suite** (proxy history, Repeater, Scanner, Intruder, scope, match-replace, site map)
2. **A controlled web browser** (navigate, DOM query, click/fill, JS eval, screenshots, cookies, network log)
3. **Parley-MCP** — user's existing AI-controlled TCP/TLS MiTM proxy for non-HTTP protocols (cloned verbatim from upstream; pullable)
4. **github-MCP** — user's existing MCP for source-aware code access with automatic secret redaction via MCP Armor (cloned verbatim from upstream; pullable). Enables source-code-informed web testing: Claude can read target repos and correlate findings in running code with their source.

The four MCPs are registered independently in Claude Code and orchestrated by the LLM; they do not call each other.

## Non-Goals

- No Node.js dependency anywhere in the stack.
- No Playwright / Selenium — browser is driven via raw Chrome DevTools Protocol (CDP).
- No orchestration layer — Claude composes tools directly.
- No modifications to Parley-MCP or github-MCP upstream; both are cloned verbatim and installed in the shared venv.

## Architecture

```
┌──────────────────────────── Claude Code ────────────────────────────┐
│      registers four stdio MCP servers via ~/.claude/settings        │
└───────┬──────────────┬──────────────────┬──────────────────┬────────┘
        │ stdio        │ stdio            │ stdio            │ stdio
        ▼              ▼                  ▼                  ▼
   ┌──────────┐  ┌────────────┐     ┌──────────┐       ┌───────────┐
   │ burp-mcp │  │browser-mcp │     │parley-mcp│       │github-mcp │
   │ (Python) │  │  (Python)  │     │ (Python) │       │ (Python)  │
   └────┬─────┘  └─────┬──────┘     └────┬─────┘       └─────┬─────┘
        │HTTP loopback │ CDP ws          │                   │HTTPS
        │127.0.0.1:8775│ 127.0.0.1:9222  │(upstream repo,    │(api.github.com
        ▼              ▼                 │ unmodified)       │ via PAT)
   ┌──────────────┐ ┌──────────────┐     │                   ▼
   │Burp extension│ │   Chrome     │     │              ┌───────────┐
   │ Kotlin,      │ │ --proxy-server     │              │ MCP Armor │
   │ Montoya API  │ │ chained to   │     │              │ (secret   │
   │ embedded     │ │ Burp/Parley  │     │              │ redaction)│
   │ HTTP server  │ │              │     │              └───────────┘
   └──────────────┘ └──────────────┘     │              (in upstream)
```

### Transport

- **Claude Code ↔ MCP:** stdio (standard local transport; no ports) — for all four MCPs.
- **burp-mcp Python ↔ Burp extension:** HTTP over loopback `127.0.0.1:8775`.
- **browser-mcp Python ↔ Chrome:** Chrome DevTools Protocol over websocket on `127.0.0.1:9222`.
- **github-mcp Python ↔ GitHub API:** HTTPS to `api.github.com` (or GHE endpoint) authenticated via `GITHUB_TOKEN` env var.

### Shared venv and workspace

One venv at `Web-MCP/.venv`. Each MCP has its own `pyproject.toml` and is installed editable (`pip install -e MCPs/burp-mcp`). Shared utilities live in `Web-MCP/common/` and are imported by all Python MCPs.

## Directory Layout

```
/home/kali/Web-MCP/
├── .venv/                              # shared virtualenv
├── config.toml                         # single config file (paths, ports, proxy chain)
├── pyproject.toml                      # workspace-style root for editable installs
├── requirements.txt                    # pinned dev deps (pytest, respx, etc.)
├── README.md                           # setup + smoke-test checklist
├── claude_config.example.json          # Claude Code MCP registration snippet
│
├── common/                             # shared Python library
│   ├── __init__.py
│   ├── config.py                       # loads config.toml
│   ├── logging.py                      # structured JSON logger
│   ├── cdp.py                          # CDP websocket client
│   ├── burp_client.py                  # typed HTTP client → Burp extension
│   └── mcp_base.py                     # stdio lifecycle, error envelope
│
├── MCPs/
│   ├── burp-mcp/
│   │   ├── pyproject.toml
│   │   ├── server.py                   # MCP entry point
│   │   ├── tools.py                    # tool definitions
│   │   ├── burp-ext/                   # Kotlin Burp extension source
│   │   │   ├── build.gradle.kts
│   │   │   └── src/main/kotlin/...
│   │   ├── build/libs/burp-mcp-bridge.jar  # built artifact
│   │   └── tests/
│   ├── browser-mcp/
│   │   ├── pyproject.toml
│   │   ├── server.py
│   │   ├── tools.py
│   │   ├── chrome_launcher.py
│   │   └── tests/
│   ├── parley-mcp/                     # git clone of upstream, untouched
│   └── github-mcp/                     # git clone of upstream, untouched
│
├── docs/
│   └── superpowers/specs/              # this document + future specs
├── logs/                               # structured logs per MCP
└── tests/
    ├── integration/                    # opt-in E2E tests (@pytest.mark.integration)
    └── fixtures/
        └── target_app.py               # tiny Flask app for E2E
```

## Components

### burp-mcp

**Kotlin extension** (`MCPs/burp-mcp/burp-ext/`): built with Gradle, uses Montoya API. Runs an embedded HTTP server on `127.0.0.1:8775` using the JDK-bundled `com.sun.net.httpserver.HttpServer` — chosen to keep the extension jar dependency-free (no Ktor / shaded dependencies). Endpoints:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/meta` | edition (Community/Pro), version, Burp build |
| `GET` | `/proxy/history` | paginated history; query params: method, host, status, contains, cursor, limit |
| `GET` | `/proxy/request/{id}` | full request + response bytes |
| `POST` | `/repeater/send` | create Repeater tab with supplied request |
| `POST` | `/scanner/scan` | start scan (Pro only → 503 on Community) |
| `GET` | `/scanner/issues` | list scan issues with filtering |
| `POST` | `/intruder/launch` | start Intruder attack (Pro only) |
| `GET` | `/scope` | read target scope |
| `POST` | `/scope` | add/remove scope entries |
| `GET` | `/match-replace` | read match-and-replace rules |
| `POST` | `/match-replace` | add/update/delete rules |
| `GET` | `/sitemap` | site map entries |

Build produces `burp-mcp-bridge.jar`. Loaded in Burp via Extensions → Add → Java.

**Python MCP** (`MCPs/burp-mcp/server.py`): thin wrapper over the extension. Each MCP tool maps 1:1 to an endpoint. Uses `httpx` for HTTP, official `mcp` Python SDK for stdio. Detects Pro vs Community at startup via `GET /meta`; tools requiring Pro are still registered but return a structured `PRO_REQUIRED` error when invoked on Community.

### browser-mcp

Pure Python: stdlib + `websockets` + `httpx` (for discovering CDP targets via `GET http://127.0.0.1:9222/json`). No Playwright, no Selenium.

**Chrome launch:** subprocess.Popen with flags:
```
chrome --remote-debugging-port=9222 \
       --proxy-server=<configured> \
       --ignore-certificate-errors \
       --user-data-dir=/tmp/web-mcp-chrome-profile-<pid> \
       --no-first-run --no-default-browser-check
```

Chrome binary path resolved from config (`chrome`, `chromium`, `google-chrome` tried in order).

**Tools:**

| Tool | CDP methods |
|---|---|
| `browser_launch(proxy?, headless?, user_data_dir?)` | subprocess spawn; connect websocket |
| `browser_navigate(url, timeout_s=30)` | `Page.navigate` + wait for `Page.loadEventFired` |
| `browser_snapshot()` | `DOM.getDocument` + `Accessibility.getFullAXTree` |
| `browser_query(selector)` | `DOM.querySelector` + `DOM.getOuterHTML` |
| `browser_click(selector)` | `DOM.querySelector` → coordinates → `Input.dispatchMouseEvent` |
| `browser_fill(selector, text)` | `DOM.focus` + `Input.insertText` |
| `browser_eval(js)` | `Runtime.evaluate` |
| `browser_screenshot(full_page?)` | `Page.captureScreenshot` (base64 PNG) |
| `browser_cookies(domain?)` | `Network.getCookies` |
| `browser_set_cookie(...)` | `Network.setCookie` |
| `browser_network_log(since_seq?)` | returns `Network.*` events accumulated in an in-memory ring buffer |
| `browser_close()` | terminate subprocess, close websocket |

### parley-mcp

Cloned from `https://github.com/gglessner/Parley-MCP.git` into `MCPs/parley-mcp/`. Installed into shared venv via `pip install -r MCPs/parley-mcp/requirements.txt`. Entry point: `python MCPs/parley-mcp/run_server.py` (unchanged). If upstream evolves, `git pull` and reinstall.

### github-mcp

Cloned from `https://github.com/gglessner/github-MCP.git` into `MCPs/github-mcp/`. Ships its own `libs/mcp_armor/` for secret redaction — installed into shared venv via `pip install -r MCPs/github-mcp/libs/mcp_armor/requirements.txt` (and any top-level requirements the repo specifies). Entry point: `python -m github_mcp` (run with `cwd=MCPs/github-mcp/` so the `github_mcp` package resolves).

**Authentication:** requires `GITHUB_TOKEN` environment variable (GitHub Personal Access Token). Optional `GHE_TOKEN` for GitHub Enterprise. Tokens are passed via the Claude Code MCP config's `env` block — never committed to `config.toml` or logged.

**Capabilities (read-only, per upstream):** `list_repos`, `get_repo`, `list_branches`, `list_commits`, `list_tags`, `list_issues`, `get_issue`, `list_issue_comments`, `list_pulls`, `get_pull`, `list_pull_files`, `list_pull_comments`, `get_file_contents`, `get_directory_tree`, `search_repos`, `search_code`, `search_issues`, `get_security_overview`, `list_dependabot_alerts`, `list_servers`. All responses pass through MCP Armor before leaving the MCP.

Upstream updates flow via `git pull` and reinstall. No modifications on our side.

### common/

- **`config.py`** — loads `Web-MCP/config.toml` using `tomllib`. Schema:
  ```toml
  [burp]
  bridge_url = "http://127.0.0.1:8775"

  [browser]
  chrome_binary = "chromium"   # or "chrome", "google-chrome", or absolute path
  default_proxy = "127.0.0.1:8080"
  headless = false
  cdp_port = 9222

  [logging]
  level = "INFO"
  dir = "logs"
  ```
- **`logging.py`** — JSON formatter, one file per MCP under `Web-MCP/logs/`.
- **`cdp.py`** — `CDPSession` class: websocket connect, target attach, request/response correlation by message id, async event handlers.
- **`burp_client.py`** — typed methods mirroring each extension endpoint; raises `BurpUnavailable`, `BurpProRequired`, `BurpBadInput`, `BurpUpstreamError`.
- **`mcp_base.py`** — stdio MCP server scaffolding, shared error-envelope helper, startup/shutdown hooks.

## Data Flow

Example 1 — PoC validation without source: *"validate reflected XSS in `/search?q=` on target.com"*

1. Claude → `burp_scope_add("target.com")` → Python MCP → HTTP → Burp extension → Montoya adds scope.
2. Claude → `browser_launch(proxy="127.0.0.1:8080")` → Chrome subprocess spawns with Burp as proxy.
3. Claude → `browser_navigate("https://target.com/search?q=<payload>")` → CDP → request through Burp → logged → target responds → Chrome renders.
4. Claude → `browser_snapshot()` → DOM returned → Claude sees whether payload executed.
5. Claude → `burp_proxy_history(host="target.com", contains="<payload>")` → Python MCP → HTTP → extension returns matching entries.
6. Claude → `burp_repeater_send(request_id=N, modified_body=...)` → replay with variants.
7. If a protocol-level issue appears, Claude switches to `parley_*` tools.

Example 2 — source-code-informed testing: *"audit the `/api/export` endpoint in `acmecorp/webapp`"*

1. Claude → `github_search_code(repo="acmecorp/webapp", q="/api/export")` → github-mcp → GitHub API → MCP Armor redacts any secrets in results → returns matches.
2. Claude → `github_get_file_contents("src/api/export.py")` → reads route handler, identifies parameters and auth checks.
3. Claude → `github_list_dependabot_alerts("acmecorp/webapp")` → known-vulnerable dependencies on this route.
4. Claude → `burp_scope_add(...)` + `browser_launch(...)` + navigate to `/api/export` with inputs derived from the source.
5. Claude correlates observed behavior (from Burp history / browser network log) against expected behavior (from source) and flags divergences.

This is the core source-aware loop: **read source → derive targeted test inputs → observe runtime behavior → correlate.**

**Proxy chain patterns:**
- Default: browser → Burp (8080) → upstream.
- Raw TCP/TLS targets: browser bypassed; Claude drives Parley directly.
- Dual: browser → Parley (8080) → Burp (8081) → upstream (configured via `browser.default_proxy`).

**Wire format:** all MCP tool calls use standard MCP JSON. Binary blobs (screenshots, raw responses) base64-encoded. Large lists paginated with opaque `cursor` tokens, default page size 50.

**No inter-MCP state.** Each MCP is crash-isolated; Claude owns orchestration.

## Error Handling

Every tool returns either a structured success or a structured error — never raises to stdio.

**Error envelope (shared):**
```json
{
  "ok": false,
  "error": {
    "code": "BURP_UNAVAILABLE | TARGET_NOT_ATTACHED | PRO_REQUIRED | TIMEOUT | BAD_INPUT | UPSTREAM_HTTP | INTERNAL",
    "message": "one-line human readable",
    "detail": { }
  }
}
```

**burp-mcp:**
- Extension unreachable → `BURP_UNAVAILABLE` with hint to load extension.
- Community + Pro-only tool → `PRO_REQUIRED`.
- Unknown request id → `BAD_INPUT`.
- HTTP 5xx from extension → `UPSTREAM_HTTP` with extension body.

**browser-mcp:**
- Chrome died → `TARGET_NOT_ATTACHED`, invite `browser_launch` again.
- CDP disconnect → one silent reconnect; second failure → `TARGET_NOT_ATTACHED`.
- Navigation exceeds timeout → `TIMEOUT` with partial load state.
- Selector not found → `BAD_INPUT`.
- JS eval throws → success envelope with `{"exception": "..."}` (the tool call itself succeeded).

**parley-mcp:** as-is from upstream; no wrapping.

**github-mcp:** as-is from upstream. Missing `GITHUB_TOKEN` surfaces as whatever error the upstream raises — we document this in README as a prerequisite check.

**Crash isolation:** each MCP is its own subprocess; Claude Code respawns on next invocation.

**Logging:** full stack traces at DEBUG in `logs/{mcp}.log`; MCP response stays terse.

**Explicitly not handled:** no retry logic inside tools (Claude decides); no cross-MCP error propagation.

## Testing

**Unit tests (pytest, per MCP):**
- `burp-mcp`: mock extension HTTP with `respx`. Validate request shapes and response parsing.
- `browser-mcp`: mock CDP websocket with local fixture replaying canned protocol frames.
- `common/`: config loading, CDP encoding/decoding, error envelope.
- Coverage target: ≥80% on Python code.

**Kotlin extension:** Gradle + JUnit 5. Mock `MontoyaApi` where needed. Test endpoint routing + Montoya calls.

**Integration tests (`tests/integration/`, `@pytest.mark.integration`, opt-in):**
- Requires the tester to have Burp running with the bridge extension loaded (documented prerequisite — Burp Community lacks reliable headless automation, so we do not attempt to spawn it from the test harness). Real Chrome and real Flask fixture are spawned by the test.
- Chain test: browser → Burp → fixture — confirms `browser_navigate` and `burp_proxy_history` observe the same request.
- Not run in default CI.

**Fixture target app** (`tests/fixtures/target_app.py`): tiny Flask app with GET echo, POST form, reflected-XSS endpoint, simple login.

**Parley-MCP / github-MCP:** trust upstream tests. Our integration coverage is limited to "MCP starts and registers tools with Claude Code" — confirmed by the manual smoke test.

**Manual smoke test** (`README.md`): hit `/meta`, verify `/mcp` lists three connected servers, run one compound Claude prompt end-to-end.

## Dependencies

**Python runtime deps (top-level `requirements.txt`):**
- `mcp` (official Python SDK)
- `httpx`
- `websockets`
- `tomli` (only if Python <3.11; 3.13 is installed so use stdlib `tomllib`)

**Dev deps:**
- `pytest`, `pytest-asyncio`, `respx`, `pytest-cov`, `ruff`

**System deps (documented in README):**
- Python 3.13 ✓ installed
- Burp Suite 2026.2.4 ✓ installed (Community; Pro optional)
- JDK 17+ and Gradle for building the Burp extension
- Chromium or Chrome
- `GITHUB_TOKEN` environment variable with at minimum `repo` + `security_events` scopes (for github-mcp); `GHE_TOKEN` only if using GitHub Enterprise

## Out of Scope (future work)

- Firefox / WebKit support in browser-mcp (CDP is Chromium-only).
- Remote (non-loopback) deployments — current design assumes everything runs on the tester's workstation.
- Packaging as a single installable (`pip install web-mcp`) — workspace layout keeps each MCP separately installable for now.
- GUI / dashboard.
