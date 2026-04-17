# Methodology & Recon Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce ten `SKILL.md` files — four `methodology-*` (scoping, rules-of-engagement, phases, evidence-capture) and six `recon-*` (subdomain-enum, tech-fingerprinting, content-discovery, js-analysis, api-enum, sitemap-crawl) — following the format locked in by sub-projects 1 and 2.

**Architecture:** Ten prose markdown files, each at `.claude/skills/<name>/SKILL.md`. Each follows the 8-section template from `docs/skill-conventions.md`. Per Approach A in the spec: methodology skills sit above, recon skills declare prerequisites upward to methodology plus sideways to required MCP skills, forward references stay at the category level only (`testing-*`, `reporting-*`). Recon skills use hybrid `## Tool commands` (shell canonical + MCP follow-up).

**Tech Stack:** Markdown + YAML frontmatter. No code, no automated tests. Structural checks live at the end of each task and in the final verification task.

**Spec:** `docs/superpowers/specs/2026-04-17-methodology-recon-skills-design.md`
**Exemplars:** `.claude/skills/mcp-browser/SKILL.md`, `.claude/skills/mcp-burp/SKILL.md`
**Conventions:** `docs/skill-conventions.md`

**Standard authorization paragraph (verbatim, used on every recon-* skill):**

> Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.

---

### Task 1: `.claude/skills/methodology-scoping/SKILL.md`

**Files:**
- Create: `.claude/skills/methodology-scoping/SKILL.md`

**Source material (the implementer must read these):**
- Spec section "Per-skill content → methodology-scoping" — dictates content.
- `docs/skill-conventions.md` — rules for frontmatter, sections, cross-references.
- `.claude/skills/mcp-browser/SKILL.md` — format exemplar.

- [ ] **Step 1: Create directory + write SKILL.md**

```bash
mkdir -p /home/kali/Web-MCP/.claude/skills/methodology-scoping
```

**Frontmatter (exact):**
```yaml
---
name: methodology-scoping
description: Define the scope of a web application penetration test — in-scope assets, excluded targets, third-party restrictions, credential handling — before any active testing begins.
---
```

**Body (8 H2 sections, in order):**

1. `## When to use` — one paragraph. Use at the start of an engagement; when the target list is ambiguous ("test this site" with no written asset list); when a recon finding surfaces an asset whose scope status is unclear.
2. `## Signal to look for` — bullet points: no written target list; user says "test this site" without clarifying scope; a discovered asset sits on a borderline (shared host, third-party CDN, different domain owned by the same org).
3. `## Test steps` — numbered scoping checklist:
   1. Obtain in-scope URL/IP list from the test sponsor.
   2. Obtain explicit exclusion list (prod data stores, payment systems, specific user accounts).
   3. Confirm third-party and hosted-service restrictions (SaaS, CDN, cloud IaaS — some providers require their own pre-approval).
   4. Confirm credential-handling rules (test accounts vs. real, password rotation, use of MFA).
   5. Confirm data-retention / data-egress limits (what can leave the test environment, how results are stored).
   6. Obtain signed-off scope record (email, PDF, ticket — any durable artifact) and save a path to it.
4. `## Tool commands` — consultative. Include a short template block for the "scope questionnaire" the operator sends to the test sponsor. Include one concrete verification command: `curl -sI https://target.example.com | grep -i '^server\|^x-'` and `dig +short target.example.com NS` as ownership spot-checks. Do not include heavy tool orchestration — methodology skills do not run tools against targets.
5. `## Interpret results` — how to classify an asset: clearly in-scope, clearly out, or "maybe → escalate". For "maybe" assets, stop and ask the sponsor in writing before testing.
6. `## Finding writeup` — one-line omission note: `<!-- Methodology skill — does not itself produce findings. -->`.
7. `## References` — external links: PTES Pre-engagement (`http://www.pentest-standard.org/index.php/Pre-engagement`), OWASP WSTG Introduction (`https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/`), NIST SP 800-115 §3 (`https://csrc.nist.gov/pubs/sp/800/115/final`).
8. `## Authorization note` — treat authorization substantively. Body paragraph (not verbatim boilerplate) explaining that scoping *is* authorization: the point of this skill is to produce the written artifact that makes later testing legitimate. End the paragraph with: *"If no such artifact exists, do not proceed to any recon-* or testing-* skill."*

**Length target:** ≤ 180 lines.

- [ ] **Step 2: Verify frontmatter + section count + length**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/methodology-scoping/SKILL.md
grep -c '^## ' .claude/skills/methodology-scoping/SKILL.md
wc -l .claude/skills/methodology-scoping/SKILL.md
```

Expected: frontmatter block (`---`, `name:`, `description:`, `---`); section count = 8; line count ≤ 180.

- [ ] **Step 3: Verify description length**

```bash
d=$(grep -m1 '^description:' .claude/skills/methodology-scoping/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
```
Expected: ≤ 180.

- [ ] **Step 4: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/methodology-scoping/SKILL.md
git commit -m "feat(skills): methodology-scoping (scope definition + signed-off artifact)"
```

---

### Task 2: `.claude/skills/methodology-rules-of-engagement/SKILL.md`

**Files:**
- Create: `.claude/skills/methodology-rules-of-engagement/SKILL.md`

**Source material:**
- Spec section "Per-skill content → methodology-rules-of-engagement".
- `docs/skill-conventions.md`.
- `.claude/skills/methodology-scoping/SKILL.md` (Task 1 output) — cross-referenced by this skill.
- `.claude/skills/mcp-browser/SKILL.md` — format exemplar.

- [ ] **Step 1: Create directory + write SKILL.md**

```bash
mkdir -p /home/kali/Web-MCP/.claude/skills/methodology-rules-of-engagement
```

**Frontmatter:**
```yaml
---
name: methodology-rules-of-engagement
description: Operational limits for an authorised web pentest — testing windows, rate limits, destructive-action ban, escalation path, safe-shutdown — consulted before any invasive probe.
---
```

**Body — 8 sections:**

1. `## When to use` — before active testing begins; after a probe causes a service anomaly; when a finding's proof-of-concept would require a destructive demonstration; when the testing window is about to close. Open with: *"Prerequisite skills: `methodology-scoping`."*
2. `## Signal to look for` — about to launch an automated scan or brute force; about to demonstrate impact via account takeover or data exfiltration; user asks "is it okay to do X?"; user reports "the site is acting weird after my last test".
3. `## Test steps` — numbered RoE checklist:
   1. Confirm testing window (start/end UTC, allowed days).
   2. Confirm rate limits per host (requests/second, concurrent connections, guidance on how to back off).
   3. Confirm banned actions: no DoS, no destructive data actions beyond a minimal PoC (change-one-benign-record, not drop-a-table), no lateral movement past the in-scope boundary, no exfiltration beyond what's needed to prove the finding.
   4. Confirm outage-escalation path: phone/pager of a 24×7 contact + Slack/email fallback.
   5. Confirm safe-shutdown procedure: what to do if you detect your traffic has triggered an incident.
4. `## Tool commands` — consultative; brief template for the "RoE confirmation" message you send the sponsor before go-live. Cross-reference `methodology-evidence-capture` for preserving the before/after state when running an invasive probe.
5. `## Interpret results` — green-light conditions (all five checklist items signed off in writing) vs. "pause and escalate" conditions (any item missing, or a mid-test anomaly exceeds the agreed threshold).
6. `## Finding writeup` — one-line omission note: `<!-- Methodology skill — does not itself produce findings. -->`.
7. `## References` — PTES Rules of Engagement (`http://www.pentest-standard.org/index.php/Pre-engagement#Rules_of_Engagement`), OWASP WSTG Test Execution section.
8. `## Authorization note` — body paragraph treating authorization substantively. Emphasise that the signed-off RoE is what makes otherwise-invasive actions legitimate; without it, none of the recon-* or testing-* skills should run. End with: *"If any RoE item is unconfirmed, stop and obtain confirmation in writing before proceeding."*

**Length target:** ≤ 180 lines.

- [ ] **Step 2: Verify frontmatter + section count + length**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/methodology-rules-of-engagement/SKILL.md
grep -c '^## ' .claude/skills/methodology-rules-of-engagement/SKILL.md
wc -l .claude/skills/methodology-rules-of-engagement/SKILL.md
```
Expected: frontmatter block; section count = 8; line count ≤ 180.

- [ ] **Step 3: Verify description length**

```bash
d=$(grep -m1 '^description:' .claude/skills/methodology-rules-of-engagement/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
```
Expected: ≤ 180.

- [ ] **Step 4: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/methodology-rules-of-engagement/SKILL.md
git commit -m "feat(skills): methodology-rules-of-engagement (testing windows, rate limits, escalation)"
```

---

### Task 3: `.claude/skills/methodology-phases/SKILL.md`

**Files:**
- Create: `.claude/skills/methodology-phases/SKILL.md`

**Source material:**
- Spec section "Per-skill content → methodology-phases".
- `docs/skill-conventions.md`.
- `.claude/skills/methodology-scoping/SKILL.md`, `.claude/skills/methodology-rules-of-engagement/SKILL.md` (Tasks 1-2 outputs).
- `.claude/skills/mcp-browser/SKILL.md`, `.claude/skills/mcp-burp/SKILL.md` — named by this skill.

- [ ] **Step 1: Create directory + write SKILL.md**

```bash
mkdir -p /home/kali/Web-MCP/.claude/skills/methodology-phases
```

**Frontmatter:**
```yaml
---
name: methodology-phases
description: Sequence a web pentest engagement across scope, recon, discovery, exploit, and report phases — guides when Claude should reach for methodology, recon, testing, or reporting skills.
---
```

**Body — 8 sections:**

1. `## When to use` — at engagement start (to plan); mid-engagement (to decide whether enough recon has been done before exploitation); at finding confirmation (to decide whether to move to write-up).
2. `## Signal to look for` — user asks "what should I do next?" without a specific step; Claude has just produced a recon artifact and must decide whether to move to active testing; a finding has been confirmed but no write-up exists yet.
3. `## Test steps` — a phase-by-phase decision tree. Each phase is its own numbered block. Write each block as:

   **Phase 1: Scope & Rules of Engagement.** Enter: engagement kickoff. Skills: `methodology-scoping`, `methodology-rules-of-engagement`. Exit criteria: signed-off scope and RoE artifact exists.

   **Phase 2: Recon.** Enter: Phase 1 exit met. Skills (in rough order of use): `recon-subdomain-enum`, `recon-tech-fingerprinting`, `recon-content-discovery`, `recon-js-analysis`, `recon-api-enum`, `recon-sitemap-crawl`. Exit criteria: attack-surface inventory exists; `burp_sitemap` returns a populated list for every in-scope host.

   **Phase 3: Discovery.** Enter: Phase 2 exit met. Skills: the `testing-*` category (future sub-project 4). Exit criteria: at least one reproducible positive or negative result for each attack class the tester decides to cover.

   **Phase 4: Exploit.** Enter: Phase 3 produces a positive. Skills: relevant `testing-*` skill + `methodology-evidence-capture` for every confirmed issue. Exit criteria: reproducible PoC + captured evidence for every finding.

   **Phase 5: Report.** Enter: exploitation phase concluded or testing window closed. Skills: the `reporting-*` category (future sub-project 5) + `methodology-evidence-capture` consumed by that category. Exit criteria: deliverable produced + findings handed off.

4. `## Tool commands` — minimal. One concrete "recon-complete checkpoint" shell + MCP one-liner: `burp_sitemap(prefix="https://target.example.com", limit=500)` — if the list is densely populated across the in-scope hosts, Phase 2 is done.
5. `## Interpret results` — phase-exit criteria restated: Phase 1 produces paperwork; Phase 2 produces an inventory; Phase 3 produces decisions about which attack classes to pursue; Phase 4 produces findings with evidence; Phase 5 produces a deliverable.
6. `## Finding writeup` — one-line omission note: `<!-- Methodology skill — does not itself produce findings. -->`.
7. `## References` — PTES Execution Standard (`http://www.pentest-standard.org/`), OWASP WSTG Framework (`https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/`).
8. `## Authorization note` — one-line omission comment: `<!-- Methodology skill — does not itself perform actions against a target; authorization is handled in methodology-scoping and methodology-rules-of-engagement. -->`.

**Length target:** ≤ 200 lines (this one is slightly longer because the phases table).

- [ ] **Step 2: Verify frontmatter + section count + length**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/methodology-phases/SKILL.md
grep -c '^## ' .claude/skills/methodology-phases/SKILL.md
wc -l .claude/skills/methodology-phases/SKILL.md
```
Expected: frontmatter block; section count = 8; line count ≤ 200.

- [ ] **Step 3: Verify description length**

```bash
d=$(grep -m1 '^description:' .claude/skills/methodology-phases/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
```
Expected: ≤ 180.

- [ ] **Step 4: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/methodology-phases/SKILL.md
git commit -m "feat(skills): methodology-phases (5-phase decision tree)"
```

---

### Task 4: `.claude/skills/methodology-evidence-capture/SKILL.md`

**Files:**
- Create: `.claude/skills/methodology-evidence-capture/SKILL.md`

**Source material:**
- Spec section "Per-skill content → methodology-evidence-capture".
- `docs/skill-conventions.md`.
- `.claude/skills/mcp-browser/SKILL.md`, `.claude/skills/mcp-burp/SKILL.md`, `.claude/skills/mcp-github/SKILL.md` — referenced for evidence-capture tool calls.

- [ ] **Step 1: Create directory + write SKILL.md**

```bash
mkdir -p /home/kali/Web-MCP/.claude/skills/methodology-evidence-capture
```

**Frontmatter:**
```yaml
---
name: methodology-evidence-capture
description: Reproducible evidence conventions for web pentest findings — screenshot formats, raw request/response preservation, numbered MCP tool-call reproduction steps, source-code references.
---
```

**Body — 8 sections:**

1. `## When to use` — every time a finding is confirmed and must be documented; before closing out a proxy session (evidence dies with the session); when a run-once runtime observation must be preserved (dynamic token, one-time redirect, etc.).
2. `## Signal to look for` — a probe produced a positive result that now needs a finding; Claude is about to move on from a reproducible runtime observation; a finding's reproduction depends on session state that is about to be lost.
3. `## Test steps` — evidence checklist (numbered):
   1. Save the raw HTTP request via `burp_proxy_request(id=N)` (both `request` and `response` fields).
   2. Capture a rendered screenshot via `browser_screenshot(full_page=true)` — required if the bug has a visible UI component; optional otherwise.
   3. Record the numbered MCP tool-call sequence that reproduced the bug, verbatim. Another operator must be able to paste the sequence into a fresh Claude session and reproduce.
   4. If the finding references source code, include repo + commit SHA + line range (e.g. `src/api/export.py#L42-L57 @ abc123`). Use `mcp-github` tools for the lookup if the repo is on GitHub.
   5. Record timestamps in UTC for each step.
4. `## Tool commands` — concrete MCP examples:
   - `burp_proxy_request(id=12)` — save full raw request + response.
   - `browser_screenshot(full_page=true)` — save rendered screenshot as PNG (base64 in the response, decode and write to a file in the engagement's evidence directory).
   - `burp_repeater_send(raw_base64=<b64>, host=..., port=443, secure=true, tab_name="repro-<finding-id>")` — parameterised reproduction.
   - `github_get_file_contents(repo="org/name", path="src/api/export.py", ref="<sha>")` — source-side evidence.

   Include a short template block showing the preferred evidence-directory layout, e.g.:
   ```
   evidence/
   ├── F-001-exposed-git/
   │   ├── request.http
   │   ├── response.http
   │   ├── screenshot.png
   │   └── repro.md
   ```
5. `## Interpret results` — what counts as reproducible: third party can re-run the numbered tool-call sequence and see the same outcome. Non-reproducible: state was lost (session cookie expired, one-time token burned); re-capture before write-up.
6. `## Finding writeup` — one-line omission note: `<!-- Methodology skill — this file defines the finding writeup shape the rest of the library consumes. -->`.
7. `## References` — OWASP WSTG Reporting section, NIST SP 800-115 §6 (`https://csrc.nist.gov/pubs/sp/800/115/final`).
8. `## Authorization note` — one-line omission comment: `<!-- Methodology skill — does not itself perform actions against a target; authorization is handled in methodology-scoping and methodology-rules-of-engagement. -->`.

**Length target:** ≤ 200 lines.

- [ ] **Step 2: Verify frontmatter + section count + length**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/methodology-evidence-capture/SKILL.md
grep -c '^## ' .claude/skills/methodology-evidence-capture/SKILL.md
wc -l .claude/skills/methodology-evidence-capture/SKILL.md
```
Expected: frontmatter block; section count = 8; line count ≤ 200.

- [ ] **Step 3: Verify description length**

```bash
d=$(grep -m1 '^description:' .claude/skills/methodology-evidence-capture/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
```
Expected: ≤ 180.

- [ ] **Step 4: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/methodology-evidence-capture/SKILL.md
git commit -m "feat(skills): methodology-evidence-capture (reproducible evidence contract)"
```

---

### Task 5: `.claude/skills/recon-subdomain-enum/SKILL.md`

**Files:**
- Create: `.claude/skills/recon-subdomain-enum/SKILL.md`

**Source material:**
- Spec section "Per-skill content → recon-subdomain-enum".
- `docs/skill-conventions.md`.
- `.claude/skills/methodology-scoping/SKILL.md`, `.claude/skills/methodology-rules-of-engagement/SKILL.md`, `.claude/skills/mcp-burp/SKILL.md` — named as prerequisites.
- `.claude/skills/methodology-evidence-capture/SKILL.md` — referenced in Finding writeup.

- [ ] **Step 1: Create directory + write SKILL.md**

```bash
mkdir -p /home/kali/Web-MCP/.claude/skills/recon-subdomain-enum
```

**Frontmatter:**
```yaml
---
name: recon-subdomain-enum
description: Enumerate subdomains of a target organisation using passive sources (CT logs, passive DNS) and active probes, then load results into Burp scope for downstream testing.
---
```

**Body — 8 sections:**

1. `## When to use` — open with the prerequisite line: *"Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-burp`."* Then one paragraph on when this skill applies (early-phase recon, expanding attack surface beyond an initial URL).
2. `## Signal to look for` — engagement lists a root domain without specific hosts; a newly-discovered asset may have siblings; tech fingerprinting shows cloud-hosted infra where siblings commonly cluster.
3. `## Test steps` — numbered flow:
   1. Run passive enumeration: `subfinder -d target.com -silent`.
   2. Run CT log harvest: `curl -s 'https://crt.sh/?q=%25.target.com&output=json' | jq -r '.[].name_value' | sort -u`.
   3. Optional active: `amass enum -passive -d target.com` (passive mode only — active mode would violate RoE rate limits; see `methodology-rules-of-engagement`).
   4. De-duplicate + filter to in-scope host wildcards from `methodology-scoping`.
   5. Load newly confirmed in-scope hosts into Burp: `burp_scope_modify(add=["https://newsub.target.com"])`.
   6. Optional: resolve each with `dig +short <host>` to filter unreachable entries.
4. `## Tool commands` — hybrid:
   - **Shell (canonical):**
     ```
     subfinder -d target.com -silent
     # Success: prints one hostname per line
     curl -s 'https://crt.sh/?q=%25.target.com&output=json' | jq -r '.[].name_value' | sort -u
     # Success: deduped list from Certificate Transparency logs
     amass enum -passive -d target.com
     # Success: hostnames across multiple passive sources
     ```
   - **MCP follow-up:**
     ```
     burp_scope_check(urls=["https://newsub.target.com"])
     burp_scope_modify(add=["https://newsub.target.com"], remove=[])
     # Success: {"ok": true, "data": {"added": 1, "removed": 0}}
     ```
5. `## Interpret results` — owned vs third-party: `_acme-challenge.*` CNAMEs are ACME DNS-01 records, not hosts you can test. Wildcard DNS produces false positives (every name resolves). Stale CT entries: certs issued long ago may point to hosts that no longer exist — always verify reachability before testing.
6. `## Finding writeup` — typically not an individual finding (feeds attack-surface inventory). If an unintended asset is exposed (dev/staging publicly reachable when it shouldn't be), write up as **"Exposed non-production asset"**, severity Low-Medium (raise if the asset leaks credentials or customer data). Evidence per `methodology-evidence-capture`: include the passive-source hit, a `curl -I` showing the asset is reachable, and a `burp_sitemap` entry if present.
7. `## References` — OWASP WSTG Information Gathering WSTG-INFO-04 (`https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/04-Enumerate_Applications_on_Webserver`), crt.sh (`https://crt.sh/`), ProjectDiscovery Subfinder docs (`https://docs.projectdiscovery.io/tools/subfinder/`).
8. `## Authorization note` — **standard paragraph verbatim** (the exact three-sentence block at the top of this plan).

**Length target:** ≤ 240 lines.

- [ ] **Step 2: Verify frontmatter + section count + length**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/recon-subdomain-enum/SKILL.md
grep -c '^## ' .claude/skills/recon-subdomain-enum/SKILL.md
wc -l .claude/skills/recon-subdomain-enum/SKILL.md
```
Expected: frontmatter block; section count = 8; line count ≤ 240.

- [ ] **Step 3: Verify description length**

```bash
d=$(grep -m1 '^description:' .claude/skills/recon-subdomain-enum/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
```
Expected: ≤ 180.

- [ ] **Step 4: Verify authorization paragraph present verbatim**

```bash
grep -q "Only use against systems you are authorized to test" .claude/skills/recon-subdomain-enum/SKILL.md && echo OK || echo MISSING
```
Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/recon-subdomain-enum/SKILL.md
git commit -m "feat(skills): recon-subdomain-enum (passive CT + active feed to Burp scope)"
```

---

### Task 6: `.claude/skills/recon-tech-fingerprinting/SKILL.md`

**Files:**
- Create: `.claude/skills/recon-tech-fingerprinting/SKILL.md`

**Source material:**
- Spec section "Per-skill content → recon-tech-fingerprinting".
- `docs/skill-conventions.md`.
- Methodology + mcp-browser + mcp-burp skills — named as prerequisites.

- [ ] **Step 1: Create directory + write SKILL.md**

```bash
mkdir -p /home/kali/Web-MCP/.claude/skills/recon-tech-fingerprinting
```

**Frontmatter:**
```yaml
---
name: recon-tech-fingerprinting
description: Identify the technology stack (web server, framework, CMS, WAF/CDN) behind a target using header analysis, cookie tells, error-page signatures, and rendered-DOM inspection.
---
```

**Body — 8 sections:**

1. `## When to use` — prereq line: *"Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-browser`, `mcp-burp`."* Paragraph: before selecting attack classes; when a framework-specific test skill must be chosen; when a CDN/WAF may alter response bodies.
2. `## Signal to look for` — target is a black-box HTTP service; about to pick an attack technique without knowing the stack; probe results look inconsistent across hosts (possibly CDN interference).
3. `## Test steps`:
   1. Grab headers and status page: `curl -sI https://target.example.com` and `curl -s https://target.example.com/ | head -40`.
   2. Run Wappalyzer / WhatWeb: `whatweb -a3 https://target.example.com` and/or `wappalyzer https://target.example.com` (if CLI available).
   3. Drive the browser for rendered fingerprint: `browser_launch(headless=true, proxy="127.0.0.1:8080")`, `browser_navigate(url="https://target.example.com")`, `browser_snapshot()`.
   4. Review captured headers via `burp_proxy_history(host="target.example.com", limit=50)` — look for `X-Powered-By`, `Server`, framework cookies.
   5. Probe an invalid route (`curl -sI https://target.example.com/xyz-404`) to elicit a framework-specific error page (e.g. Django debug page, Rails error tell).
4. `## Tool commands` — hybrid:
   - **Shell:** `whatweb -a3 https://target.example.com` (success: grouped plugin-based fingerprint lines); `curl -sI https://target.example.com` (success: header block).
   - **MCP:** `browser_navigate(url=...)` + `browser_snapshot()` (rendered DOM), `burp_proxy_history(host="target.example.com")` for all captured response headers.
5. `## Interpret results` — strong signals (`X-Powered-By: PHP/7.4.3`, `JSESSIONID` cookie = Java servlet, `connect.sid` = Node `express-session`, `csrftoken` = Django, CSP domains tell you CDN vendor). Weak signals (generic `Server: nginx` — the upstream could be anything). WAF presence (Cloudflare `cf-ray`, Akamai `akamai-*`, AWS WAF response-body watermark). Note WAF presence because it informs payload delivery and may cause false negatives downstream.
6. `## Finding writeup` — typically informational. A detailed, unredacted stack banner (e.g. `X-Powered-By: PHP/5.2.17`) can itself be an **"Information Disclosure"** finding (severity Low). Evidence per `methodology-evidence-capture`: the response header block.
7. `## References` — OWASP WSTG WSTG-INFO-02/08/09, WhatWeb docs (`https://github.com/urbanadventurer/WhatWeb`), Wappalyzer docs (`https://www.wappalyzer.com/`).
8. `## Authorization note` — standard paragraph verbatim.

**Length target:** ≤ 240 lines.

- [ ] **Step 2: Verify frontmatter + section count + length**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/recon-tech-fingerprinting/SKILL.md
grep -c '^## ' .claude/skills/recon-tech-fingerprinting/SKILL.md
wc -l .claude/skills/recon-tech-fingerprinting/SKILL.md
```
Expected: frontmatter block; section count = 8; line count ≤ 240.

- [ ] **Step 3: Verify description length**

```bash
d=$(grep -m1 '^description:' .claude/skills/recon-tech-fingerprinting/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
```
Expected: ≤ 180.

- [ ] **Step 4: Verify authorization paragraph present verbatim**

```bash
grep -q "Only use against systems you are authorized to test" .claude/skills/recon-tech-fingerprinting/SKILL.md && echo OK || echo MISSING
```
Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/recon-tech-fingerprinting/SKILL.md
git commit -m "feat(skills): recon-tech-fingerprinting (headers, cookies, rendered-DOM tells)"
```

---

### Task 7: `.claude/skills/recon-content-discovery/SKILL.md`

**Files:**
- Create: `.claude/skills/recon-content-discovery/SKILL.md`

**Source material:**
- Spec section "Per-skill content → recon-content-discovery".
- `docs/skill-conventions.md`.
- Methodology + mcp-burp + mcp-browser skills — named as prerequisites.

- [ ] **Step 1: Create directory + write SKILL.md**

```bash
mkdir -p /home/kali/Web-MCP/.claude/skills/recon-content-discovery
```

**Frontmatter:**
```yaml
---
name: recon-content-discovery
description: Discover hidden endpoints, backup files, and configuration artifacts on a web target using wordlist-based enumeration (ffuf/dirsearch/gobuster) plus common low-hanging paths.
---
```

**Body — 8 sections:**

1. `## When to use` — prereq line: *"Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-burp`, `mcp-browser`."* Paragraph: after scope is settled and the public surface is known; find what isn't linked.
2. `## Signal to look for` — target has a large, unknown attack surface; framework hints suggest unprotected dev/admin endpoints; backup or source-control files may be exposed.
3. `## Test steps`:
   1. Check low-hanging paths first: `curl -sI https://target.example.com/robots.txt`, `.../sitemap.xml`, `.../.git/HEAD`, `.../.env`, `.../.DS_Store`, `.../backup.zip`.
   2. Run ffuf with a common wordlist: `ffuf -u https://target.example.com/FUZZ -w /usr/share/wordlists/dirb/common.txt -mc 200,301,403`. Respect RoE rate limits (`-rate 10`).
   3. Optional: `dirsearch -u https://target.example.com -e php,bak,old,zip,tar,gz,sql`.
   4. Load confirmed hits into Burp scope: `burp_scope_modify(add=["https://target.example.com/hidden-path"])`.
   5. Spot-check hits that require JS to render: `browser_navigate(url="https://target.example.com/hidden-path")`, `browser_snapshot()`.
4. `## Tool commands` — hybrid:
   - **Shell canonical:**
     ```
     ffuf -u https://target.example.com/FUZZ -w /usr/share/wordlists/dirb/common.txt -mc 200,301,403 -rate 10 -o ffuf.json -of json
     # Success: ffuf.json contains the matched paths; stdout shows hit summary
     ```
   - **Shell low-hanging:**
     ```
     for p in robots.txt sitemap.xml .git/HEAD .env .DS_Store backup.zip; do
       curl -sI "https://target.example.com/$p" | head -1
     done
     ```
   - **MCP follow-up:**
     ```
     burp_scope_modify(add=["https://target.example.com/admin"])
     browser_navigate(url="https://target.example.com/admin")
     browser_snapshot()
     ```
5. `## Interpret results` — status-code triage: `200` = reachable content, `301` = redirect (follow and re-probe), `403` = resource exists but access controlled (document and move on; don't try to bypass without RoE clearance). Length-based false-positive filter: `-fs` or `-fw` flag to ignore boilerplate 404s that return 200 with a standard length. Soft-404s: pages that return 200 but are actually error pages — inspect via `browser_snapshot`. Rate-limiting response (429 or artificial delays) is the signal to consult `methodology-rules-of-engagement` and back off.
6. `## Finding writeup` — each confirmed hit is either a direct finding or feeds forward. Direct findings: **"Exposed `.git` Directory"** (High severity — full source leak), **"Exposed `.env` File"** (High — credentials), **"Backup File Accessible"** (Medium-High depending on contents). Evidence per `methodology-evidence-capture`: `curl -I` output and a `burp_proxy_request` entry for the full response body.
7. `## References` — OWASP WSTG WSTG-CONF-04/05, ffuf docs (`https://github.com/ffuf/ffuf`), SecLists project (`https://github.com/danielmiessler/SecLists`).
8. `## Authorization note` — standard paragraph verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2: Verify frontmatter + section count + length**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/recon-content-discovery/SKILL.md
grep -c '^## ' .claude/skills/recon-content-discovery/SKILL.md
wc -l .claude/skills/recon-content-discovery/SKILL.md
```
Expected: frontmatter block; section count = 8; line count ≤ 260.

- [ ] **Step 3: Verify description length**

```bash
d=$(grep -m1 '^description:' .claude/skills/recon-content-discovery/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
```
Expected: ≤ 180.

- [ ] **Step 4: Verify authorization paragraph present verbatim**

```bash
grep -q "Only use against systems you are authorized to test" .claude/skills/recon-content-discovery/SKILL.md && echo OK || echo MISSING
```
Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/recon-content-discovery/SKILL.md
git commit -m "feat(skills): recon-content-discovery (ffuf/dirsearch + low-hanging paths)"
```

---

### Task 8: `.claude/skills/recon-js-analysis/SKILL.md`

**Files:**
- Create: `.claude/skills/recon-js-analysis/SKILL.md`

**Source material:**
- Spec section "Per-skill content → recon-js-analysis".
- `docs/skill-conventions.md`.
- Methodology + mcp-browser (required) + mcp-burp (optional) skills.

- [ ] **Step 1: Create directory + write SKILL.md**

```bash
mkdir -p /home/kali/Web-MCP/.claude/skills/recon-js-analysis
```

**Frontmatter:**
```yaml
---
name: recon-js-analysis
description: Extract endpoints, API routes, client-side secrets, and DOM sinks from a target's JavaScript bundles via static download and runtime browser inspection.
---
```

**Body — 8 sections:**

1. `## When to use` — prereq line: *"Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-browser`. Optional: `mcp-burp`."* Paragraph: target is an SPA or heavily JS-driven; content-discovery and sitemap crawl have left gaps that the bundles would fill.
2. `## Signal to look for` — `curl <target>` returns a JS shell with almost no content; Network tab shows large minified bundles; framework fingerprint points to React/Vue/Angular/Svelte.
3. `## Test steps`:
   1. Inventory bundles: `browser_navigate(url="https://target.example.com")`, `browser_network_log(since_seq=0)` — filter for `.js` URLs.
   2. Download each bundle: `curl -o main.js https://target.example.com/static/js/main.js` (repeat per bundle).
   3. Extract endpoints: `linkfinder -i main.js -o cli` (or `jsluice urls main.js`). Fallback grep: `grep -oE '(api|/v[0-9]+)/[A-Za-z0-9_\-/]+' main.js | sort -u`.
   4. Runtime inspection: `browser_eval(expression="Object.keys(window).filter(k => !Object.keys(window).includes.call([], k))")` for exposed globals, `browser_eval(expression="document.querySelectorAll('[data-*]').length")` for framework hints.
   5. Correlate with captured traffic: `burp_proxy_history(host="target.example.com", contains=".js")` and `burp_proxy_history(contains="/api")`.
4. `## Tool commands` — hybrid:
   - **Shell:**
     ```
     curl -o main.js https://target.example.com/static/js/main.js
     linkfinder -i main.js -o cli
     jsluice urls main.js
     grep -oE '(api|/v[0-9]+)/[A-Za-z0-9_\-/]+' main.js | sort -u
     ```
   - **MCP:**
     ```
     browser_network_log(since_seq=0)   # find all bundle URLs
     browser_eval(expression="Object.keys(window).length")   # exposed globals
     burp_proxy_history(contains=".js") # everything Burp captured
     ```
5. `## Interpret results` — development-only endpoints may appear in the bundle but be feature-flagged off at runtime; confirm reachability before reporting. Placeholder API keys (`YOUR_API_KEY_HERE`, `xxxx-xxxx`, `sk_test_*`) are false positives; real secrets look like `sk_live_*` or high-entropy random strings. DOM sinks (`innerHTML`, `document.write`, `eval`, `setTimeout(string, ...)`) identified here feed the future `testing-*` category (XSS work).
6. `## Finding writeup` — hardcoded production secret in JS → **"Credential Exposure in JavaScript Bundle"** (High-Critical). Undocumented internal API → informational that feeds `testing-*` skills. Evidence per `methodology-evidence-capture`: the bundle URL, line number of the hit, and the `browser_navigate` + `browser_network_log` sequence that observed it in use.
7. `## References` — OWASP WSTG Client-side Testing (WSTG-CLNT-*, `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/`), LinkFinder repo (`https://github.com/GerbenJavado/LinkFinder`), jsluice repo (`https://github.com/BishopFox/jsluice`).
8. `## Authorization note` — standard paragraph verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2: Verify frontmatter + section count + length**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/recon-js-analysis/SKILL.md
grep -c '^## ' .claude/skills/recon-js-analysis/SKILL.md
wc -l .claude/skills/recon-js-analysis/SKILL.md
```
Expected: frontmatter block; section count = 8; line count ≤ 260.

- [ ] **Step 3: Verify description length**

```bash
d=$(grep -m1 '^description:' .claude/skills/recon-js-analysis/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
```
Expected: ≤ 180.

- [ ] **Step 4: Verify authorization paragraph present verbatim**

```bash
grep -q "Only use against systems you are authorized to test" .claude/skills/recon-js-analysis/SKILL.md && echo OK || echo MISSING
```
Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/recon-js-analysis/SKILL.md
git commit -m "feat(skills): recon-js-analysis (static LinkFinder/jsluice + runtime browser_eval)"
```

---

### Task 9: `.claude/skills/recon-api-enum/SKILL.md`

**Files:**
- Create: `.claude/skills/recon-api-enum/SKILL.md`

**Source material:**
- Spec section "Per-skill content → recon-api-enum".
- `docs/skill-conventions.md`.
- Methodology + mcp-burp skills.

- [ ] **Step 1: Create directory + write SKILL.md**

```bash
mkdir -p /home/kali/Web-MCP/.claude/skills/recon-api-enum
```

**Frontmatter:**
```yaml
---
name: recon-api-enum
description: Discover and enumerate web APIs — OpenAPI/Swagger specs, GraphQL introspection, REST versioning — by probing well-known paths and inspecting proxy history.
---
```

**Body — 8 sections:**

1. `## When to use` — prereq line: *"Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-burp`."* Paragraph: target has an API surface (mobile backend, SPA backend, B2B endpoints); before testing API-specific attack classes.
2. `## Signal to look for` — Network tab shows JSON responses with API-shaped URLs (`/api`, `/v1`, `/graphql`); `Content-Type: application/json`; CORS preflight responses; mobile app is in scope.
3. `## Test steps`:
   1. Probe well-known OpenAPI paths: `curl -s https://target.example.com/swagger/v1/swagger.json`, `.../openapi.json`, `.../v2/api-docs`, `.../swagger-ui.html`, `.../api-docs`.
   2. If GraphQL endpoint exists (`/graphql`, `/api/graphql`), probe introspection:
      ```
      curl -s -X POST https://target.example.com/graphql \
        -H 'Content-Type: application/json' \
        --data '{"query":"query IntrospectionQuery { __schema { types { name kind description } } }"}'
      ```
   3. Review Burp for already-captured API traffic: `burp_proxy_history(host="target.example.com", contains="/api")`.
   4. If spec found: download it, summarise endpoints, identify authentication model.
   5. If introspection succeeds: save the schema; identify queries/mutations; note access control model.
   6. Replay an interesting introspection query via `burp_repeater_send(raw_base64=<b64>, host="target.example.com", port=443, secure=true)`.
4. `## Tool commands` — hybrid:
   - **Shell:**
     ```
     curl -s https://target.example.com/swagger/v1/swagger.json | jq . | head -60
     curl -s https://target.example.com/openapi.json | jq .paths | head
     curl -s -X POST https://target.example.com/graphql \
       -H 'Content-Type: application/json' \
       --data '{"query":"{ __schema { types { name } } }"}'
     ```
   - **MCP:**
     ```
     burp_proxy_history(host="target.example.com", contains="/api", limit=100)
     # For replay:
     burp_repeater_send(raw_base64="<base64-of-full-POST-body>", host="target.example.com", port=443, secure=true)
     ```
5. `## Interpret results` — disabled-but-still-responsive introspection: some frameworks reject the query but leak the schema via error messages — check error shape. Versioned APIs: `v1` often has weaker auth than `v2`; enumerate both. Authentication models: `Authorization: Bearer <jwt>` vs session cookie vs `X-API-Key` header; each has different attack surface.
6. `## Finding writeup` — publicly exposed internal OpenAPI spec → **"Information Disclosure (API Specification)"** (Medium). GraphQL introspection enabled in production → **"GraphQL Introspection Enabled"** (Medium). Unauthenticated sensitive endpoint → High/Critical per future `reporting-*` severity guidance. Evidence per `methodology-evidence-capture`: the spec URL, the raw JSON response, the `burp_repeater_send` tab reproducing the query.
7. `## References` — OWASP API Security Top 10 (`https://owasp.org/www-project-api-security/`), Swagger/OpenAPI spec (`https://spec.openapis.org/`), GraphQL Introspection docs (`https://graphql.org/learn/introspection/`).
8. `## Authorization note` — standard paragraph verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2: Verify frontmatter + section count + length**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/recon-api-enum/SKILL.md
grep -c '^## ' .claude/skills/recon-api-enum/SKILL.md
wc -l .claude/skills/recon-api-enum/SKILL.md
```
Expected: frontmatter block; section count = 8; line count ≤ 260.

- [ ] **Step 3: Verify description length**

```bash
d=$(grep -m1 '^description:' .claude/skills/recon-api-enum/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
```
Expected: ≤ 180.

- [ ] **Step 4: Verify authorization paragraph present verbatim**

```bash
grep -q "Only use against systems you are authorized to test" .claude/skills/recon-api-enum/SKILL.md && echo OK || echo MISSING
```
Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/recon-api-enum/SKILL.md
git commit -m "feat(skills): recon-api-enum (Swagger/OpenAPI + GraphQL introspection)"
```

---

### Task 10: `.claude/skills/recon-sitemap-crawl/SKILL.md`

**Files:**
- Create: `.claude/skills/recon-sitemap-crawl/SKILL.md`

**Source material:**
- Spec section "Per-skill content → recon-sitemap-crawl".
- `docs/skill-conventions.md`.
- Methodology + mcp-browser + mcp-burp skills.

- [ ] **Step 1: Create directory + write SKILL.md**

```bash
mkdir -p /home/kali/Web-MCP/.claude/skills/recon-sitemap-crawl
```

**Frontmatter:**
```yaml
---
name: recon-sitemap-crawl
description: Organise the recon phase's collected traffic into an attack-surface map by driving browser-mcp for authenticated crawling and consulting burp-mcp's sitemap for what Burp already captured.
---
```

**Body — 8 sections:**

1. `## When to use` — prereq line: *"Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-browser`, `mcp-burp`."* Paragraph: multiple sources of partial traffic exist (browser sessions, ffuf hits, API probes); need a single inventory before transitioning to active testing.
2. `## Signal to look for` — recon is "done enough" but no single inventory exists; attack-surface mental model is fragmented across tools; about to exit Phase 2 per `methodology-phases`.
3. `## Test steps`:
   1. Baseline: `burp_sitemap(prefix="https://target.example.com", limit=500)` — save what Burp already knows.
   2. Authenticated browser crawl: `browser_launch(headless=true, proxy="127.0.0.1:8080")`, `browser_navigate(url="https://target.example.com/login")`, `browser_fill` + `browser_click` to authenticate.
   3. Walk the app's visible menu structure with `browser_click` + `browser_navigate` to linked-but-uncrawled pages.
   4. Surface XHR-only endpoints: `browser_network_log(since_seq=0)`.
   5. Re-check Burp: `burp_sitemap(prefix="https://target.example.com", limit=500)` — new paths should now appear.
   6. Optional shell diff: write both sitemap lists to files and `diff` them against the ffuf results from `recon-content-discovery`.
4. `## Tool commands` — MCP-native primary:
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
   Optional shell:
   ```
   # Diff Burp sitemap output against ffuf content-discovery results.
   diff <(cat burp_sitemap.txt | sort) <(cat ffuf_hits.txt | sort)
   ```
5. `## Interpret results` — crawl gaps: routes that require form submission, file upload, or multi-step state may not appear without explicitly walking them; you still have to think about what you haven't touched. "Complete enough" is the exit criterion for Phase 2 per `methodology-phases` — the sitemap densely covers every in-scope host, including XHR endpoints seen via `browser_network_log`.
6. `## Finding writeup` — typically feeds the `testing-*` phase. If the crawl surfaces an unintended area (admin UI reachable unauthenticated, pre-production environment mistakenly linked from prod), write up per `methodology-evidence-capture` with the exact `browser_navigate` + `burp_sitemap` sequence that demonstrated the exposure.
7. `## References` — OWASP WSTG WSTG-INFO-07 (Map Execution Paths — `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/07-Map_Execution_Paths_Through_Application`), Burp Suite sitemap documentation (`https://portswigger.net/burp/documentation/desktop/tools/target/site-map`).
8. `## Authorization note` — standard paragraph verbatim.

**Length target:** ≤ 260 lines.

- [ ] **Step 2: Verify frontmatter + section count + length**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/recon-sitemap-crawl/SKILL.md
grep -c '^## ' .claude/skills/recon-sitemap-crawl/SKILL.md
wc -l .claude/skills/recon-sitemap-crawl/SKILL.md
```
Expected: frontmatter block; section count = 8; line count ≤ 260.

- [ ] **Step 3: Verify description length**

```bash
d=$(grep -m1 '^description:' .claude/skills/recon-sitemap-crawl/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
```
Expected: ≤ 180.

- [ ] **Step 4: Verify authorization paragraph present verbatim**

```bash
grep -q "Only use against systems you are authorized to test" .claude/skills/recon-sitemap-crawl/SKILL.md && echo OK || echo MISSING
```
Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/recon-sitemap-crawl/SKILL.md
git commit -m "feat(skills): recon-sitemap-crawl (browser crawl + Burp sitemap consolidation)"
```

---

### Task 11: Final verification (one follow-up commit if issues found)

- [ ] **Step 1: Confirm all ten files tracked**

```bash
cd /home/kali/Web-MCP
git ls-files \
  .claude/skills/methodology-scoping/SKILL.md \
  .claude/skills/methodology-rules-of-engagement/SKILL.md \
  .claude/skills/methodology-phases/SKILL.md \
  .claude/skills/methodology-evidence-capture/SKILL.md \
  .claude/skills/recon-subdomain-enum/SKILL.md \
  .claude/skills/recon-tech-fingerprinting/SKILL.md \
  .claude/skills/recon-content-discovery/SKILL.md \
  .claude/skills/recon-js-analysis/SKILL.md \
  .claude/skills/recon-api-enum/SKILL.md \
  .claude/skills/recon-sitemap-crawl/SKILL.md
```
Expected: all ten paths appear.

- [ ] **Step 2: Name-vs-directory consistency check**

```bash
cd /home/kali/Web-MCP
for d in \
  .claude/skills/methodology-scoping \
  .claude/skills/methodology-rules-of-engagement \
  .claude/skills/methodology-phases \
  .claude/skills/methodology-evidence-capture \
  .claude/skills/recon-subdomain-enum \
  .claude/skills/recon-tech-fingerprinting \
  .claude/skills/recon-content-discovery \
  .claude/skills/recon-js-analysis \
  .claude/skills/recon-api-enum \
  .claude/skills/recon-sitemap-crawl; do
  dirname=$(basename "$d")
  name=$(grep -m1 '^name:' "$d/SKILL.md" | awk '{print $2}')
  if [ "$dirname" = "$name" ]; then echo "OK: $dirname"; else echo "MISMATCH: $dirname vs $name"; fi
done
```
Expected: ten `OK:` lines.

- [ ] **Step 3: Description length check**

```bash
cd /home/kali/Web-MCP
for f in \
  .claude/skills/methodology-scoping/SKILL.md \
  .claude/skills/methodology-rules-of-engagement/SKILL.md \
  .claude/skills/methodology-phases/SKILL.md \
  .claude/skills/methodology-evidence-capture/SKILL.md \
  .claude/skills/recon-subdomain-enum/SKILL.md \
  .claude/skills/recon-tech-fingerprinting/SKILL.md \
  .claude/skills/recon-content-discovery/SKILL.md \
  .claude/skills/recon-js-analysis/SKILL.md \
  .claude/skills/recon-api-enum/SKILL.md \
  .claude/skills/recon-sitemap-crawl/SKILL.md; do
  d=$(grep -m1 '^description:' "$f" | sed 's/^description:[[:space:]]*//')
  echo "${#d} chars: $f"
done
```
Expected: all ten ≤ 180.

- [ ] **Step 4: Section count check**

```bash
cd /home/kali/Web-MCP
for f in \
  .claude/skills/methodology-scoping/SKILL.md \
  .claude/skills/methodology-rules-of-engagement/SKILL.md \
  .claude/skills/methodology-phases/SKILL.md \
  .claude/skills/methodology-evidence-capture/SKILL.md \
  .claude/skills/recon-subdomain-enum/SKILL.md \
  .claude/skills/recon-tech-fingerprinting/SKILL.md \
  .claude/skills/recon-content-discovery/SKILL.md \
  .claude/skills/recon-js-analysis/SKILL.md \
  .claude/skills/recon-api-enum/SKILL.md \
  .claude/skills/recon-sitemap-crawl/SKILL.md; do
  c=$(grep -c '^## ' "$f")
  echo "$c sections: $f"
done
```
Expected: all ten = 8.

- [ ] **Step 5: Authorization paragraph presence — only for recon-* skills (methodology skills intentionally vary)**

```bash
cd /home/kali/Web-MCP
for f in \
  .claude/skills/recon-subdomain-enum/SKILL.md \
  .claude/skills/recon-tech-fingerprinting/SKILL.md \
  .claude/skills/recon-content-discovery/SKILL.md \
  .claude/skills/recon-js-analysis/SKILL.md \
  .claude/skills/recon-api-enum/SKILL.md \
  .claude/skills/recon-sitemap-crawl/SKILL.md; do
  if grep -q "Only use against systems you are authorized to test" "$f"; then echo "OK: $f"; else echo "MISSING: $f"; fi
done
```
Expected: six `OK:` lines.

- [ ] **Step 6: Methodology authorization-note variants**

```bash
cd /home/kali/Web-MCP
# Scoping and RoE must treat authorization substantively (paragraph, not one-line comment)
for f in \
  .claude/skills/methodology-scoping/SKILL.md \
  .claude/skills/methodology-rules-of-engagement/SKILL.md; do
  awk '/^## Authorization note/,/^## |^$/' "$f" | wc -l | awk -v f="$f" '{ if ($1 > 3) print "OK (substantive): " f; else print "THIN: " f }'
done
# Phases and evidence-capture must have the one-line HTML-comment omission marker
for f in \
  .claude/skills/methodology-phases/SKILL.md \
  .claude/skills/methodology-evidence-capture/SKILL.md; do
  if grep -q '^<!-- Methodology skill — does not itself perform actions against a target' "$f"; then echo "OK (omitted): $f"; else echo "MISSING OMISSION: $f"; fi
done
```
Expected: two `OK (substantive):` lines; two `OK (omitted):` lines.

- [ ] **Step 7: Cross-references use names only (no paths)**

```bash
cd /home/kali/Web-MCP
# Look for any .claude/skills/ path inside the new skills; should be none (cross-refs are name-only)
grep -rn "\.claude/skills/" .claude/skills/methodology-*/SKILL.md .claude/skills/recon-*/SKILL.md || echo "OK: no path-form cross-references"
```
Expected: `OK: no path-form cross-references`.

- [ ] **Step 8: If any check above fails, fix inline and make one follow-up commit**

```bash
git commit -am "fix(skills): methodology/recon — corrections from final verification"
```

---

## Plan-end verification

- [ ] Ten feature commits on top of the spec commit, in this order: `methodology-scoping`, `methodology-rules-of-engagement`, `methodology-phases`, `methodology-evidence-capture`, `recon-subdomain-enum`, `recon-tech-fingerprinting`, `recon-content-discovery`, `recon-js-analysis`, `recon-api-enum`, `recon-sitemap-crawl`.
- [ ] All seven Task-11 structural checks pass.
- [ ] Each skill references the required prerequisite skills by name in `## When to use`.
- [ ] Each recon-* skill's `## Tool commands` contains both a shell block and an MCP block (hybrid style).
- [ ] Cross-references use skill names only, no paths.
- [ ] No forward references to unwritten sub-project-4 or sub-project-5 skills by specific name (only `testing-*` / `reporting-*` category references allowed).
