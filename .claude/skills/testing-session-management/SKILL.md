---
name: testing-session-management
description: Test for OWASP A07 Session Management flaws — predictable IDs, missing rotation, fixation, weak cookie flags, missing expiry.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-sitemap-crawl`, `mcp-burp`.

Use this skill against an authenticated application where session cookies or tokens govern user state.

## Signal to look for

- `Set-Cookie` headers missing the `Secure` flag, `HttpOnly` flag, or `SameSite` attribute.
- Session IDs that are short, sequential, or timestamp-based, indicating low entropy.
- Unchanged session ID across the login boundary, indicating session fixation.

## Test steps

1. Collect `Set-Cookie` headers via `burp_proxy_history(contains="Set-Cookie")`.
2. Inspect cookie flags; note any missing `Secure`, `HttpOnly`, or `SameSite` attributes.
3. Fixation: obtain a pre-authentication session ID, complete login, then observe whether the server issues a new (rotated) session ID.
4. Predictability: collect 100 or more session IDs via repeated logins; assess entropy by visual inspection and/or Burp Sequencer (Pro).
5. Expiration: log in, wait an extended idle period, then retry the session; observe whether idle sessions are invalidated.
6. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell — inspect Set-Cookie flags directly:**

```bash
curl -sI -c - https://target.example.com/login | grep -i 'set-cookie'
# Success: Set-Cookie visible; inspect flags
```

**MCP — pull Set-Cookie headers from proxy history:**

```
burp_proxy_history(host="target.example.com", contains="Set-Cookie", limit=100)
```

Expected envelope:

```json
{"ok": true, "items": [...]}
```

**MCP — retrieve raw Set-Cookie header from a specific request:**

```
burp_proxy_request(id=<N>)
```

Expected envelope:

```json
{"ok": true, "request": "...", "response": "..."}
```

## Interpret results

- **Missing flags:** Each cookie that lacks `Secure`, `HttpOnly`, or `SameSite` is a distinct finding; note the cookie name and the missing attribute(s).
- **Session fixation confirmed:** Pre-login session ID matches the post-login session ID, meaning the server did not rotate the identifier on authentication.
- **Predictability confirmed:** A consistent pattern (incrementing counter, timestamp component, truncated random value) is visible across the sampled IDs.
- **Idle-expiration failure confirmed:** A session issued before the idle window is still accepted by the server after extended inactivity.

## Finding writeup

**Title:** `Session <issue> on <cookie>`

**Severity mapping:**
- Session fixation — High
- Predictable session IDs — High
- Missing `Secure` flag — Medium
- Missing `HttpOnly` flag — Medium

**Evidence** per `methodology-evidence-capture`: include the raw `Set-Cookie` header excerpt and a side-by-side comparison of the before-login and after-login cookie values.

**Fix:**
- Serve the application over HTTPS only and set the `Secure` flag on all session cookies.
- Set the `HttpOnly` flag to prevent JavaScript access.
- Set `SameSite=Lax` as the default to mitigate CSRF-assisted fixation.
- Rotate the session ID immediately upon successful login.
- Generate session IDs using a cryptographically random source of sufficient length (128 bits minimum).
- Enforce server-side idle-session expiry and invalidate sessions on logout.

## References

- OWASP WSTG SESS-02: <https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/06-Session_Management_Testing/02-Testing_for_Cookies_Attributes>
- PortSwigger Authentication (session section): <https://portswigger.net/web-security/authentication>
- CWE-384: <https://cwe.mitre.org/data/definitions/384.html>

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
