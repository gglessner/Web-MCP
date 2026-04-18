---
name: testing-jwt
description: Test for OWASP A07 JWT flaws — algorithm confusion (alg:none, HS256/RS256 swap), weak signing, kid path traversal, exp bypass.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-sitemap-crawl`, `mcp-burp`.

Target uses JWTs for auth (Bearer tokens in Authorization header or cookies).

## Signal to look for

- `Authorization: Bearer eyJhbG...` header in requests.
- Tokens whose base64-decoded header shows `"alg":"none"`.
- `kid` claim present in the token header.
- Non-refreshed tokens replayed past their `exp` timestamp.

## Test steps

1. Decode token via `jwt_tool -t <token>`.
2. alg:none attack: set `"alg":"none"`, strip signature; replay via `burp_repeater_send`.
3. HS256/RS256 confusion: sign an HS256-forged token using the server's public key as HMAC secret.
4. `kid` path traversal: `"kid":"../../dev/null"`, `"kid":"../../../dev/null"`, etc.
5. Expiration bypass: manipulate `exp` forward and replay.
6. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell:**

```bash
# alg:none exploitation
jwt_tool <token> -X a

# HS/RS confusion — sign with server public key as HMAC secret
jwt_tool <token> -X k -pk <public-key.pem>
```

**MCP:**

```python
# Replay forged token via Burp Repeater
burp_repeater_send(
    raw_base64=<b64 with forged token>,
    host="target.example.com",
    port=443,
    secure=true,
    tab_name="jwt-probe"
)
# Expected envelope on success: {"ok": true, ...}
```

Inspect the response body and status code to confirm whether the server accepted the forged token.

## Interpret results

A server returning a 200 (or otherwise authorized) response to a request carrying the forged token is a confirmed finding. False positive to rule out: client-side-only signature check (browser validates but server does not re-verify). Confirm server-side acceptance by hitting an authorization-gated endpoint (e.g., an admin-only endpoint) with the forged token and verifying that privileged content or actions are returned.

## Finding writeup

- **Title:** `JWT <technique> flaw on <endpoint>`
- **Severity:**
  - alg:none or signing-key exposure = Critical
  - Algorithm confusion = Critical
  - Weak secret = High
  - `exp` bypass = High
- **Evidence** per `methodology-evidence-capture`: decoded token, forged token, authenticated request + response.
- **Fix:** Whitelist allowed algorithms; reject `none`; use distinct keys for different roles; validate `kid` against an allow-list; enforce `exp`.

## References

- OWASP WSTG SESS-10: <https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/06-Session_Management_Testing/10-Testing_JSON_Web_Tokens>
- PortSwigger JWT attacks: <https://portswigger.net/web-security/jwt>
- CWE-347: <https://cwe.mitre.org/data/definitions/347.html>

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
