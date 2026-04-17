---
name: testing-auth-bypass
description: Test for OWASP A07 Authentication Bypass — parameter tampering, forced-browsing of post-auth pages, SQL-injection-in-auth.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-sitemap-crawl`, `mcp-burp`.

Authenticated routes exist; bypass candidates include SQLi-in-login, default credentials, header-based auth spoofing (`X-Remote-User`), forced browsing past auth redirects.

## Signal to look for

- Login returning different response-lengths for valid vs invalid users (user enumeration).
- SSO/header-auth headers (`X-Authenticated-User`, `X-Forwarded-User`) accepted by the application.
- Redirect-to-login loops that may be stripped by intermediaries.

## Test steps

1. **Header-auth probe:** Request an authenticated page with `X-Authenticated-User: admin` or `X-Forwarded-User: admin`.
2. **SQLi-in-login:** Username `admin' --` (cross-reference `testing-sqli`).
3. **Default credentials:** Try `admin:admin`, `admin:password`, and common vendor defaults.
4. **Forced browsing:** Request an authenticated URL directly without a session; observe whether it serves content or redirects to login.
5. **Capture evidence** per `methodology-evidence-capture`.

## Tool commands

**Shell:**

```bash
curl -H "X-Remote-User: admin" https://target.example.com/admin/dashboard
# Success: dashboard renders
```

**MCP:**

Send a bypass probe via Burp Repeater:

```
burp_repeater_send(raw_base64=<b64>, host="target.example.com", port=443, secure=true, tab_name="auth-bypass-probe")
```

Expected envelope:

```json
{"ok": true, ...}
```

Compare responses across bypass techniques using `burp_proxy_history` to review all requests and isolate anomalies:

```
burp_proxy_history(filter="auth-bypass-probe")
```

Expected envelope:

```json
{"ok": true, ...}
```

## Interpret results

Any technique that produces an authenticated-view response without valid credentials is a confirmed bypass. False positive: proxy middleware may strip `X-Remote-User` at the edge; if the backend is directly reachable, test against it to confirm whether the header bypass is actually exploitable.

## Finding writeup

- **Title:** `Authentication Bypass via <technique>`
- **Severity:** Full bypass = Critical; limited bypass = High.
- **Evidence** per `methodology-evidence-capture`: the bypass request and the authenticated response.
- **Fix:** Technique-specific — enforce server-side session validation; reject trust-header inputs from clients; enforce login-redirect on every authenticated page.

## References

- OWASP WSTG ATHN-04: <https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/04-Testing_for_Bypassing_Authentication_Schema>
- PortSwigger Authentication: <https://portswigger.net/web-security/authentication>
- CWE-287: <https://cwe.mitre.org/data/definitions/287.html>

## Authorization note

Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.
