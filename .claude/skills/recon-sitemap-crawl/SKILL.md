---
name: recon-sitemap-crawl
description: Consolidate the recon phase's collected traffic into an attack-surface map via browser-mcp authenticated crawling and burp-mcp sitemap inspection.
---

# Sitemap Crawl and Attack-Surface Consolidation

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-browser`, `mcp-burp`.

Multiple sources of partial traffic exist — browser sessions, ffuf hits, API probes — and
you need a single inventory before transitioning to active testing. Use this skill to merge
what Burp already knows with a fresh authenticated browser crawl and surface XHR-only
endpoints that passive traffic capture missed.

## Signal to look for

- Recon is "done enough" but no single, authoritative path inventory exists.
- The attack-surface mental model is fragmented across Burp history, ffuf output, and
  manual notes.
- You are about to exit Phase 2 per `methodology-phases` and need the sitemap dense
  enough to drive `testing-*` skill selection.

## Test steps

1. **Baseline — save what Burp already captured.**

   ```
   burp_sitemap(prefix="https://target.example.com", limit=500)
   # Success: {"ok": true, "data": {"items": [...], "total": 182}}
   ```

   Write the returned paths to `burp_sitemap.txt` for later diffing.

2. **Launch an authenticated browser routed through Burp.**

   ```
   browser_launch(headless=true, proxy="127.0.0.1:8080")
   browser_navigate(url="https://target.example.com/login")
   browser_fill(selector="input[name=user]", text="tester")
   browser_fill(selector="input[name=pass]", text="<TEST-PASSWORD>")
   browser_click(selector="button[type=submit]")
   ```

   Confirm the post-login URL shows an authenticated home page before proceeding.

3. **Walk the visible menu structure to linked-but-uncrawled pages.**

   For each top-level nav item, use `browser_click` or `browser_navigate` to follow
   the link and let Burp record the traffic. Repeat for any sub-menus or modal flows
   the landing page exposes.

   ```
   browser_navigate(url="https://target.example.com/dashboard")
   browser_click(selector="a[href='/settings']")
   browser_navigate(url="https://target.example.com/reports")
   ```

4. **Surface XHR-only endpoints via the network log.**

   ```
   browser_network_log(since_seq=0)
   # Success: {"ok": true, "data": {"events": [...], "next_seq": 74}}
   ```

   Inspect `events` for fetch/XHR requests not already present in the Burp sitemap.
   Note every unique path for the final inventory.

5. **Re-check Burp — new paths should now appear.**

   ```
   burp_sitemap(prefix="https://target.example.com", limit=500)
   # Success: {"ok": true, "data": {"items": [...], "total": 247}}
   ```

   Write the updated list to `burp_sitemap_post_crawl.txt`.

6. **Optional shell diff against content-discovery results.**

   Compare the sitemap against ffuf hits from `recon-content-discovery` to find paths
   known to ffuf but absent from Burp (direct-access-only routes) or vice versa.

   ```bash
   diff <(sort burp_sitemap_post_crawl.txt) <(sort ffuf_hits.txt)
   ```

   Paths in ffuf but not in Burp may be accessible without a session cookie and warrant
   unauthenticated testing first.

## Tool commands

MCP-native primary commands:

```
burp_sitemap(prefix="https://target.example.com", limit=500)
# Success: {"ok": true, "data": {"items": [...], "total": 182}}

browser_launch(headless=true, proxy="127.0.0.1:8080")
browser_navigate(url="https://target.example.com/login")
browser_fill(selector="input[name=user]", text="tester")
browser_fill(selector="input[name=pass]", text="<TEST-PASSWORD>")
browser_click(selector="button[type=submit]")
browser_network_log(since_seq=0)
```

Optional shell diff:

```bash
# Diff Burp sitemap output against ffuf content-discovery results.
diff <(sort burp_sitemap.txt) <(sort ffuf_hits.txt)
```

## Interpret results

**Crawl gaps are expected.** Routes requiring form submission, file upload, or multi-step
state transitions will not appear unless you explicitly walk them. After the crawl, ask
what you have not touched: wizard-style flows, out-of-band delivery paths (email links,
webhook callbacks), and admin-tier pages that are not linked from the standard nav.

**"Complete enough" is the Phase 2 exit criterion per `methodology-phases`.** The sitemap
is complete enough when it densely covers every in-scope host, includes authenticated and
unauthenticated paths, and captures XHR endpoints visible via `browser_network_log`. The
goal is not an exhaustive spider — it is a map accurate enough to drive `testing-*` skill
selection without blind spots in the attack surface.

## Finding writeup

This skill typically produces an inventory that feeds `testing-*` skills rather than a
standalone finding. However, if the crawl surfaces an unintended area — an admin UI
reachable without authentication, a pre-production environment mistakenly linked from
production — write it up per `methodology-evidence-capture` with the exact
`browser_navigate` and `burp_sitemap` call sequence that demonstrated the exposure:

- **Title pattern:** `Unintended <area> exposed via unauthenticated path` — e.g.
  "Admin panel reachable without authentication via `/admin/`".
- **Severity guidance:** Unauthenticated access to administrative functionality is
  typically High or Critical; raise to Critical if the exposed area reveals customer
  data, credentials, or privileged actions. Leaked internal pages with no sensitive
  data are Low-Medium.
- **Reproduction steps:** the `browser_navigate` call that reached the area, the
  `burp_sitemap` excerpt confirming Burp captured it, and a `browser_screenshot` as
  evidence.

## References

- OWASP WSTG-INFO-07 Map Execution Paths:
  https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/07-Map_Execution_Paths_Through_Application
- Burp Suite sitemap documentation:
  https://portswigger.net/burp/documentation/desktop/tools/target/site-map

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
