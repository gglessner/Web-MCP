---
name: testing-cache-poisoning
description: Test for Web Cache Poisoning — unkeyed-input reflection, cache-key manipulation, cache deception.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-tech-fingerprinting`, `mcp-burp`.

Target has a cache layer (CDN, reverse proxy) between users and the origin.

## Signal to look for

- `X-Cache:` response header indicating a cache hit or miss.
- `CF-Cache-Status:` response header from Cloudflare-backed CDN deployments.
- `Age:` response header showing how long the cached object has been stored.
- Static-content URLs with cached responses (images, JS, CSS, etc.).
- CDN fingerprint identified during tech fingerprinting.

## Test steps

1. Identify a cached endpoint by observing `X-Cache: HIT`, `CF-Cache-Status: HIT`, or a non-zero `Age:` header in the response.
2. Run Burp Suite's "Param Miner" extension (Pro) against the cached endpoint to discover unkeyed inputs — headers that alter the response body or behavior but are excluded from the cache key.
3. Once an unkeyed header is confirmed, craft a request that injects a malicious payload via that header (e.g., `X-Forwarded-Host: evil.com`) and send it to prime the cache.
4. Re-fetch the same URL without the injected header from a different browser session or IP to confirm the poisoned response is being served to other users.
5. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell — manual cache probing:**

```
curl -H "X-Forwarded-Host: evil.com" https://target.example.com/
curl https://target.example.com/    # re-fetch without header, compare
```

**MCP — Burp Repeater workflow:**

Send the poisoning request with the unkeyed header:

```
burp_repeater_send(raw_base64=<b64 of poisoning request>, host="target.example.com", port=443, secure=true, tab_name="cache-poison")
```

Expected envelope:

```json
{"ok": true, "response": { ... }}
```

Re-fetch without the injected header to compare responses:

```
burp_repeater_send(raw_base64=<b64 of clean request>, host="target.example.com", port=443, secure=true, tab_name="cache-poison-verify")
```

Compare the two responses — if the clean fetch returns the poisoned content, the cache is confirmed poisoned.

## Interpret results

- Poisoned response persists across subsequent clean fetches = confirmed web cache poisoning.
- If the poisoned response includes injected JavaScript or markup that executes in a victim's browser, the severity escalates to persistent XSS.
- DoS-only finding: if poisoning causes the cache to serve a 5xx error to subsequent visitors, this is still a valid finding (denial of service via cache poisoning).

## Finding writeup

- **Title:** Web Cache Poisoning via `<header>` (e.g., `X-Forwarded-Host`).
- **Severity:**
  - Persistent XSS delivered via poisoned cache = Critical.
  - DoS-only (cached 5xx served to users) = High.
- **Evidence** per `methodology-evidence-capture`: the poisoning request with the unkeyed header, a subsequent clean fetch showing the poisoned response, and the cache-status headers (`X-Cache`, `CF-Cache-Status`, `Age`) confirming a cache hit.
- **Fix:**
  - Include the affected header in the cache key so different header values produce separate cache entries.
  - Strip unknown or unrecognized headers at the cache layer before storing or forwarding responses.
  - Disable caching for authenticated or personalized routes to limit the blast radius of any future poisoning attempt.

## References

- OWASP Web Cache Poisoning reference: `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/`
- PortSwigger Web cache poisoning: `https://portswigger.net/web-security/web-cache-poisoning`
- CWE-349: `https://cwe.mitre.org/data/definitions/349.html`

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
