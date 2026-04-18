---
name: mcp-burp
description: Drive Burp Suite (Community or Pro) via burp-mcp for proxy history analysis, Repeater replay, scope management, sitemap review, and Pro-only Scanner/Intruder control.
---

# Using burp-mcp for HTTP/S penetration testing

## When to use

When HTTP/S traffic is the subject of a test: inspecting proxy history,
replaying requests with mutations, managing scope, reviewing the sitemap,
or launching automated scans (Pro only). Use the `mcp-browser` skill to
drive a real browser and route traffic through Burp; use this skill to
then interrogate and replay what Burp captured.

Prerequisites:

1. `burp-mcp` registered in Claude Code (see top-level
   `claude_config.example.json`).
2. The Kotlin bridge jar loaded in a running Burp instance:
   `MCPs/burp-mcp/burp-ext/BUILD.md` explains the build and load steps.
   Burp → Extensions → Output must show
   `burp-mcp-bridge listening on 127.0.0.1:8775`.

## Signal to look for

- Target is an HTTP/S web application or API.
- Need to replay a specific captured request with modified headers,
  parameters, or body.
- Need to add or remove URLs from Burp's scope before a scan.
- Need to enumerate what Burp's sitemap already knows about the target.
- Pro edition: need an active or passive scan, or need to launch Intruder
  against a parameterised request.

## Test steps

1. Call `burp_meta()` — verify the bridge is live and note the edition
   (`COMMUNITY_EDITION` vs `PRO_EDITION`).
2. Call `burp_scope_modify(add=["https://target.example.com"])` — set
   scope before any scan or history filter.
3. Call `burp_proxy_history(host="target.example.com", limit=50)` — page
   through recent requests; narrow with `method`, `status`, or `contains`.
4. Call `burp_proxy_request(id=<N>)` — retrieve the full raw
   request/response for a specific history entry.
5. Send a probe and read the response in one call:
   `burp_http_send(raw_base64=<b64>, host="target.example.com", port=443, secure=true, save_to="F-001/probe-1")`
   — returns `{status, headers, body_preview, body_len, time_ms, saved}`. Use this
   for all automated probing (boolean diffs, error-string detection, timing).
6. (Optional) Open the same request in the Burp UI for manual follow-up:
   `burp_repeater_send(raw_base64=<b64>, host=..., port=443, secure=true, tab_name="probe-1")`.
7. Review the sitemap: `burp_sitemap(prefix="https://target.example.com/api")`.
8. (Pro only) Start an active scan: `burp_scanner_scan(url="https://target.example.com", mode="active")`.
9. (Pro only) Poll for issues: `burp_scanner_issues()`.
10. (Pro only) Send to Intruder: `burp_intruder_launch(raw_base64=<b64>, host="target.example.com", port=443, secure=true)`.
11. Inspect or update match-replace rules:
    `burp_match_replace_get()` then `burp_match_replace_set(rules=[...])`.
12. Persist a proxy-history entry as evidence:
    `burp_save_request(id=<N>, save_to="F-001/baseline")` — writes
    `evidence/F-001/baseline.request.http` and `.response.http`.

## Tool commands

```
# Verify bridge is live
burp_meta()
# Success: {"ok": true, "data": {"edition": "COMMUNITY_EDITION", "version": "...", "bridge_version": "0.1.0"}}
# Failure: {"ok": false, "error": {"code": "BURP_UNAVAILABLE", ...}}

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

# Scope
burp_scope_check(urls=["https://target.example.com/admin"])
# Success: {"ok": true, "data": {"checks": {"https://target.example.com/admin": true}}}

burp_scope_modify(add=["https://target.example.com"], remove=[])
# Success: {"ok": true, "data": {"added": 1, "removed": 0}}

# History browse
burp_proxy_history(host="target.example.com", method="POST", status=200, limit=20)
# Success: {"ok": true, "data": {"items": [...], "total": 47, "cursor": 20}}

# Pull one full request
burp_proxy_request(id=12)
# Success: {"ok": true, "data": {"request": "...", "response": "...", "host": "...", "port": 443}}
# Failure: {"ok": false, "error": {"code": "BAD_INPUT", ...}}

# Repeater — base64 the raw bytes of the request
burp_repeater_send(raw_base64="R0VUIC9hcGkvdXNlcnMgSFRUUC8xLjENCkhvc3Q6IHRhcmdldC5leGFtcGxlLmNvbQ0KDQo=",
                   host="target.example.com", port=443, secure=true, tab_name="probe-1")
# Success: {"ok": true, "data": {"tab_id": "..."}}

# Sitemap
burp_sitemap(prefix="https://target.example.com/api", limit=100)
# Success: {"ok": true, "data": {"items": [...], "total": 23}}

# Match-replace
burp_match_replace_get()
# Success: {"ok": true, "data": {"rules": [...]}}

burp_match_replace_set(rules=[{"match": "X-Debug: false", "replace": "X-Debug: true",
                                "type": "request_header", "enabled": true}])
# Success: {"ok": true, "data": {"count": 1}}

# --- Pro-only tools: Community edition returns PRO_REQUIRED ---
burp_scanner_scan(url="https://target.example.com", mode="active")
# Pro: {"ok": true, "data": {"scan_id": "..."}}
# Community: {"ok": false, "error": {"code": "PRO_REQUIRED", "message": "...", "detail": {}}}

burp_scanner_issues()
# Pro: {"ok": true, "data": {"issues": [...]}}
# Community: {"ok": false, "error": {"code": "PRO_REQUIRED", "message": "...", "detail": {}}}

burp_intruder_launch(raw_base64="...", host="target.example.com", port=443, secure=true)
# Pro: {"ok": true, "data": {"tab_id": "..."}}
# Community: {"ok": false, "error": {"code": "PRO_REQUIRED", "message": "...", "detail": {}}}
```

## Interpret results

All tools return `{"ok": true, "data": {...}}` on success or
`{"ok": false, "error": {"code": "...", "message": "...", "detail": {...}}}` on failure.

Error codes:

- `BURP_UNAVAILABLE` — bridge jar not loaded or Burp is not running.
  Fix: build and load the jar per `MCPs/burp-mcp/burp-ext/BUILD.md`,
  verify Burp → Extensions → Output shows the listening message.
- `PRO_REQUIRED` — Community edition attempting a Pro-only tool
  (`burp_scanner_scan`, `burp_scanner_issues`, `burp_intruder_launch`).
  Fix: upgrade to Burp Pro, or skip that step.
- `BAD_INPUT` — supplied id is not in history or URL is malformed.
  Fix: recheck the id from `burp_proxy_history`, validate the URL.
- `UPSTREAM_HTTP` — bridge returned an unexpected non-standard error.
  Check Burp's Extensions → Output tab for the stack trace.

False positive to watch for: `burp_proxy_history` returns `total=0` even
though traffic has been sent. Most likely cause: Burp's upstream proxy
setting is intercepting before history, or the browser is not routing
through `127.0.0.1:8080`. Confirm browser traffic passes through Burp
by checking Burp → Proxy → Intercept is off and the browser proxy is set.

## Finding writeup

- **Title pattern:** `<Issue> via <endpoint> (HTTP <method>)` — e.g.
  "Insecure Direct Object Reference via `/api/users/<id>` (HTTP GET)".
- **Severity guidance:** Reference the `reporting-severity-rubric` skill.
  Unauthenticated access to sensitive data is typically High or Critical;
  authenticated IDOR is Medium to High depending on data sensitivity.
- **Description template:** *"The `<parameter>` value is accepted without
  authorisation check at `<endpoint>`, allowing an attacker with a valid
  session to access or modify resources belonging to other users."*
- **Reproduction steps:** provide the numbered `burp_*` tool calls
  verbatim, from `burp_proxy_history` to the decisive `burp_repeater_send`
  response, so a reviewer can paste them into a new Claude session.
  Include the raw request and response excerpts from `burp_proxy_request`.
- **Suggested fix:** enforce authorisation at the server before returning
  the resource; do not rely on client-supplied IDs alone.

## References

- burp-mcp README: `MCPs/burp-mcp/README.md`
- Bridge build steps: `MCPs/burp-mcp/burp-ext/BUILD.md`
- PortSwigger Montoya API:
  https://portswigger.github.io/burp-extensions-montoya-api/javadoc/
- OWASP WSTG — Testing for Proxying:
  https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/

## Authorization note

Only use against systems you are authorized to test. This skill assumes the
user has obtained written authorization. If authorization is uncertain, stop
and confirm scope before proceeding.
