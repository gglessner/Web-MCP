---
name: testing-cors
description: Test for OWASP A05 CORS misconfiguration — wildcard with credentials, reflected origin, null origin, subdomain trust.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-js-analysis`, `recon-sitemap-crawl`, `mcp-burp`.

Use this skill when the target exposes authenticated JSON endpoints that serve `Access-Control-Allow-Origin`. CORS misconfigurations on authenticated endpoints allow cross-origin sites to read sensitive data on behalf of a victim user.

## Signal to look for

- `Access-Control-Allow-Origin: *` returned alongside `Access-Control-Allow-Credentials: true`
- `Access-Control-Allow-Origin` reflects the value of the incoming `Origin` header verbatim
- `null` origin accepted (i.e., `Access-Control-Allow-Origin: null` with `Access-Control-Allow-Credentials: true`)

## Test steps

1. Send a request with `Origin: https://attacker.com`; inspect the response's `Access-Control-Allow-Origin` header to determine whether the origin is reflected or otherwise trusted.
2. Null origin: repeat the request with `Origin: null` and check whether `Access-Control-Allow-Origin: null` is returned with credentials allowed.
3. Subdomain trust: send `Origin: https://evil.target.example.com` to determine whether the application blindly trusts any subdomain of its own domain.
4. Confirm exploitability: craft a page hosted at `attacker.com` that uses `fetch()` with `credentials: "include"` to request the authenticated endpoint cross-origin; verify the response body is accessible to the attacker-controlled page.
5. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell:**

```bash
curl -sI -H "Origin: https://attacker.com" https://target.example.com/api/profile | grep -i 'access-control'
# Success: Access-Control-Allow-Origin: https://attacker.com + Allow-Credentials: true
```

**MCP:**

Send the probe through Burp Repeater:

```
burp_repeater_send(raw_base64=<b64 with Origin header>, host="target.example.com", port=443, secure=true, tab_name="cors-probe")
```

Retrieve the response headers from proxy history:

```
burp_proxy_request(id=<N>)
```

Expected envelope for a successful MCP call:

```json
{"ok": true, ...}
```

## Interpret results

- `Access-Control-Allow-Origin` reflecting the attacker-controlled origin combined with `Access-Control-Allow-Credentials: true` = exploitable; a cross-origin attacker can read authenticated responses.
- `Access-Control-Allow-Origin: *` without `Access-Control-Allow-Credentials: true` = weaker finding; credentials are not exposed, but public data may be unnecessarily disclosed to any origin.
- No reflection or a fixed allow-list origin returned = not vulnerable via this vector.

## Finding writeup

- **Title:** `CORS Misconfiguration at <endpoint>`
- **Severity:** Authenticated cross-origin read = High to Critical; reflective origin without credentials enabled = Medium.
- **Evidence** per `methodology-evidence-capture`: the request containing the spoofed `Origin` header, the response showing the reflected `Access-Control-Allow-Origin` and `Access-Control-Allow-Credentials` headers, and the cross-origin proof-of-concept demonstrating data retrieval.
- **Fix:** Maintain an explicit server-side allow-list of trusted origins; never reflect the `Origin` header value directly into `Access-Control-Allow-Origin`; never combine a wildcard (`*`) origin with `Access-Control-Allow-Credentials: true`.

## References

- OWASP WSTG CLNT-07: <https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/07-Testing_Cross_Origin_Resource_Sharing>
- PortSwigger CORS: <https://portswigger.net/web-security/cors>
- CWE-942: <https://cwe.mitre.org/data/definitions/942.html>

## Authorization note

Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.
