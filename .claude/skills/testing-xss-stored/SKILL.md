---
name: testing-xss-stored
description: Test for OWASP A03 Stored XSS in persistent inputs (comments, profile fields, filenames, review fields).
---

# Testing for Stored XSS (OWASP A03)

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-sitemap-crawl`, `mcp-burp`, `mcp-browser`.

Use this skill when user-supplied input is persisted server-side and later re-rendered to other users. Unlike reflected XSS, stored XSS does not require the victim to follow a crafted link — the payload executes whenever any user (or admin) loads the page that renders the stored content.

## Signal to look for

- Comment, review, or message fields whose content is displayed to other users.
- Profile fields (display name, biography, avatar URL) rendered in shared views such as leaderboards, activity feeds, or admin dashboards.
- Uploaded filenames displayed elsewhere in the UI (attachment lists, media galleries, audit logs).
- Admin-review panels that render raw user content for moderation — high-value targets because admin sessions carry elevated privilege.

## Test steps

1. Submit a canary payload to the persistent input via `burp_repeater_send` (POST to the comment, profile, or upload endpoint). Use a self-identifying payload such as `<svg/onload=alert(1)>` that is both visually distinct and evaluable.

2. Retrieve the rendering page via `browser_navigate` to the URL where the stored content is displayed. Navigate as a different user account when possible to confirm cross-user impact — this distinguishes stored XSS from a self-XSS finding.

3. Confirm execution via `browser_eval(expression="!!document.querySelector('svg[onload]')")`. A return value of `true` confirms the payload is present and unencoded in the DOM.

4. Capture a screenshot with `browser_screenshot(full_page=true)` and retrieve the submit and retrieval requests via `burp_proxy_request` as evidence per `methodology-evidence-capture`.

## Tool commands

**Shell:**

```bash
curl -X POST -H "Cookie: session=<SESSION>" \
  -d 'comment=<svg/onload=alert(1)>' \
  https://target.example.com/comment
# Success: 200 stored; redirect to comment-list page
```

**MCP:**

```
# Step 1 — submit the payload via Repeater
burp_repeater_send(raw_base64=<b64 submit>, host="target.example.com", port=443, secure=true, tab_name="xss-stored-submit")
# Success: {"ok": true, "data": {"tab_id": "..."}}

# Step 2 — navigate to the rendering page (as a different user if possible)
browser_navigate(url="https://target.example.com/post/123")
# Success: {"ok": true, "data": {"url": "https://target.example.com/post/123"}}

# Step 3 — confirm DOM execution
browser_eval(expression="!!document.querySelectorAll('svg[onload]').length > 0")
# Confirmed: {"ok": true, "data": {"value": true, "type": "boolean", "exception": null}}

# Step 4 — capture evidence
browser_screenshot(full_page=true)
# Success: {"ok": true, "data": {"format": "png", "base64": "iVBORw0K..."}}

burp_proxy_request(id=<N>)
# Success: {"ok": true, "data": {"request": "...", "response": "..."}}
```

## Interpret results

- Payload rendered and `browser_eval` returns `true` — confirmed stored XSS. Proceed to cross-user confirmation and writeup.
- `browser_eval` returns `false` — the payload was stored but not executed. Common causes:
  - **Backend sanitizer runs on render, not on submit** — the raw payload may be stored but sanitized at render time. Inspect the rendered HTML via `browser_query(selector="<area>")` to see what the sanitizer produced. An unauthenticated submission may also be sanitized differently than content submitted by an authenticated user; repeat the test with an authenticated session.
  - **CSP blocks execution** — check the `Content-Security-Policy` response header via `burp_proxy_history`. Record the policy verbatim; the stored payload is still a weakness even if execution is currently blocked.
- **Cross-user impact:** Confirm by navigating to the rendering page in a second browser session authenticated as a different user and repeating the `browser_eval` check. Self-XSS (payload executes only for the submitting user) is a lower-severity finding; cross-user execution is Critical.

## Finding writeup

- **Title:** `Stored XSS in <field>` — e.g. "Stored XSS in comment body" or "Stored XSS in profile display name".
- **Severity:** Persistent cross-user execution = **Critical**. The payload executes automatically for every user who loads the affected page, with no interaction required beyond visiting a normal application URL.
- **Evidence** (per `methodology-evidence-capture`):
  1. Submit request and response showing the payload accepted and stored.
  2. Retrieval request and response showing the rendering page loaded.
  3. Screenshot from `browser_screenshot` with the payload visible in the DOM.
  4. `browser_eval` result showing `"value": true`.
  5. Note whether cross-user impact was confirmed (second session test result).
- **Fix:**
  - Encode on render, not on submit — apply context-aware output encoding at every point where stored content is emitted into HTML.
  - Deploy a `Content-Security-Policy` header with a strict `script-src` directive as defense-in-depth.
  - Sanitize rich-text input with an allow-list HTML parser (e.g. DOMPurify) rather than a block-list approach.

## References

- OWASP WSTG INPV-02 (Stored XSS): `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/02-Testing_for_Stored_Cross_Site_Scripting`
- PortSwigger Stored XSS: `https://portswigger.net/web-security/cross-site-scripting/stored`
- CWE-79: `https://cwe.mitre.org/data/definitions/79.html`

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
