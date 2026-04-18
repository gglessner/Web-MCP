---
name: testing-header-injection
description: Test for HTTP Header Injection — CRLF, host-header injection, cache-key injection — affecting response splitting and routing.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-sitemap-crawl`, `mcp-burp`.

Use this skill when user input flows into HTTP response headers, `Location:` redirects, or `Host:`-based URL construction (for example, password-reset emails that build absolute URLs from the incoming Host header).

## Signal to look for

- `Location:` redirect whose destination is derived from a user-supplied query parameter or path segment.
- `Set-Cookie:` header containing user-controlled values without sanitization.
- `Host:` header used to build absolute URLs in response bodies, emails, or redirects.

## Test steps

1. **CRLF probe:** inject `%0D%0A` (URL-encoded CRLF) into a parameter that is reflected into a response header (e.g., a redirect destination). Observe whether the injected text appears as a new response header line, indicating response splitting.
2. **Host-header:** send `Host: attacker.com` in the request; observe whether links in the response body or emailed artifacts (e.g., password-reset links) use `attacker.com` as the domain.
3. **Cache-key probe:** vary a non-keyed header (`X-Forwarded-Host`, `X-Forwarded-Scheme`) and observe whether the downstream cache serves the poisoned response to subsequent clean requests (requests that omit the injected header).
4. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell:**

```bash
curl -sI -H 'Host: attacker.com' https://target.example.com/reset
# Success: reset link in response body or subsequent email uses attacker.com
```

**MCP:**

```python
# Replay a request with a CRLF payload via Burp Repeater
burp_repeater_send(
    raw_base64=<b64 with CRLF payload>,
    host="target.example.com",
    port=443,
    secure=true,
    tab_name="crlf-probe"
)

# Compare baseline vs. injected response headers in proxy history
burp_proxy_history(host="target.example.com")
```

## Interpret results

- **Response splitting confirmed** when the injected CRLF sequence produces a new header line in the server response (e.g., an `X-Injected:` header appearing below the intended header).
- **Host-header injection confirmed** when an out-of-band artifact — such as an email containing a password-reset link — uses the spoofed host (`attacker.com`) rather than the legitimate domain.
- **Cache poisoning confirmed** when an unauthenticated re-fetch of the same URL (without the injected header) returns the poisoned response served from cache.

## Finding writeup

- **Title:** `HTTP Header Injection via <parameter>`
- **Severity:**
  - Response splitting enabling XSS: High
  - Cache poisoning: High
  - Reflected host used in password-reset links: Critical
- **Evidence** per `methodology-evidence-capture`: the request containing the CRLF or spoofed Host payload, the response headers showing the injection effect, and a screenshot of the email or reset link using the attacker-controlled host.
- **Fix:** reject `\r\n` and non-ASCII characters in all header-bound inputs; validate the `Host` header against a strict allow-list of known application domains.

## References

- OWASP WSTG INPV-15 (HTTP Splitting/Smuggling): `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/15-Testing_for_HTTP_Splitting_Smuggling`
- PortSwigger HTTP host header attacks: `https://portswigger.net/web-security/host-header`
- CWE-93: `https://cwe.mitre.org/data/definitions/93.html`

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
