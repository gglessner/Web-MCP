---
name: testing-xss-dom
description: Test for OWASP A03 DOM-based XSS — sinks executing attacker-controlled input without server round-trip.
---

# DOM-based XSS testing

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-js-analysis`, `recon-sitemap-crawl`, `mcp-browser`.

Use this skill when the target is a SPA with client-side routing where attacker-controlled
sources such as `location.hash`, `location.search`, `postMessage`, or `document.referrer`
flow directly into dangerous sinks such as `innerHTML`, `eval`, or `document.write` — all
without a server round-trip. The injected payload executes in the victim's browser through
purely client-side data flow.

## Signal to look for

- JS bundle analysis (from `recon-js-analysis`) flagged a `location.hash` → `innerHTML`
  data flow.
- Framework-specific dangerous sinks in bundle source: `dangerouslySetInnerHTML` (React),
  `v-html` (Vue), or `[innerHTML]` property binding (Angular).
- Hash-routed SPA: the server returns the same HTML shell regardless of the fragment, so
  the fragment value is consumed entirely client-side.

## Test steps

1. Identify the source-sink pair from `recon-js-analysis` output (e.g. `location.hash`
   assigned into `element.innerHTML`).
2. Craft a payload in the identified source (URL hash, query param, or postMessage data).
3. Load the page with the payload via:
   `browser_navigate(url="https://target.example.com/#<svg/onload=alert(1)>")`
4. Confirm execution via:
   `browser_eval(expression="!!document.querySelector('svg[onload]')")`
   Expected result: `{"ok": true, "data": {"value": true, "type": "boolean", "exception": null}}`
5. Confirm NO server round-trip via:
   `browser_network_log(since_seq=0)`
   Review the returned event list — the raw payload string must not appear in any recorded
   request URL or body. If it does appear, the issue is reflected XSS, not DOM XSS.
6. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell:** None required — DOM XSS is a client-side concern. Optional static analysis to
pre-screen a bundle before browser testing:

```
curl -o main.js https://target.example.com/static/js/main.js
grep -oE '(innerHTML|document\.write|eval)\(' main.js
```

**MCP:**

```
# Navigate with URL-encoded payload in the hash fragment
browser_navigate(url="https://target.example.com/#%3Csvg%2Fonload%3Dalert(1)%3E")
# Success: {"ok": true, "data": {"url": "https://target.example.com/#<svg/onload=alert(1)>"}}

# Confirm the SVG element exists in the DOM (proves sink executed)
browser_eval(expression="!!document.querySelector('svg[onload]')")
# Success: {"ok": true, "data": {"value": true, "type": "boolean", "exception": null}}

# Confirm the payload never left the browser
browser_network_log(since_seq=0)
# Success: {"ok": true, "data": {"events": [...], "next_seq": <N>}}
# Review events — payload string must not appear in any request URL or body.
```

## Interpret results

**DOM XSS confirmed:** `browser_eval` returns `true` AND `browser_network_log` shows the
payload was never sent to the server. The vulnerability is purely client-side.

**False positive — reflected XSS:** The server DOES receive the payload (it appears in a
logged request URL or body). The issue is server-side reflection, not DOM-based. Switch to
`testing-xss-reflected` and note the reclassification.

**False negative — Trusted Types:** A Trusted Types policy can silently block assignment to
`innerHTML` even when the data flow is present. If `browser_eval` returns `false` and the
browser console reports a Trusted Types violation, document the policy as a partial
mitigation and probe for policy bypasses separately.

## Finding writeup

- **Title:** `DOM-based XSS in <source> → <sink>` (e.g. "DOM-based XSS in `location.hash`
  → `innerHTML`").
- **Severity:** Authenticated-origin JS execution = High. One-click or zero-interaction
  impact = Critical. Future `reporting-*` guidance will formalize the rubric.
- **Evidence** per `methodology-evidence-capture`:
  - URL containing the payload in the hash or query string.
  - `browser_eval` result showing `true`.
  - `browser_network_log` output confirming no server interaction with the payload.
  - Screenshot of execution (e.g. alert dialog or injected element visible in the DOM).
- **Fix guidance:**
  - Avoid dangerous sinks; prefer `textContent` over `innerHTML` for untrusted data.
  - Where HTML output is necessary, sanitize with `DOMPurify` (allow-list approach).
  - Enforce Trusted Types via a Content-Security-Policy `require-trusted-types-for 'script'`
    directive to harden the entire application against DOM injection.

## References

- OWASP WSTG CLNT-01 (DOM-based XSS): `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/01-Testing_for_DOM-Based_Cross_Site_Scripting`
- PortSwigger DOM XSS: `https://portswigger.net/web-security/cross-site-scripting/dom-based`
- CWE-79: `https://cwe.mitre.org/data/definitions/79.html`

## Authorization note

Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.
