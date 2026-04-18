# Engagement Layer — Design Spec

**Date:** 2026-04-18
**Status:** Approved for implementation planning
**Scope:** Web-MCP items 1 (hard scope enforcement), 2 (credential store +
placeholder substitution), 3 (multi-identity request sending), 4 (OOB
callback receiver), plus tester-facing setup documentation.

---

## 1. Problem statement

Four gaps block effective multi-account, in-scope, credential-safe testing:

1. `browser_navigate` / `burp_http_send` will hit any host; `burp_scope_check`
   is advisory only.
2. Engagement-supplied login credentials must be typed by the LLM today, so
   the model sees them.
3. IDOR/BOLA/privesc testing needs ≥2 authenticated identities; today the LLM
   juggles raw cookies by hand.
4. Blind SSRF/XXE/SQLi/cmd-injection branches in `testing-*` skills are dead
   ends on Burp Community (no Collaborator).

All four hang off one new artefact: `engagement.toml`.

---

## 2. `engagement.toml`

Per-engagement, repo-root, gitignored. Read at MCP-server startup; only
`[identities.*]` is server-writable.

```toml
[engagement]
name = "acme-2026-q2"

[scope]
hosts = ["app.acme.com", "*.api.acme.com", "10.20.0.0/16"]

[credentials.user1]
username = "alice@acme.com"
password = "..."

[credentials.admin]
username = "root@acme.com"
password = "..."

[identities.user1]
cookies = [{name = "session", value = "...", domain = "app.acme.com"}]
headers = {Authorization = "Bearer ..."}
captured_at = "2026-04-18T20:00:00Z"

[oob]
provider = "interactsh"   # or "selfhost"
```

**Behaviour when absent:** fail-open (current behaviour preserved).
**Behaviour when present with `hosts = []`:** fail-closed.

`[scope].hosts` entries: exact host, `*.suffix` wildcard, or CIDR.

---

## 3. Item 1 — Hard scope enforcement

`common/engagement.py`:

```python
class Engagement:
    @classmethod
    def load(cls, path="engagement.toml") -> "Engagement | None": ...
    def in_scope(self, host_or_url: str) -> bool: ...
    def scope_hosts(self) -> list[str]: ...
```

Guard applied at each server's `call_tool` chokepoint, before dispatch:

| Tool | Host source |
|---|---|
| `browser_navigate` | `urlparse(args["url"]).hostname` |
| `browser_click`/`_fill`/`_eval`/`_query`/`_snapshot`/`_screenshot`/`_wait_for`/`_get_response_body`/`_network_log`/`_cookies` | session's current page host (cached on each navigate) |
| `burp_http_send`, `burp_repeater_send`, `burp_intruder_launch` | `args["host"]` |
| `burp_scanner_scan` | `urlparse(args["url"]).hostname` |

Out of scope → `error_envelope(ErrorCode.OUT_OF_SCOPE, "<host> not in engagement.toml [scope].hosts")`.
`ErrorCode.OUT_OF_SCOPE` is a new member of `common/mcp_base.ErrorCode`.

At burp-mcp startup, `[scope].hosts` is pushed to Burp via the bridge's
`/scope/modify` so Burp's GUI scope matches.

---

## 4. Item 2 — Credential placeholder substitution + redaction

`common/credstore.py`:

```python
class CredStore:
    def __init__(self, engagement: Engagement | None): ...
    def expand(self, args: Any) -> Any: ...      # recursive str/dict/list walk
    def filter(self, result: Any) -> Any: ...    # mcp_armor ContentFilter wrapper
```

**Placeholder grammar:** `{{CRED:<name>.<field>}}`. `<name>` = a
`[credentials.*]` table; `<field>` = any key in it. Unknown placeholder →
`error_envelope(ErrorCode.BAD_INPUT, "unknown credential placeholder ...")`.

**Expansion** runs on tool **inputs** at the chokepoint, before dispatch.
Special case: `burp_http_send`/`burp_repeater_send` `raw_base64` is decoded,
expanded, re-encoded.

**Redaction** runs on tool **outputs** after dispatch. At startup, every
`[credentials.*].*` value and every `[identities.*]` cookie/header value is
registered as an exact-match `re.escape()` pattern in an
`mcp_armor.ContentFilter` with replacement
`[REDACTED:CRED:<name>.<field>]` / `[REDACTED:IDENT:<name>.<kind>]`.

`mcp_armor` is lifted from `MCPs/github-mcp/MCPs/libs/mcp_armor/` to
`common/mcp_armor/` (copied, with an `UPSTREAM.txt` pointing at
`gglessner/MCP-Armor`) so browser-mcp and burp-mcp import it directly.

---

## 5. Item 3 — Multi-identity

### Capture (option c — manual seed *and* tool capture)

New browser-mcp tool:

```
browser_capture_identity(name: str) -> {cookies: int, headers: [str], captured_at}
```

Reads `Network.getAllCookies` (filtered to in-scope domains) plus the
`Authorization` header from the most recent in-scope request in the session's
network log. Writes `[identities.<name>]` to `engagement.toml` atomically
(`tempfile.mkstemp` + `os.replace`). Re-registers the new values in the
`CredStore` redaction filter.

Manual seed: tester edits `[identities.*]` directly; server picks it up at
startup.

### Use

`burp_http_send` and `burp_repeater_send` gain optional `as_identity: str`.
When set: decode `raw_base64` → replace/insert `Cookie:` header from
`[identities.<name>].cookies` → replace/insert each
`[identities.<name>].headers` entry → re-encode. Missing identity →
`BAD_INPUT`.

New browser-mcp tool `browser_apply_identity(name: str)` calls
`Network.setCookies` with the stored jar for browser-side authenticated
crawling under that identity.

---

## 6. Item 4 — OOB callback receiver

`common/oob.py` wraps `interactsh-client` (subprocess, JSON-line output).
Exposed via two new burp-mcp tools:

| Tool | Returns |
|---|---|
| `oob_get_payload()` | `{domain, url}` — the unique interaction domain to embed in payloads |
| `oob_poll(since_id: int = 0)` | `[{id, protocol, remote_addr, timestamp, raw_request}, ...]` |

`[oob].provider = "selfhost"` swaps in a stdlib `http.server` +
`socketserver` UDP-53 catcher bound on `[oob].listen` (for air-gapped labs);
same tool surface.

`testing-ssrf`, `testing-xxe`, `testing-command-injection`, `testing-sqli`
skills each gain a short "Blind detection" subsection referencing these tools.

---

## 7. Chokepoint pipeline (both servers)

```
@server.call_tool()
async def call_tool(name, arguments):
    arguments = credstore.expand(arguments)          # item 2 in
    if not engagement.permits(name, arguments, session_state):
        return [TextContent(text=json.dumps(OUT_OF_SCOPE_ERR))]   # item 1
    result = await handle(name, arguments)           # existing dispatch (incl. item 3 as_identity)
    result = credstore.filter(result)                # item 2 out
    return [TextContent(text=json.dumps(result))]
```

---

## 8. Tester-facing documentation (deliverable)

New `docs/engagement-setup.md`, linked from README under the existing
"Running multiple engagements on one machine" section. Covers, in order:

1. Copy the repo per engagement (recap of README §multi-engagement).
2. Write `engagement.toml`: scope hosts, credentials per test account.
3. Launch Burp with the per-engagement bridge port; confirm scope auto-loaded.
4. First-session walkthrough: `browser_launch` → `browser_navigate` to login →
   `browser_fill` with `{{CRED:user1.password}}` → `browser_capture_identity("user1")`
   → repeat for `user2` → `burp_http_send(..., as_identity="user2")` IDOR probe.
5. OOB: `oob_get_payload()` → embed → `oob_poll()`.
6. What `[REDACTED:CRED:...]` / `[REDACTED:IDENT:...]` markers mean in output.
7. Troubleshooting: `OUT_OF_SCOPE` errors, unknown-placeholder errors,
   stale-identity re-capture.

`methodology-scoping` skill gains a step: "write `engagement.toml` before
recon; the scope block is the mechanical guardrail downstream skills rely on."

---

## 9. Testing

| Module | Tests |
|---|---|
| `common/engagement.py` | host/wildcard/CIDR match table; absent-file fail-open; empty-hosts fail-closed; atomic identity write round-trip |
| `common/credstore.py` | expand on str/nested-dict/list; base64 round-trip; unknown placeholder error; redaction of cred + identity values; named-group replacement token |
| `common/oob.py` | mock interactsh JSON-line stream → poll returns parsed interactions; selfhost catcher receives HTTP/DNS hit |
| browser-mcp | `browser_capture_identity` writes correct TOML; `browser_apply_identity` issues `Network.setCookies`; navigate to out-of-scope host → `OUT_OF_SCOPE` |
| burp-mcp | `burp_http_send` with `as_identity` injects Cookie header; out-of-scope host → `OUT_OF_SCOPE`; `oob_*` tools wired |
| integration | end-to-end against `tests/fixtures/target_app.py`: login as user1 via placeholder → capture → replay as user1 via `as_identity` → assert 200; replay as user2 → assert 403 |

---

## 10. Out of scope (this spec)

- Findings store (#5 from the evaluation list)
- Engagement bootstrap script (#6)
- Rate limiter (#7)
- Response diff tool (#8)
- Per-identity browser profiles (one Chrome per identity)
- Credential rotation / expiry detection beyond manual re-capture
