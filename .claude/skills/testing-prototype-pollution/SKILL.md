---
name: testing-prototype-pollution
description: Test for Prototype Pollution in Node.js and client-side JS — source/sink analysis, gadget identification, payload delivery.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-js-analysis`, `recon-sitemap-crawl`, `mcp-browser`.

Use this skill when testing a JS-heavy application that relies on object-merge libraries such as lodash, jquery-extend, or `Object.assign` with user-controlled input. Prototype pollution becomes a realistic attack surface when untrusted data flows into merge or deep-clone operations that do not sanitize property keys.

## Signal to look for

- JSON request bodies containing deeply-nested objects that are merged into application state on the server or client.
- URL parameters parsed with `qs` or similar libraries that support bracket notation (e.g. `?a[__proto__][polluted]=yes`).
- Source/sink analysis from `recon-js-analysis` that flagged potential gadgets — reads of `Object.prototype` properties in HTML-templating engines, CSP configuration objects, or function-flag checks.

## Test steps

1. **Pollution probe:** Send `{"__proto__": {"polluted": "yes"}}` (or the `constructor.prototype` equivalent) to any endpoint that accepts and merges a JSON object into application state.
2. **Runtime check:** Call `browser_eval(expression="({}).polluted")` — if the return value is `"yes"`, prototype pollution succeeded and the property has been inherited by all plain objects.
3. **Gadget search:** Review JS sinks identified during `recon-js-analysis` for reads of `Object.prototype.X` that feed into dangerous operations: CSP header construction, boolean feature flags, HTML-templating sinks (`innerHTML`, `document.write`), or `eval`-like calls.
4. **End-to-end exploit:** Attempt to pollute a property that triggers an XSS gadget (e.g. `Object.prototype.innerHTML`) and observe whether the templating engine renders the injected value into the DOM.
5. **Capture evidence** per `methodology-evidence-capture`: save the polluting request, the `browser_eval` confirmation output, and a screen recording or screenshot of any gadget-triggered effect.

## Tool commands

**Shell — static grep on downloaded bundles for prototype usage:**

```
grep -nE 'Object\.prototype\.|__proto__\[' main.js
```

**MCP — send the `__proto__` probe via Burp Repeater:**

```
burp_repeater_send(raw_base64=<b64 with __proto__ payload>, host="target.example.com", port=443, secure=true, tab_name="proto-probe")
```

Response envelope example: `{"ok": true, "status": 200, "body": "..."}`.

**MCP — confirm runtime pollution in the browser:**

```
browser_eval(expression="({}).polluted")
```

Expected return when pollution succeeded: `"yes"`.

**Burp Pro — DOM Invader:** Enable DOM Invader's prototype-pollution mode from the Burp browser extension panel for automated canary injection and confirmation across all page navigations.

## Interpret results

A non-`undefined` return from `browser_eval(expression="({}).polluted")` — matching the value injected in the probe — confirms that the runtime object prototype has been modified and that all subsequently created plain objects will inherit the polluted property.

Exploitation impact depends entirely on gadget availability:

- **Pollution confirmed, no gadget found:** Medium severity — the vulnerability exists and could be escalated if a gadget is introduced later, or if an existing gadget was missed.
- **Pollution with a gadget chain to XSS:** High severity — user-controlled script execution is achievable.
- **Pollution with a gadget to DoS or logic bypass** (e.g. forcing `isAdmin: true` on every object): High or Medium depending on the business impact of the bypassed control.

## Finding writeup

- **Title:** `Prototype Pollution via <parameter>` (e.g. `Prototype Pollution via __proto__ JSON key in /api/merge`).
- **Severity:** XSS via gadget chain = High; DoS or logic-control bypass = Medium; pollution confirmed without reachable gadget = Medium.
- **Evidence** per `methodology-evidence-capture`:
  - The polluting HTTP request with the `__proto__` (or `constructor.prototype`) payload.
  - The `browser_eval` return value confirming runtime inheritance.
  - Screenshot or recording of the gadget exploit if demonstrated (XSS alert, DOM modification, etc.).
- **Fix:**
  - `Object.freeze(Object.prototype)` at application startup to prevent mutation.
  - Use `Object.create(null)` for dictionaries that must accept arbitrary keys.
  - Validate and reject object keys matching `__proto__`, `constructor`, and `prototype` before any merge operation.
  - Upgrade lodash to 4.17.21+ or replace `_.merge` with a sanitizing equivalent.

## References

- OWASP WSTG CLNT-13 (Testing for Client-side Prototype Pollution): `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/13-Testing_for_Client-side_Prototype_Pollution`
- PortSwigger Prototype pollution: `https://portswigger.net/web-security/prototype-pollution`
- CWE-1321: `https://cwe.mitre.org/data/definitions/1321.html`

## Authorization note

Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.
