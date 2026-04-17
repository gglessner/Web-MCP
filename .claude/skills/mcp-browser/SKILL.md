---
name: mcp-browser
description: Drive a real Chrome browser via the browser-mcp MCP server for reconnaissance, manual interaction, DOM inspection, and JS execution during web application penetration testing.
---

# Using browser-mcp for web pentest interactions

## When to use

When a test step requires a real browser: multi-step authentication flows,
DOM-level inspection after client-side rendering, confirming JavaScript-level
behavior (DOM XSS, postMessage, SameSite cookie effects), or capturing
screenshots as evidence. `curl` is fine for simple request/response checks;
come here when the page relies on JS or when you need to observe the rendered
state.

Prerequisite: the `browser-mcp` server is registered in Claude Code (see
`README.md` in the Web-MCP repo root).

## Signal to look for

- Target is a single-page app: `curl <target>` returns a stub HTML shell with
  JS bundle references and almost no content.
- Authentication is a multi-step flow (SSO redirect, CAPTCHA, WebAuthn).
- The suspected bug requires client-side JS to execute: DOM XSS, postMessage,
  location-based redirects, local/session storage handling.
- Evidence must include a screenshot of the rendered page.

## Test steps

1. `browser_launch(headless=true, proxy="127.0.0.1:8080")` — routes traffic
   through Burp for recording. Omit the `proxy` argument to test without
   interception.
2. `browser_navigate(url="<target-url>")` — waits for the `Page.loadEventFired`
   event (default 30 s timeout).
3. `browser_snapshot()` — returns the full DOM plus the accessibility tree.
   Use for high-level structure.
4. Interact with the page as needed:
   - `browser_query(selector="<css-selector>")` — returns `outerHTML` of the
     first match.
   - `browser_click(selector="<css-selector>")` — dispatches a real mouse
     event at the element's centroid.
   - `browser_fill(selector="<css-selector>", text="<value>")` — focuses and
     types into an input.
5. `browser_eval(expression="<javascript>")` — returns the value or the
   exception text. Use for concrete proof of client-side behavior.
6. `browser_network_log(since_seq=<N>)` — returns CDP `Network.*` events
   accumulated since sequence `N` (use `0` on first call).
7. `browser_cookies(urls=["<origin>"])` / `browser_set_cookie(...)` — inspect
   or modify cookies for the active session.
8. `browser_screenshot(full_page=true)` — capture evidence as base64 PNG.
9. `browser_close()` — terminate the Chrome subprocess. Idempotent.

## Tool commands

Concrete examples — replace angle-bracketed placeholders with real values.

```
# 1. Start Chrome routed through Burp for recording
browser_launch(headless=true, proxy="127.0.0.1:8080")
# Success: {"ok": true, "data": {"chrome_binary": "...", "cdp_url": "..."}}

# 2. Navigate to the target
browser_navigate(url="https://target.example.com/login")
# Success: {"ok": true, "data": {"url": "..."}}
# Failure: {"ok": false, "error": {"code": "TIMEOUT", ...}} — proxy or target unreachable

# 3. Inspect the rendered DOM
browser_snapshot()
# Success: {"ok": true, "data": {"dom": {...}, "accessibility": {...}}}

# 4. Grab a specific element
browser_query(selector="form#login")
# Success: {"ok": true, "data": {"html": "<form id=\"login\">...</form>", "nodeId": 42}}

# 5. Fill + submit a form
browser_fill(selector="input[name=user]", text="tester")
browser_fill(selector="input[name=pass]", text="hunter2")
browser_click(selector="button[type=submit]")
browser_navigate(url="https://target.example.com/home")  # wait for navigation

# 6. Confirm JS-level behavior (DOM XSS probe)
browser_eval(expression="!!document.querySelector('svg[onload]')")
# Success: {"ok": true, "data": {"value": true, "type": "boolean", "exception": null}}

# 7. Review requests that happened during the flow
browser_network_log(since_seq=0)
# Success: {"ok": true, "data": {"events": [...], "next_seq": 27}}

# 8. Capture evidence
browser_screenshot(full_page=true)
# Success: {"ok": true, "data": {"format": "png", "base64": "iVBORw0K..."}}

# 9. Clean up
browser_close()
# Success: {"ok": true, "data": {"closed": true}}
```

## Interpret results

Every browser-mcp tool returns either `{"ok": true, "data": {...}}` or
`{"ok": false, "error": {"code": "...", "message": "...", "detail": {...}}}`.

Error codes you will actually see:

- `TARGET_NOT_ATTACHED` — `browser_launch` was never called, or Chrome died.
  Call `browser_launch` and retry.
- `TIMEOUT` (on navigate) — target or proxy unreachable, or the page never
  fired `Page.loadEventFired` within the timeout. Confirm target is reachable
  (`curl <target>`), confirm Burp is listening on the configured proxy port.
- `BAD_INPUT` (on query/click/fill) — the selector matched nothing. Re-run
  `browser_snapshot()` to find the right selector.
- `INTERNAL` — unexpected failure. Inspect `logs/browser-mcp.log` for the
  stack trace.

False positives to watch for:

- JS that runs but is blocked by a strict CSP: the payload reflected, the DOM
  looks vulnerable, but execution is prevented. Check the response's
  `Content-Security-Policy` header via `burp_proxy_history` and call it out in
  the finding.
- Elements present in the DOM but hidden via CSS. `browser_click` still
  succeeds — but a real user could not reach them. Note the hidden-state in
  the writeup.

## Finding writeup

- **Title pattern:** `<Issue> in <component> (client-side)` — e.g. "DOM-based
  XSS in `#search` query parameter (client-side)".
- **Severity guidance:** If the confirmed impact is arbitrary JS execution in
  the authenticated origin, use High or Critical per `reporting-severity-rubric`.
  If the trigger requires unusual user interaction (hover plus click in a
  specific order), drop one severity level and note the interaction cost.
- **Description template:** *"The `<parameter>` value is rendered into the DOM
  at `<location>` without encoding, allowing an attacker who controls
  `<parameter>` to execute JavaScript in the context of `<origin>`. Impact:
  session hijacking, UI redress, and access to any data visible to the
  authenticated user."*
- **Reproduction steps:** the numbered `browser_*` calls that produced the
  evidence, verbatim. Reviewers must be able to paste them into another
  Claude session and reproduce.
- **Suggested fix:** context-aware output encoding at the rendering site, plus
  a Content-Security-Policy as defense in depth. Link to CWE-79 and the OWASP
  XSS Prevention Cheat Sheet.

## References

- browser-mcp README: `MCPs/browser-mcp/README.md`
- Chrome DevTools Protocol: https://chromedevtools.github.io/devtools-protocol/
- OWASP Web Security Testing Guide — Client-side Testing:
  https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/

## Authorization note

Only use against systems you are authorized to test. This skill assumes the
user has obtained written authorization. If authorization is uncertain, stop
and confirm scope before proceeding.
