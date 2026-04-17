---
name: recon-js-analysis
description: Extract endpoints, API routes, client-side secrets, and DOM sinks from a target's JavaScript bundles via static download and runtime browser inspection.
---

# JavaScript Bundle Analysis

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-browser`. Optional: `mcp-burp`.

Use this skill when the target is a single-page application or a heavily
JS-driven site. Content discovery and sitemap crawls leave gaps when most
routing and API wiring lives inside client-side bundles rather than server
responses. Analyzing those bundles fills the gaps: undocumented endpoints,
internal API prefixes, hardcoded credentials, and DOM sinks that feed later
testing phases.

## Signal to look for

- `curl <target>` returns a JS shell with almost no meaningful HTML content —
  just `<div id="root"></div>` and a handful of `<script>` tags.
- The Network tab shows one or more large minified bundles (often 200 KB–5 MB)
  loading under `/static/js/` or similar paths.
- Framework fingerprint points to React, Vue, Angular, or Svelte (chunk names,
  global variables, or meta tags confirm the framework).

## Test steps

1. Inventory bundles via `browser_navigate` and `browser_network_log`.

   ```
   browser_navigate(url="https://target.example.com")
   browser_network_log(since_seq=0)
   ```

   Filter the returned events for `.js` URLs to get the full list of bundle
   files served on initial load.

2. Download each bundle with curl.

   ```bash
   curl -o main.js https://target.example.com/static/js/main.js
   ```

   Repeat for each chunk identified in step 1 (e.g., `vendor.js`,
   `runtime.js`).

3. Extract endpoints from the downloaded bundle.

   ```bash
   linkfinder -i main.js -o cli
   ```

   Alternative (jsluice):

   ```bash
   jsluice urls main.js
   ```

   Fallback grep when neither tool is installed:

   ```bash
   grep -oE '(api|/v[0-9]+)/[A-Za-z0-9_\-/]+' main.js | sort -u
   ```

4. Runtime inspection — probe exposed globals and framework state.

   ```
   browser_eval(expression="Object.keys(window).length")
   ```

   Framework detection probe (React):

   ```
   browser_eval(expression="document.querySelectorAll('[data-reactroot]').length")
   ```

   Run additional probes as needed for Vue (`window.__vue_app__`) or Angular
   (`window.ng`) to map what the framework exposes globally.

5. Correlate bundle URLs and discovered API routes with captured Burp traffic.

   ```
   burp_proxy_history(host="target.example.com", contains=".js")
   burp_proxy_history(host="target.example.com", contains="/api")
   ```

## Tool commands

**Shell:**

```bash
curl -o main.js https://target.example.com/static/js/main.js
linkfinder -i main.js -o cli
jsluice urls main.js
grep -oE '(api|/v[0-9]+)/[A-Za-z0-9_\-/]+' main.js | sort -u
```

**MCP:**

```
# Capture all network events from page load — find bundle URLs
browser_network_log(since_seq=0)
# Success: {"ok": true, "data": {"events": [...], "next_seq": 42}}

# Count exposed window globals as a runtime sanity check
browser_eval(expression="Object.keys(window).length")
# Success: {"ok": true, "data": {"value": 87, "type": "number", "exception": null}}

# Find JS bundles that Burp recorded
burp_proxy_history(host="target.example.com", contains=".js")
# Success: {"ok": true, "data": {"items": [...], "total": 6, "cursor": 6}}

# Find API calls Burp recorded
burp_proxy_history(host="target.example.com", contains="/api")
# Success: {"ok": true, "data": {"items": [...], "total": 14, "cursor": 14}}
```

## Interpret results

**Development-only endpoints** — bundles often include routes that are
feature-flagged off at runtime (e.g., `/debug`, `/admin-preview`). Confirm
reachability with `browser_navigate` or a direct `curl` probe before including
them in a finding.

**Placeholder secrets** — strings like `YOUR_API_KEY_HERE`, `xxxx-xxxx`, or
`sk_test_*` are false positives inserted by developers as placeholders or for
testing. Do not report these as credential exposures.

**Real secrets** — patterns worth reporting: `sk_live_*` (Stripe live keys),
high-entropy base64 strings embedded in non-test contexts, private key PEM
headers, and OAuth client secrets. Cross-reference against the target's
known third-party integrations to confirm relevance.

**DOM sinks** — occurrences of `innerHTML`, `document.write`, `eval`, and
`setTimeout(string, ...)` in bundle source are indicators for client-side
injection. Flag their locations (file, approximate line) and pass them forward
to `testing-*` skills for XSS-focused follow-up.

## Finding writeup

- **Hardcoded production secret in JS bundle** → title: "Credential Exposure
  in JavaScript Bundle", severity: High to Critical depending on what the
  key grants access to. Evidence: bundle URL, line number or grep hit showing
  the key, and the `browser_navigate` + `browser_network_log` sequence that
  confirmed the bundle is publicly served.

- **Undocumented internal API endpoint** → informational finding that feeds
  `testing-*` skills. Note the full path, HTTP method if determinable from
  the bundle, and any parameters visible in the source.

Evidence per `methodology-evidence-capture`: record the bundle URL, the exact
line or grep output showing the hit, and the `browser_navigate` +
`browser_network_log` command sequence used to locate the bundle.

## References

- OWASP WSTG Client-side Testing:
  https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/
- LinkFinder repository: https://github.com/GerbenJavado/LinkFinder
- jsluice repository: https://github.com/BishopFox/jsluice

## Authorization note

Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.
