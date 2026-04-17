---
name: testing-missing-function-access
description: Test for OWASP A01 Missing Function-Level Access Control — forced browsing to admin/privileged endpoints without checks.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-content-discovery`, `recon-api-enum`, `mcp-burp`.

Use this skill when the application has distinct privilege tiers such as admin, moderator, and regular user. Each endpoint that performs a privileged operation should enforce the caller's role server-side; this test verifies that enforcement is present and cannot be bypassed by simply knowing the URL.

## Signal to look for

- Endpoints under `/admin`, `/internal`, or `/api/v1/admin`.
- Endpoints that appear only in admin-facing UIs but are not documented in public API references.
- Response differential between authenticated non-admin and unauthenticated requests returns 200 instead of 302 or 403, indicating the server serves the resource without verifying role.

## Test steps

1. Enumerate admin paths using wordlists from `recon-content-discovery`.
2. Issue each discovered request as a low-privileged authenticated user via `burp_repeater_send`.
3. Observe the response code: 200 indicates no role check; 403 indicates the endpoint is protected; 302 to a login page also indicates protection.
4. Also test unauthenticated access by removing the session cookie and replaying each request.
5. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell — forced browsing with a low-privileged session:**

```bash
ffuf -u https://target.example.com/FUZZ -w admin-paths.txt -H "Cookie: session=<LOWPRIV>" -mc 200
# Success: any 200 responses indicate missing role check
```

**MCP — list admin paths Burp has already seen:**

```
burp_sitemap(prefix="https://target.example.com/admin", limit=100)
```

Example response envelope:

```json
{"ok": true, "items": [...]}
```

**MCP — replay each path under a low-privileged session:**

```
burp_repeater_send(raw_base64=<b64>, host="target.example.com", port=443, secure=true, tab_name="funcaccess-probe")
```

Example response envelope:

```json
{"ok": true, "response": {"status": 200, "body": "..."}}
```

## Interpret results

A 200 response to an admin endpoint issued under a non-admin session is a confirmed finding. False positive scenario: the endpoint exists and returns HTTP 200 but delivers empty or stub data to non-admin callers. Verify the response body contains admin-only information by comparing it against the same request issued with valid admin credentials. If the non-admin response is substantively different (empty list, placeholder text), the control may be soft rather than absent.

## Finding writeup

- **Title:** Missing Function-Level Access Control at `<endpoint>`.
- **Severity:** Admin functionality accessible via a low-privileged session = Critical; same functionality accessible without any session = Critical.
- **Evidence** per `methodology-evidence-capture`: include the low-privileged request and the full response demonstrating admin data, plus the same request replayed with admin credentials for comparison.
- **Fix:** Enforce role authorization on every admin endpoint at the middleware layer using RBAC so that each new route inherits the check automatically rather than requiring per-handler implementation.

## References

- OWASP WSTG ATHZ-02: <https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/05-Authorization_Testing/02-Testing_for_Bypassing_Authorization_Schema>
- PortSwigger Access Control: <https://portswigger.net/web-security/access-control>
- CWE-284: <https://cwe.mitre.org/data/definitions/284.html>

## Authorization note

Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.
