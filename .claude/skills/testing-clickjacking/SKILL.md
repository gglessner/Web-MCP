---
name: testing-clickjacking
description: Test for Clickjacking — missing X-Frame-Options or frame-ancestors CSP directive on sensitive state-changing pages.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-sitemap-crawl`, `mcp-browser`.

Sensitive state-changing pages should reject framing via `X-Frame-Options: DENY/SAMEORIGIN` or CSP `frame-ancestors`. If a page that performs destructive or privileged actions (account deletion, payment confirmation, permission grants) can be embedded in an attacker-controlled frame, an adversary can trick an authenticated user into triggering those actions invisibly — a UI-redress attack.

## Signal to look for

Sensitive pages — such as delete account, confirm payment, and grant permission endpoints — that are missing both `X-Frame-Options` and a `Content-Security-Policy` header containing a `frame-ancestors` directive. Either header alone is sufficient protection; the absence of both is the vulnerable condition.

## Test steps

1. Check headers: `curl -sI https://target.example.com/settings`.
2. If missing: craft PoC HTML with `<iframe src="<target>"></iframe>`.
3. Use `browser_navigate` to navigate to the hosted PoC; visually confirm the target renders inside the frame.
4. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell — check framing-protection headers:**

```bash
curl -sI https://target.example.com/settings | grep -iE 'x-frame-options|content-security-policy'
# Success: neither header present
```

**MCP — load PoC and capture visual proof:**

```
browser_navigate(url="file:///tmp/clickjack-poc.html")
```

Expected envelope:

```json
{"ok": true, "url": "file:///tmp/clickjack-poc.html", "status": 200}
```

```
browser_screenshot(full_page=true)
```

Expected envelope:

```json
{"ok": true, "path": "/tmp/screenshot-clickjack.png", "width": 1280, "height": 900}
```

## Interpret results

If the target page renders inside the iframe when the PoC is loaded in the browser, the page is vulnerable to clickjacking.

False positive consideration: `Content-Security-Policy: frame-ancestors 'none'` provides equivalent or stronger protection than `X-Frame-Options: DENY`. A page missing `X-Frame-Options` but carrying a CSP `frame-ancestors` directive is protected. Always check the full CSP value before reporting; a `frame-ancestors 'none'` or `frame-ancestors 'self'` is sufficient even without XFO.

## Finding writeup

- **Title:** Clickjacking on `<sensitive-page>`
- **Severity:** UI-redress on an authenticated, state-changing action = Medium-High; on a static or unauthenticated page = Low.
- **Evidence** per `methodology-evidence-capture`: response headers (showing absence of protection), PoC HTML source, and a screenshot of the framed target rendered inside the attacker page.
- **Fix:** Add `X-Frame-Options: DENY` to all sensitive responses, or set `Content-Security-Policy: frame-ancestors 'self'` (use `'none'` to block all framing). Prefer the CSP directive for modern browsers.

## References

- OWASP WSTG CLNT-09: `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/09-Testing_for_Clickjacking`
- PortSwigger Clickjacking: `https://portswigger.net/web-security/clickjacking`
- CWE-1021: `https://cwe.mitre.org/data/definitions/1021.html`

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
