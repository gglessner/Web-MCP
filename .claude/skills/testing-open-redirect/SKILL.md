---
name: testing-open-redirect
description: Test for Open Redirect in login-next, SSO-return-to, and download parameters — enables phishing and SSRF pivots.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-api-enum`, `mcp-burp`.

Parameters like `?next=`, `?return_to=`, `?url=`, `?redirect=` that control the `Location:` header after an authenticated action are prime targets for open redirect testing. These parameters appear in login flows, SSO callbacks, post-logout redirects, and file download handlers, and a misconfigured allow-list or absent validation can let an attacker redirect a victim to an arbitrary external URL.

## Signal to look for

- Parameters that carry URL-like values: `?next=`, `?return_to=`, `?redirect=`, `?url=`, `?dest=`, `?target=`.
- 302 (or 301/303/307/308) responses whose `Location:` header echoes a user-controlled value verbatim or with minimal transformation.
- Login flows that append a `?next=` parameter to preserve the originally requested URL before authentication.
- SSO or OAuth return-to parameters that accept absolute URLs rather than relative paths.
- Download or preview endpoints that construct a redirect to a resource URL supplied by the caller.

## Test steps

1. **Absolute URL probe:** submit `?next=https://attacker.com` and observe whether the `Location:` header in the response points to `https://attacker.com`.
2. **Scheme-less probe:** submit `?next=//attacker.com` to bypass simple `https://` prefix checks; browsers treat `//` as protocol-relative.
3. **Userinfo bypass:** submit `?next=https://target.example.com@attacker.com`; the authority of this URL is `attacker.com`, but naive string-prefix checks may match `target.example.com`.
4. **Null and whitespace bypass:** submit `?next=%00https://attacker.com` or `?next=%09https://attacker.com` to probe parsers that strip leading control characters before validation.
5. **Inspect `Location:` header** in the response for each probe and record whether the attacker-controlled host appears.
6. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell:**

```bash
curl -sI "https://target.example.com/login?next=https://attacker.com" | grep -i 'location'
# Success: Location: https://attacker.com
```

**MCP:**

Send the probe through Burp Repeater for full response header capture:

```
burp_repeater_send(raw_base64=<b64>, host="target.example.com", port=443, secure=true, tab_name="redirect-probe")
```

Expected envelope on success:

```json
{"ok": true, "response": {"status": 302, "headers": {"Location": "https://attacker.com"}, ...}}
```

Retrieve a specific proxy history entry for full response headers:

```
burp_proxy_request(id=<N>)
```

Expected envelope:

```json
{"ok": true, "request": {...}, "response": {"headers": {"Location": "https://attacker.com"}, ...}}
```

## Interpret results

- **Confirmed:** the `Location:` header in the redirect response contains the attacker-controlled host (`attacker.com`) without modification.
- **Partial / allow-list weakness:** the server performs a host suffix match rather than an exact-match check — for example, it allows any host ending in `foo.com`, so `evilfoo.com` passes. Verify whether the allow-list enforces an exact match (e.g., `FooBank.com`) or only a suffix (`foo.com`), and document which bypass strings succeed.
- **Not vulnerable:** the server rewrites or rejects the parameter and redirects only to a hard-coded or relative path.

## Finding writeup

- **Title:** `Open Redirect in <parameter>` (e.g., `Open Redirect in ?next= parameter on /login`).
- **Severity:**
  - SSO or login-flow redirect used to facilitate phishing: Medium-High.
  - Pure UX redirect with no authentication context: Low.
- **Evidence** per `methodology-evidence-capture`: the full request URL including the payload parameter, and the raw response showing the `Location:` header with the attacker-controlled value.
- **Fix:** validate the redirect target against an explicit allow-list of permitted destinations; prefer relative URLs only; unconditionally reject scheme-less URLs (`//`), userinfo components (`user@host`), and any URL whose parsed host does not exactly match an allow-listed domain.

## References

- OWASP WSTG CLNT-04: `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/04-Testing_for_Client_Side_URL_Redirect`
- PortSwigger (host-header / redirect topic): `https://portswigger.net/kb/issues/00500100_open-redirection-reflected`
- CWE-601: `https://cwe.mitre.org/data/definitions/601.html`

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
