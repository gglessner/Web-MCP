---
name: recon-tech-fingerprinting
description: Identify the technology stack (web server, framework, CMS, WAF/CDN) of a target via headers, cookies, error-page signatures, and rendered-DOM inspection.
---

# Technology Stack Fingerprinting

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-browser`, `mcp-burp`.

Use this skill before selecting attack classes; when a framework-specific test
skill must be chosen; and when a CDN or WAF may alter response bodies in ways
that would make subsequent active tests produce misleading results.

## Signal to look for

- Target is a black-box HTTP service with no prior stack knowledge.
- You are about to pick an attack technique without knowing the underlying
  framework, runtime, or server.
- Probe results look inconsistent across hosts — response bodies, headers, or
  status codes differ in ways that suggest CDN interference or load-balanced
  heterogeneous backends.

## Test steps

1. Grab headers and the status page:
   ```
   curl -sI https://target.example.com
   curl -s https://target.example.com/ | head -40
   ```
2. Run WhatWeb for a plugin-based fingerprint:
   ```
   whatweb -a3 https://target.example.com
   ```
   (Wappalyzer's standalone CLI was deprecated — use the browser extension or the Wappalyzer API if you need Wappalyzer fingerprints.)
3. Drive the browser for a rendered-DOM fingerprint:
   ```
   browser_launch(headless=true, proxy="127.0.0.1:8080")
   browser_navigate(url="https://target.example.com")
   browser_snapshot()
   ```
4. Review captured headers — look for `X-Powered-By`, `Server`, and
   framework-specific cookie names:
   ```
   burp_proxy_history(host="target.example.com", limit=50)
   ```
5. Probe an invalid route to elicit a framework-specific error page:
   ```
   curl -sI https://target.example.com/xyz-404
   ```
   Common tells: Django debug page, Rails error banner, Laravel Whoops page.

## Tool commands

Shell:

```bash
# Plugin-based fingerprint
whatweb -a3 https://target.example.com
# Success: grouped plugin-based fingerprint lines, one plugin group per result entry

# Header grab
curl -sI https://target.example.com
# Success: header block including Server, X-Powered-By, Set-Cookie lines
```

MCP:

```
# Launch Chrome routed through Burp, then capture rendered DOM
browser_launch(headless=true, proxy="127.0.0.1:8080")
# Success: {"ok": true, "data": {"chrome_binary": "...", "cdp_url": "..."}}

browser_navigate(url="https://target.example.com")
# Success: {"ok": true, "data": {"url": "https://target.example.com"}}

browser_snapshot()
# Success: {"ok": true, "data": {"dom": {...}, "accessibility": {...}}}

# Review all captured response headers for the target host
burp_proxy_history(host="target.example.com", limit=50)
# Success: {"ok": true, "data": {"items": [...], "total": 12, "cursor": 12}}
```

## Interpret results

**Strong signals** — high-confidence indicators of a specific technology:

- `X-Powered-By: PHP/7.4.3` — PHP runtime, version exposed.
- `JSESSIONID` cookie — Java servlet container (Tomcat, JBoss, WebSphere).
- `connect.sid` cookie — Node.js with `express-session`.
- `csrftoken` cookie — Django (Python).
- CSP `script-src` domains referencing a known CDN vendor (e.g.,
  `cdn.cloudflare.com`, `*.akamaihd.net`) identify the CDN layer.

**Weak signals** — require corroboration before acting on them:

- Generic `Server: nginx` — the upstream application could be anything; nginx
  commonly fronts Node, PHP, Python, and Go services alike.

**WAF presence:**

- Cloudflare: `cf-ray` response header.
- Akamai: `akamai-*` headers or `AkamaiGHost` in the `Server` value.
- AWS WAF: response-body watermark or `x-amzn-requestid` header in blocked
  responses.

WAF presence informs payload delivery strategy and may cause false negatives
in later active-testing phases; note it explicitly in the engagement log.

## Finding writeup

Tech fingerprinting results are typically informational and feed the attack-
surface inventory rather than producing a standalone finding. Exception: a
detailed, unredacted stack banner — for example, `X-Powered-By: PHP/5.2.17`
— is an **"Information Disclosure"** finding, severity Low, because it
reveals an end-of-life version and assists attacker targeting.

Evidence per `methodology-evidence-capture`: the raw response header block
from `curl -sI` or `burp_proxy_history`, showing the disclosing header name
and value verbatim.

## References

- OWASP WSTG-INFO-02 — Fingerprint Web Server:
  https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/02-Fingerprint_Web_Server
- OWASP WSTG-INFO-08 — Fingerprint Web Application Framework:
  https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/08-Fingerprint_Web_Application_Framework
- OWASP WSTG-INFO-09 — Fingerprint Web Application:
  https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/09-Fingerprint_Web_Application
- WhatWeb repository: https://github.com/urbanadventurer/WhatWeb
- Wappalyzer: https://www.wappalyzer.com/

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
