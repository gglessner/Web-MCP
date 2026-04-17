# Methodology & Recon Skills — Design

**Date:** 2026-04-17
**Author:** Garland Glessner (gglessner@gmail.com)
**Status:** Approved for planning
**Sub-project:** 3 of 5 in the Web-MCP skill-library track

## Purpose

Produce ten skills — four `methodology-*` (process guidance) and six `recon-*` (information-gathering techniques) — that teach Claude how to frame and start a web application penetration test. Together with sub-project 2's MCP usage skills, these form the front half of an engagement runbook: scope the work, agree rules, walk through phases, capture evidence, and gather the information needed before active testing.

## Non-goals

- No attack-technique runbooks (XSS, SQLi, IDOR, SSRF, etc.) — those belong in sub-project 4 as `testing-*` skills.
- No reporting or deliverable skills — sub-project 5.
- No per-tool dedicated recon skills (`recon-ffuf`, `recon-amass`, etc.) — one skill per technique, not per tool.
- No skill loader, validator, or link-checker script.
- No packaging changes — skills drop into `.claude/skills/` alongside existing files.

## Deliverables

Ten files under `.claude/skills/`:

```
.claude/skills/
├── methodology-scoping/SKILL.md
├── methodology-rules-of-engagement/SKILL.md
├── methodology-phases/SKILL.md
├── methodology-evidence-capture/SKILL.md
├── recon-subdomain-enum/SKILL.md
├── recon-tech-fingerprinting/SKILL.md
├── recon-content-discovery/SKILL.md
├── recon-js-analysis/SKILL.md
├── recon-api-enum/SKILL.md
└── recon-sitemap-crawl/SKILL.md
```

All ten live at the top of `.claude/skills/` (same flat level as existing `mcp-*` and `_template`). No `scripts/`, `references/`, or `examples/` subdirectories at initial write — each skill's content fits within the ~400-line cap. Subdirectories can be added later if a specific skill grows.

**Target body lengths:** methodology skills ~150 lines each; recon skills ~200-250 lines each. Each follows the 8-section template locked in by sub-project 1 (`docs/skill-conventions.md`).

## Per-skill content

### methodology-scoping

- **name:** `methodology-scoping`
- **description:** "Define the scope of a web application penetration test — in-scope assets, excluded targets, third-party restrictions, credential handling — before any active testing begins."
- **When to use:** start of an engagement, target-list ambiguity, a new subdomain or asset surfaces mid-test and its scope status is unclear.
- **Signal to look for:** test begins without a written target list; user says "test this site" without clarifying what "this site" includes; a recon finding sits on a borderline asset.
- **Test steps:** a checklist (in-scope URL/IP list → exclusion list → third-party and hosted-service restrictions → credential-handling rules → data-retention / data-egress limits → signed-off scope record).
- **Tool commands:** consultative — very few shell commands here; mainly templates and questions to ask the test sponsor. May include a `curl -I` DNS/ownership spot-check when confirming an asset belongs to the target organisation.
- **Interpret results:** how to tell whether an asset is in scope, what to do with "maybe" assets (escalate before testing).
- **Finding writeup:** N/A as scoping does not itself produce findings — one-line note explaining omission, per conventions.
- **References:** PTES Pre-engagement; OWASP WSTG Introduction; NIST SP 800-115 §3.
- **Authorization note:** treated substantively in the body (scoping *is* authorization); standard paragraph is therefore embedded and expanded, not appended verbatim.

### methodology-rules-of-engagement

- **name:** `methodology-rules-of-engagement`
- **description:** "Operational limits for an authorised web pentest — testing windows, rate limits, destructive-action ban, escalation path, safe-shutdown — consulted before any invasive probe."
- **When to use:** before active testing begins, after a probe causes a service anomaly, when a finding's PoC would require a destructive demonstration, when the testing window is about to close.
- **Signal to look for:** Claude is about to fire off an automated scan, a data-exfiltration PoC, or a user-account takeover demonstration; user asks "is it okay to do X?".
- **Test steps:** checklist for testing windows, rate limits per host, banned actions (no DoS, no destructive data actions beyond minimal PoC, no lateral movement past the in-scope boundary), outage-escalation path, safe-shutdown procedure.
- **Tool commands:** consultative; reference to `methodology-evidence-capture` for preserving evidence before and after invasive probes.
- **Interpret results:** green-light conditions vs. "pause and escalate" conditions.
- **Finding writeup:** N/A — one-line omission note.
- **References:** PTES Rules of Engagement; OWASP WSTG Test Execution.
- **Authorization note:** treated substantively in the body; not appended verbatim.

### methodology-phases

- **name:** `methodology-phases`
- **description:** "Sequence a web pentest engagement across scope, recon, discovery, exploit, and report phases — guides when Claude should reach for methodology, recon, testing, or reporting skills."
- **When to use:** at engagement start (to plan), mid-engagement (to decide whether enough recon has been done before exploitation), at finding-confirmation (to decide whether to move to write-up).
- **Signal to look for:** user asks "what should I do next?" without a specific step; Claude has produced a recon artifact and must decide whether to move to active testing.
- **Test steps:** a phase-by-phase decision tree. Phase 1 Scope & RoE (→ `methodology-scoping`, `methodology-rules-of-engagement`). Phase 2 Recon (→ `recon-*` skills, named individually). Phase 3 Discovery (→ `testing-*` category). Phase 4 Exploit (→ `testing-*`, with `methodology-evidence-capture` for every proven issue). Phase 5 Report (→ `reporting-*` category).
- **Tool commands:** minimal — mostly references to other skills. May include a one-liner `burp_proxy_history` / `burp_sitemap` call as the "recon-complete" checkpoint signal.
- **Interpret results:** phase-exit criteria (what must be true before you leave recon and start testing).
- **Finding writeup:** N/A — one-line omission note.
- **References:** PTES Execution Standard; OWASP WSTG Framework.
- **Authorization note:** omit with a one-line comment (no actions against a target).

### methodology-evidence-capture

- **name:** `methodology-evidence-capture`
- **description:** "Reproducible evidence conventions for web pentest findings — screenshot formats, raw request/response preservation, numbered MCP tool-call reproduction steps, source-code references."
- **When to use:** every time a finding is confirmed and must be documented, before closing out a proxy session, when a run-once runtime observation must be preserved.
- **Signal to look for:** a probe produced a positive result that now needs a finding; Claude is about to move on from a reproducible runtime observation; a finding's reproduction depends on session state that is about to be lost.
- **Test steps:** evidence checklist — raw HTTP request/response saved (`burp_proxy_request`), screenshot captured (`browser_screenshot(full_page=true)`), numbered MCP tool-call list written in the order used, source-code references by repo + SHA + line range when applicable, timestamp recorded.
- **Tool commands:** concrete examples of `burp_proxy_request`, `browser_screenshot`, `burp_repeater_send` as evidence-capture calls. Shows the shape reporting-* skills consume.
- **Interpret results:** what counts as reproducible (third party could re-run it) vs. non-reproducible (state lost, must be re-captured before write-up).
- **Finding writeup:** N/A for this skill itself — one-line omission note; this skill *defines* the finding writeup shape the rest of the library uses.
- **References:** OWASP WSTG Reporting; NIST SP 800-115 §6.
- **Authorization note:** omit with a one-line comment (no actions against a target).

### recon-subdomain-enum

- **name:** `recon-subdomain-enum`
- **description:** "Enumerate subdomains of a target organisation using passive sources (CT logs, passive DNS) and active probes, then load results into Burp scope for downstream testing."
- **When to use:** early-phase recon to expand attack surface beyond an initial URL.
- **Prerequisite skills:** `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-burp`.
- **Signal to look for:** engagement lists a root domain without specific hosts; a new asset is discovered and its parent domain may have siblings.
- **Tool commands:** hybrid. Shell: `subfinder -d target.com -silent`; `amass enum -passive -d target.com`; `curl -s 'https://crt.sh/?q=%25.target.com&output=json' | jq -r '.[].name_value'`. MCP follow-up: `burp_scope_modify(add=["https://newsub.target.com"])` to update scope before live testing.
- **Interpret results:** distinguishing owned subdomains from third-party hosting (`_acme-challenge` CNAME, shared hosts), false positives from wildcard DNS, stale CT entries.
- **Finding writeup:** typically not an individual finding — feeds into attack-surface inventory. If an unintended asset is exposed (dev/staging publicly reachable), writes up as "Exposed non-production asset". References `methodology-evidence-capture`.
- **References:** OWASP WSTG Information Gathering (WSTG-INFO-04); crt.sh; ProjectDiscovery subfinder docs.
- **Authorization note:** standard paragraph verbatim.

### recon-tech-fingerprinting

- **name:** `recon-tech-fingerprinting`
- **description:** "Identify the technology stack (web server, framework, CMS, WAF/CDN) behind a target using header analysis, cookie tells, error-page signatures, and rendered-DOM inspection."
- **When to use:** before selecting attack classes; when a specific framework dictates the right testing skills to pull in next.
- **Prerequisite skills:** `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-browser`, `mcp-burp`.
- **Signal to look for:** target is a black-box HTTP service; user is about to pick an attack technique without knowing the stack; a CDN/WAF may alter response bodies.
- **Tool commands:** hybrid. Shell: `whatweb -a3 https://target.example.com`; `wappalyzer https://target.example.com` (CLI); raw `curl -sI https://target.example.com` for server/framework headers. MCP: `browser_navigate` + `browser_snapshot` for rendered fingerprint (JS-loaded frameworks); `burp_proxy_history(host="target.example.com")` to review all captured response headers for version tells.
- **Interpret results:** distinguishing strong signals (specific `X-Powered-By` versions, framework cookies like `JSESSIONID`/`PHPSESSID`/`connect.sid`, CSP domains) from weak signals (generic `Server: nginx`); identifying WAF presence (Cloudflare, Akamai, AWS WAF) and what that implies for payload delivery.
- **Finding writeup:** typically informational; an exposed detailed stack (unredacted `X-Powered-By: PHP/5.2.17`) can be an "Information Disclosure" finding referencing `methodology-evidence-capture`.
- **References:** OWASP WSTG WSTG-INFO-02/08/09; Wappalyzer docs; WhatWeb docs.
- **Authorization note:** standard paragraph verbatim.

### recon-content-discovery

- **name:** `recon-content-discovery`
- **description:** "Discover hidden endpoints, backup files, and configuration artifacts on a web target using wordlist-based enumeration (ffuf/dirsearch/gobuster) plus common low-hanging paths."
- **When to use:** after scope is settled and the public surface is known — find what isn't linked.
- **Prerequisite skills:** `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-burp`, `mcp-browser`.
- **Signal to look for:** target has large unknown attack surface, framework hints suggest unprotected dev/admin endpoints, target exposes source control or backup files.
- **Tool commands:** hybrid. Shell canonical: `ffuf -u https://target.example.com/FUZZ -w /usr/share/wordlists/dirb/common.txt -mc 200,301,403`; `dirsearch -u https://target.example.com -e php,bak,old,zip`; `curl -I https://target.example.com/robots.txt` (and `sitemap.xml`, `.git/HEAD`, `.env`, `.DS_Store`). MCP follow-up: `burp_scope_modify(add=[...])` for new paths, `browser_navigate` to spot-check hits that require JS to render.
- **Interpret results:** status-code triage (`200` vs `403` vs `301`), length-based false-positive filtering (`-fs` flag), identifying soft-404s, recognising rate-limiting as a "need to slow down" signal (consult `methodology-rules-of-engagement`).
- **Finding writeup:** each genuine hit is either a direct finding ("Exposed `.git` directory" → high severity information disclosure) or feeds forward to `testing-*` skills. Uses `methodology-evidence-capture` conventions.
- **References:** OWASP WSTG WSTG-CONF-04/05; ffuf docs; SecLists project.
- **Authorization note:** standard paragraph verbatim.

### recon-js-analysis

- **name:** `recon-js-analysis`
- **description:** "Extract endpoints, API routes, client-side secrets, and DOM sinks from a target's JavaScript bundles via static download and runtime browser inspection."
- **When to use:** target is an SPA or heavily JS-driven; content-discovery and sitemap crawl have left gaps the bundles would fill.
- **Prerequisite skills:** `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-browser`, optional `mcp-burp`.
- **Signal to look for:** `curl <target>` returns a JS shell and no content; Network tab shows large minified bundles; framework fingerprint points to React/Vue/Angular.
- **Tool commands:** hybrid. Shell: download bundles (`curl -o bundle.js https://target/static/js/main.js`), run `linkfinder -i bundle.js -o cli`, `grep -oE '(api|/v[0-9]+)/[A-Za-z0-9_\-/]+' bundle.js`, `jsluice urls bundle.js`. MCP: `browser_eval("Object.keys(window)")` for exposed globals, `browser_network_log()` for the XHR targets the bundle actually calls, `burp_proxy_history(contains=".js")` for everything Burp has captured.
- **Interpret results:** distinguishing development-only endpoints (feature-flagged off) from reachable ones, recognising common secret-pattern false positives (placeholder API keys), identifying DOM sinks worth handing to `testing-*` skills later.
- **Finding writeup:** hardcoded secrets in JS → high severity credential exposure; undocumented internal API exposed → informational that feeds `testing-*`. References `methodology-evidence-capture`.
- **References:** OWASP WSTG Client-side Testing (WSTG-CLNT-*); LinkFinder and jsluice repos.
- **Authorization note:** standard paragraph verbatim.

### recon-api-enum

- **name:** `recon-api-enum`
- **description:** "Discover and enumerate web APIs — OpenAPI/Swagger specs, GraphQL introspection, REST versioning — by probing well-known paths and inspecting proxy history."
- **When to use:** target has an API surface (mobile app backend, SPA backend, B2B endpoints); before testing API-specific attack classes.
- **Prerequisite skills:** `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-burp`.
- **Signal to look for:** Network tab shows JSON responses with API-shaped URLs (`/api`, `/v1`, `/graphql`); `Content-Type: application/json`; CORS preflight responses.
- **Tool commands:** hybrid. Shell: `curl -s https://target.example.com/swagger/v1/swagger.json | jq .`; `curl -s https://target.example.com/openapi.json`; `curl -s https://target.example.com/v2/api-docs`; GraphQL introspection query (full POST body in the skill). MCP: `burp_proxy_history(host="target.example.com", contains="/api")` for previously captured API traffic, `burp_repeater_send` with the GraphQL introspection body for live probing.
- **Interpret results:** recognising disabled-but-still-responsive introspection, distinguishing versioned APIs (v1 legacy vs v2 current), identifying authentication models (bearer token, cookie, API key in header).
- **Finding writeup:** publicly exposed internal API spec → information disclosure (medium); introspection enabled in production → medium; unauthenticated sensitive endpoint → high/critical per future `reporting-*` severity guidance. References `methodology-evidence-capture`.
- **References:** OWASP API Security Top 10; Swagger/OpenAPI spec; GraphQL Introspection docs.
- **Authorization note:** standard paragraph verbatim.

### recon-sitemap-crawl

- **name:** `recon-sitemap-crawl`
- **description:** "Organise the recon phase's collected traffic into an attack-surface map by driving browser-mcp for authenticated crawling and consulting burp-mcp's sitemap for what Burp already captured."
- **When to use:** multiple sources of partial traffic exist (browser sessions, ffuf hits, API probes); need a single inventory before transitioning to active testing.
- **Prerequisite skills:** `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-browser`, `mcp-burp`.
- **Signal to look for:** recon is "done enough" but no single inventory exists; attack-surface mental model is fragmented across tools.
- **Tool commands:** MCP-native (primary). `burp_sitemap(prefix="https://target.example.com", limit=500)` for everything Burp already knows; `browser_launch(headless=true, proxy="127.0.0.1:8080")` + authenticated `browser_navigate`/`browser_click` loop for linked but uncrawled areas; `browser_network_log()` for XHR-only endpoints; finally `burp_sitemap` again to confirm new paths were captured. Shell-side: optional one-liner to diff the sitemap against content-discovery results.
- **Interpret results:** recognising crawl gaps (routes that require form submission, file upload, or multi-step state); knowing when the sitemap is "complete enough" to proceed to active testing (tie-back to `methodology-phases`).
- **Finding writeup:** typically not an individual finding — feeds `testing-*` skills. If crawl reveals an unintended area (admin UI exposed to unauthenticated users), writes up using `methodology-evidence-capture` conventions.
- **References:** OWASP WSTG WSTG-INFO-07 (Map Execution Paths); Burp Suite sitemap docs.
- **Authorization note:** standard paragraph verbatim.

## Cross-reference map

Approach A: methodology skills sit above recon/testing; recon skills declare prerequisites upward to methodology plus sideways to required MCP skills; no forward references to unwritten sub-projects beyond category-level mentions in `methodology-phases`.

```
methodology-phases
  ├─ names: methodology-scoping, methodology-rules-of-engagement, methodology-evidence-capture
  ├─ names each recon-* skill individually
  └─ names the testing-* and reporting-* categories (no specific skills)

methodology-scoping              ← prerequisite in every recon-* "When to use"
methodology-rules-of-engagement  ← prerequisite in every recon-* "When to use"
methodology-evidence-capture     ← referenced from every recon-* "Finding writeup"

recon-subdomain-enum        → mcp-burp
recon-tech-fingerprinting   → mcp-browser, mcp-burp
recon-content-discovery     → mcp-burp, mcp-browser
recon-js-analysis           → mcp-browser (required), mcp-burp (optional)
recon-api-enum              → mcp-burp
recon-sitemap-crawl         → mcp-browser, mcp-burp
```

All cross-references use skill names in prose (e.g., `` see the `mcp-burp` skill ``), never file paths — per `docs/skill-conventions.md`.

**Prerequisite declaration style:** each recon-* skill's `## When to use` opens with one line in the exact shape:

```
Prerequisite skills: methodology-scoping, methodology-rules-of-engagement, mcp-<x>[, mcp-<y>].
```

## Tool-commands style (hybrid)

For recon-* skills, `## Tool commands` contains both a shell block (canonical external tool invocation with expected success criteria) and an MCP block (how to feed the result into the Web-MCP stack — scope management, spot-check, evidence capture). Where a skill is MCP-native (e.g., `recon-sitemap-crawl`), MCP is primary and shell is a one-liner sidebar. Where a skill has no meaningful MCP integration, the MCP block is a one-line omission comment.

For methodology-* skills, `## Tool commands` is mostly consultative — questions to ask, checklists to follow, occasional one-liner verification calls (e.g., `curl -I` to confirm an asset's owner). No heavy tool orchestration belongs here.

## Authorization notes

- All six recon-* skills end with the standard paragraph verbatim, per conventions.
- `methodology-scoping` and `methodology-rules-of-engagement` treat authorization as their subject matter: the standard paragraph is embedded and expanded in the body rather than appended as a tail-note.
- `methodology-phases` and `methodology-evidence-capture` omit the authorization note with the one-line explanatory comment conventions requires, because neither performs actions against a target.

## Quality bar

Each skill passes the checklist from `docs/skill-conventions.md`:

- [ ] Directory name matches `name:` frontmatter exactly.
- [ ] Frontmatter has exactly two fields (`name`, `description`); description ≤ 180 characters.
- [ ] All 8 H2 sections present (or explicitly omitted with a one-line comment per conventions).
- [ ] At least one concrete tool command or MCP tool call in `## Tool commands`.
- [ ] Authorization handling per the rules above.
- [ ] External links in `## References` resolve at commit time.
- [ ] `SKILL.md` under the ~400-line cap (methodology targets ~150, recon targets ~200-250).

## Discoverability & testing

Claude Code auto-discovers each skill via `.claude/skills/*/SKILL.md` on session start in the repo root.

Manual smoke tests (after implementation, before closing the sub-project):

- "What should I do before I touch this target?" → surfaces `methodology-scoping`.
- "Is it okay to run an automated scan at 3am against this production host?" → surfaces `methodology-rules-of-engagement`.
- "How do I know when to move from recon to active testing?" → surfaces `methodology-phases`.
- "How should I record this finding so someone else can reproduce it?" → surfaces `methodology-evidence-capture`.
- "I need the full list of subdomains for target.com." → surfaces `recon-subdomain-enum`.
- "What tech stack is this site running?" → surfaces `recon-tech-fingerprinting`.
- "I want to find hidden paths and backup files on this host." → surfaces `recon-content-discovery`.
- "The app is a React SPA — what JS should I look at?" → surfaces `recon-js-analysis`.
- "Does this app expose a GraphQL or Swagger endpoint?" → surfaces `recon-api-enum`.
- "I have traffic scattered across browser sessions and Burp — how do I consolidate?" → surfaces `recon-sitemap-crawl`.

## Commit strategy

Ten atomic commits, one per skill, grouped in two series so the dependency order is obvious in `git log`:

1. `feat(skills): methodology-scoping`
2. `feat(skills): methodology-rules-of-engagement`
3. `feat(skills): methodology-phases`
4. `feat(skills): methodology-evidence-capture`
5. `feat(skills): recon-subdomain-enum`
6. `feat(skills): recon-tech-fingerprinting`
7. `feat(skills): recon-content-discovery`
8. `feat(skills): recon-js-analysis`
9. `feat(skills): recon-api-enum`
10. `feat(skills): recon-sitemap-crawl`

The spec and plan documents get their own `docs(spec)` and `docs(plan)` commits, per prior sub-projects.

## Out of scope

- Attack-technique runbooks (`testing-*`) — sub-project 4.
- Reporting / deliverables (`reporting-*`) — sub-project 5.
- Skill loader, validator, or link-checker script — author-enforced per conventions.
- Cloud-resource recon (S3/GCS/Azure blob enumeration) — specialized; add in a later pass if demand materialises.
- OSINT-for-GitHub beyond what `mcp-github` already covers.
- WAF/CDN bypass techniques — folded into `recon-tech-fingerprinting` only at the identification level, not the evasion level.

## Acceptance criteria

1. All ten `SKILL.md` files exist at the paths in the Deliverables section.
2. Each passes the quality-bar checklist above.
3. Cross-references follow the map above; names only, no paths.
4. Manual smoke-test prompts above each surface the intended skill when Claude Code is launched in the repo root.
5. Spec committed to `docs/superpowers/specs/2026-04-17-methodology-recon-skills-design.md`.
6. Ten atomic commits per the Commit strategy section, in dependency order.
