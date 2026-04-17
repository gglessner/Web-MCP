# Reporting Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce four `reporting-*` SKILL.md files — severity-rubric, finding-writeup, deliverable-report, executive-summary — forming a chain that turns captured findings into client deliverables.

**Architecture:** Four prose markdown files at `.claude/skills/reporting-<name>/SKILL.md`. Each follows the 8-section template from sub-project 1. Two sections (`## Finding writeup`, `## Authorization note`) are HTML-comment omissions — these skills don't act on targets and don't themselves produce findings. The other six sections are substantive and contain the skill's templates and examples.

**Tech Stack:** Markdown + YAML frontmatter. No code, no automated tests. Structural checks per task and at the end.

**Spec:** `docs/superpowers/specs/2026-04-17-reporting-skills-design.md`
**Exemplars:** `.claude/skills/methodology-evidence-capture/SKILL.md`, `.claude/skills/methodology-phases/SKILL.md` (both use the HTML-comment omission pattern for Finding writeup and Authorization note).
**Conventions:** `docs/skill-conventions.md`

## Shared reference material

**HTML-comment omissions — identical on all 4 reporting-* skills:**

- `## Finding writeup`: `<!-- Reporting skill — this skill defines finding writeup conventions; it does not itself produce a finding. -->`
- `## Authorization note`: `<!-- Reporting skill — does not itself perform actions against a target; authorization is handled in methodology-scoping and methodology-rules-of-engagement. -->`

**Fixed conventions (from prior sub-projects — apply to every task):**

1. American English in body; frontmatter description may retain spec wording verbatim.
2. Skill-name globs (`testing-*`, etc.) inside backticks, never italic.
3. NO `.claude/skills/` path references in the body — reference skills by backtick-wrapped name only.
4. Prerequisite line at the top of `## When to use` on its own line: `` Prerequisite skills: `<first>`, `<second>`, ..., `<last>`. ``
5. Description ≤ 175 characters.
6. No specific `testing-*` skill named in cross-references — category-level (`testing-*`) only.
7. Both HTML-comment omissions must be byte-exact (use the strings above).

**Per-task verification (run after writing each SKILL.md):**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/<skill-name>/SKILL.md
grep -c '^## ' .claude/skills/<skill-name>/SKILL.md
wc -l .claude/skills/<skill-name>/SKILL.md
d=$(grep -m1 '^description:' .claude/skills/<skill-name>/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
grep -c '^<!-- Reporting skill' .claude/skills/<skill-name>/SKILL.md
grep -q "\.claude/skills/" .claude/skills/<skill-name>/SKILL.md && echo "PATH REF FOUND" || echo "no path refs OK"
```

Expected: frontmatter block present; section count = 8; line count ≤ 260 (rubric up to 280); description ≤ 175 chars; HTML omission comment count = 2; no path refs.

---

### Task 1: `.claude/skills/reporting-severity-rubric/SKILL.md`

**Files:**
- Create: `.claude/skills/reporting-severity-rubric/SKILL.md`

**Source material:**
- Spec "Per-skill content → reporting-severity-rubric" in `docs/superpowers/specs/2026-04-17-reporting-skills-design.md`.
- `docs/skill-conventions.md`.
- `.claude/skills/methodology-phases/SKILL.md` and `.claude/skills/methodology-evidence-capture/SKILL.md` — HTML-comment omission style exemplars.

- [ ] **Step 1: Create directory + write SKILL.md**

```bash
mkdir -p /home/kali/Web-MCP/.claude/skills/reporting-severity-rubric
```

**Frontmatter (exact):**
```yaml
---
name: reporting-severity-rubric
description: CVSS 3.1 severity rubric for web pentest findings — base-score calculation, qualitative bands (Critical/High/Medium/Low), and specific-trigger examples.
---
```

**Body — 8 H2 sections:**

1. `## When to use` — opens with: `` Prerequisite skills: `methodology-scoping`, `methodology-evidence-capture`. `` Paragraph: before filing any finding with a severity tag; during report write-up when tester and reviewer disagree; when reconciling inline severity calls made in individual `testing-*` skills.
2. `## Signal to look for` — bullets: finding with ambiguous severity (e.g. authenticated IDOR on low-sensitivity data); tester/reviewer disagreement; severity tier needed for `reporting-executive-summary`.
3. `## Test steps` — numbered:
   1. Gather attack outcome + trigger conditions from the finding's evidence (per `methodology-evidence-capture`).
   2. Compute CVSS 3.1 base score by selecting AV/AC/PR/UI/S/C/I/A metric values.
   3. Read the resulting score off the qualitative band.
   4. Cross-check against the specific-trigger table (in `## Tool commands`).
   5. Record both the CVSS vector string and the qualitative band in the finding writeup (use `reporting-finding-writeup`).
4. `## Tool commands` — template blocks. (a) CVSS 3.1 vector template showing each metric and its allowed values:
   ```
   CVSS:3.1/AV:[N|A|L|P]/AC:[L|H]/PR:[N|L|H]/UI:[N|R]/S:[U|C]/C:[N|L|H]/I:[N|L|H]/A:[N|L|H]
   ```
   (b) Specific-trigger table — 8 to 10 rows mapping common web-pentest outcomes to a sample vector and qualitative band. Cover: unauth RCE, auth'd RCE, unauth data exfil, auth'd cross-user read, unauth SSRF to cloud metadata, internal service SSRF, reflected XSS (auth), stored XSS, info disclosure via stack trace, missing Secure cookie flag.
5. `## Interpret results` — qualitative bands: **Critical** 9.0-10.0, **High** 7.0-8.9, **Medium** 4.0-6.9, **Low** 0.1-3.9, **Informational** 0.0. When CVSS and business impact diverge (e.g. medium-CVSS finding leaks PII of sensitive population), prefer the higher of the two and document the reason in the finding.
6. `## Finding writeup` — HTML comment: `<!-- Reporting skill — this skill defines finding writeup conventions; it does not itself produce a finding. -->`
7. `## References` — three links:
   - FIRST CVSS 3.1 specification: `https://www.first.org/cvss/v3.1/specification-document`
   - CVSS 3.1 calculator: `https://www.first.org/cvss/calculator/3.1`
   - OWASP Risk Rating Methodology: `https://owasp.org/www-community/OWASP_Risk_Rating_Methodology`
8. `## Authorization note` — HTML comment: `<!-- Reporting skill — does not itself perform actions against a target; authorization is handled in methodology-scoping and methodology-rules-of-engagement. -->`

**Length target:** ≤ 280 lines (rubric is the longest of the 4).

- [ ] **Step 2: Verify structural checks**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/reporting-severity-rubric/SKILL.md
grep -c '^## ' .claude/skills/reporting-severity-rubric/SKILL.md
wc -l .claude/skills/reporting-severity-rubric/SKILL.md
d=$(grep -m1 '^description:' .claude/skills/reporting-severity-rubric/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
grep -c '^<!-- Reporting skill' .claude/skills/reporting-severity-rubric/SKILL.md
grep -q "\.claude/skills/" .claude/skills/reporting-severity-rubric/SKILL.md && echo "PATH REF FOUND" || echo "no path refs OK"
```

Expected: frontmatter; 8 sections; ≤ 280 lines; description ≤ 175 chars; 2 HTML omission comments; no path refs.

- [ ] **Step 3: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/reporting-severity-rubric/SKILL.md
git commit -m "feat(skills): reporting-severity-rubric (CVSS 3.1 + qualitative bands)"
```

---

### Task 2: `.claude/skills/reporting-finding-writeup/SKILL.md`

**Files:**
- Create: `.claude/skills/reporting-finding-writeup/SKILL.md`

**Source material:**
- Spec "Per-skill content → reporting-finding-writeup".
- `docs/skill-conventions.md`.
- `.claude/skills/methodology-evidence-capture/SKILL.md` — defines the evidence shape this template consumes.
- `.claude/skills/reporting-severity-rubric/SKILL.md` (Task 1 output) — referenced as a prereq.

- [ ] **Step 1: Create directory + write SKILL.md**

```bash
mkdir -p /home/kali/Web-MCP/.claude/skills/reporting-finding-writeup
```

**Frontmatter:**
```yaml
---
name: reporting-finding-writeup
description: Write a single web pentest finding — title, severity, description, impact, reproduction steps, evidence references, remediation — from captured artifacts.
---
```

**Body — 8 H2 sections:**

1. `## When to use` — opens with: `` Prerequisite skills: `methodology-scoping`, `methodology-evidence-capture`, `reporting-severity-rubric`. `` Paragraph: per confirmed finding, after evidence is captured and severity is rated.
2. `## Signal to look for` — bullets: confirmed positive from any `testing-*` skill with evidence satisfying `methodology-evidence-capture`; need to hand off a single finding for review or aggregation into `reporting-deliverable-report`.
3. `## Test steps`:
   1. Populate the canonical 7-section finding template (shown in `## Tool commands`).
   2. Apply `reporting-severity-rubric` to fix the severity (CVSS vector + qualitative band).
   3. Ensure reproduction steps are numbered MCP tool calls per `methodology-evidence-capture`.
   4. Link evidence files by relative path within the engagement directory.
   5. Redact sensitive data (real credentials, real PII) before delivery.
   6. Run a peer-review pass for language and accuracy.
4. `## Tool commands` — the canonical 7-section finding template, fully rendered:
   ```
   # [Severity] — [Title]
   
   **Severity:** [Band] ([CVSS:3.1/...])
   
   ## Description
   [1-paragraph technical summary of what is wrong and where.]
   
   ## Impact
   [1-paragraph business framing — what an attacker can do, what assets
   are at risk, what compliance implications apply.]
   
   ## Reproduction
   1. [Step 1 — MCP or shell call, copy-pasteable]
   2. [Step 2]
   ...
   
   ## Evidence
   - [request.http] — raw HTTP request
   - [response.http] — raw HTTP response
   - [screenshot.png] — rendered state after exploitation
   - [source.md] — source-code references (repo + SHA + line range)
   
   ## Remediation
   [Concrete code/config change. Not "sanitize inputs" — show the patch.]
   ```
   Plus three worked examples, one each for: **SQL Injection**, **IDOR**, **Reflected XSS**. Each worked example is 30-40 lines.
5. `## Interpret results` — the finding is "ready to ship" when every section is populated and the reproduction steps work from a fresh Claude session (third-party reproducibility per `methodology-evidence-capture`). Common pitfalls: reproduction step references a burned one-time token (re-capture); impact paragraph describes the attack instead of the business consequence.
6. `## Finding writeup` — HTML comment: `<!-- Reporting skill — this skill defines finding writeup conventions; it does not itself produce a finding. -->`
7. `## References` — two links:
   - OWASP WSTG Reporting: `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/`
   - NIST SP 800-115 §6: `https://csrc.nist.gov/pubs/sp/800/115/final`
8. `## Authorization note` — HTML comment: `<!-- Reporting skill — does not itself perform actions against a target; authorization is handled in methodology-scoping and methodology-rules-of-engagement. -->`

**Length target:** ≤ 260 lines.

- [ ] **Step 2: Verify structural checks**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/reporting-finding-writeup/SKILL.md
grep -c '^## ' .claude/skills/reporting-finding-writeup/SKILL.md
wc -l .claude/skills/reporting-finding-writeup/SKILL.md
d=$(grep -m1 '^description:' .claude/skills/reporting-finding-writeup/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
grep -c '^<!-- Reporting skill' .claude/skills/reporting-finding-writeup/SKILL.md
grep -q "\.claude/skills/" .claude/skills/reporting-finding-writeup/SKILL.md && echo "PATH REF FOUND" || echo "no path refs OK"
```
Expected: frontmatter; 8 sections; ≤ 260 lines; description ≤ 175; 2 omission comments; no path refs.

- [ ] **Step 3: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/reporting-finding-writeup/SKILL.md
git commit -m "feat(skills): reporting-finding-writeup (7-section template + 3 worked examples)"
```

---

### Task 3: `.claude/skills/reporting-deliverable-report/SKILL.md`

**Files:**
- Create: `.claude/skills/reporting-deliverable-report/SKILL.md`

**Source material:**
- Spec "Per-skill content → reporting-deliverable-report".
- `docs/skill-conventions.md`.
- `.claude/skills/methodology-scoping/SKILL.md`, `.claude/skills/methodology-rules-of-engagement/SKILL.md`, `.claude/skills/methodology-phases/SKILL.md` — referenced for scope / RoE / methodology recap shape.
- `.claude/skills/reporting-finding-writeup/SKILL.md` (Task 2 output) — provides the per-finding content.

- [ ] **Step 1: Create directory + write SKILL.md**

```bash
mkdir -p /home/kali/Web-MCP/.claude/skills/reporting-deliverable-report
```

**Frontmatter:**
```yaml
---
name: reporting-deliverable-report
description: Assemble the final pentest deliverable — engagement overview, scope, methodology, findings summary, detailed findings, appendices — from captured findings.
---
```

**Body — 8 H2 sections:**

1. `## When to use` — opens with: `` Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `methodology-phases`, `reporting-finding-writeup`. `` Paragraph: end of engagement; scoped testing is complete and every confirmed finding has been written per `reporting-finding-writeup`.
2. `## Signal to look for` — bullets: all findings drafted; client is expecting the deliverable; executive summary must be written after this (see `reporting-executive-summary`).
3. `## Test steps`:
   1. Assemble cover + metadata (client name, engagement dates, tester name, scope reference).
   2. Recap scope and RoE from `methodology-scoping` and `methodology-rules-of-engagement`.
   3. Recap methodology from `methodology-phases` (phases walked, tools used — pull from MCP servers via `mcp-burp`, `mcp-browser`, `mcp-parley`, `mcp-github` as applicable).
   4. Build a findings-at-a-glance table sorted by severity (Critical → Informational).
   5. Insert each `reporting-finding-writeup` output in full under "Detailed findings".
   6. Add appendices (tooling inventory, timeline, supporting evidence index).
   7. Reserve a top placeholder for the executive summary.
   8. Review for consistency in severity language with `reporting-severity-rubric`.
4. `## Tool commands` — the top-level report skeleton (markdown structure):
   ```
   # [Client Name] — Web Application Penetration Test Report
   
   **Engagement dates:** YYYY-MM-DD to YYYY-MM-DD
   **Tester(s):** [names]
   **Scope reference:** [path or ticket]
   
   ## 1. Executive Summary
   [Placeholder — written via reporting-executive-summary after this report is drafted.]
   
   ## 2. Engagement Overview
   [One paragraph — why the test was commissioned, top-level goals.]
   
   ## 3. Scope and Rules of Engagement
   [Recap from methodology-scoping + methodology-rules-of-engagement artifacts.]
   
   ## 4. Methodology
   [Recap from methodology-phases — phases walked, tools/MCPs used.]
   
   ## 5. Findings Summary
   [Table — columns: ID, Title, Severity, Status]
   
   ## 6. Detailed Findings
   [Per-finding sections, each produced via reporting-finding-writeup,
   sorted by severity descending.]
   
   ## 7. Appendices
   ### A. Tooling Inventory
   ### B. Engagement Timeline
   ### C. Evidence Index
   ```
   Plus a findings-summary table skeleton:
   ```
   | ID     | Title                                        | Severity | Status     |
   |--------|----------------------------------------------|----------|------------|
   | F-001  | SQL Injection in /api/users (id parameter)   | Critical | Reported   |
   | F-002  | IDOR at /api/orders/<id>                     | High     | Reported   |
   | ...    | ...                                          | ...      | ...        |
   ```
   Plus one sample populated report stub with 2-3 findings referenced (short form, not full-length finding writeups — the full text stays in their per-finding files).
5. `## Interpret results` — "ready for internal review" = all findings present in the table and detailed sections, scope/RoE/methodology recaps match the actual engagement, exec summary placeholder marked. "Ready for client" = peer-reviewed, redacted, and exec summary has been written via `reporting-executive-summary`.
6. `## Finding writeup` — HTML comment: `<!-- Reporting skill — this skill defines finding writeup conventions; it does not itself produce a finding. -->`
7. `## References` — three links:
   - PTES Reporting Standard: `http://www.pentest-standard.org/index.php/Reporting`
   - OWASP WSTG Reporting: `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/`
   - SANS reading room (penetration test reports): `https://www.sans.org/white-papers/`
8. `## Authorization note` — HTML comment: `<!-- Reporting skill — does not itself perform actions against a target; authorization is handled in methodology-scoping and methodology-rules-of-engagement. -->`

**Length target:** ≤ 260 lines.

- [ ] **Step 2: Verify structural checks**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/reporting-deliverable-report/SKILL.md
grep -c '^## ' .claude/skills/reporting-deliverable-report/SKILL.md
wc -l .claude/skills/reporting-deliverable-report/SKILL.md
d=$(grep -m1 '^description:' .claude/skills/reporting-deliverable-report/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
grep -c '^<!-- Reporting skill' .claude/skills/reporting-deliverable-report/SKILL.md
grep -q "\.claude/skills/" .claude/skills/reporting-deliverable-report/SKILL.md && echo "PATH REF FOUND" || echo "no path refs OK"
```
Expected: frontmatter; 8 sections; ≤ 260 lines; description ≤ 175; 2 omission comments; no path refs.

- [ ] **Step 3: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/reporting-deliverable-report/SKILL.md
git commit -m "feat(skills): reporting-deliverable-report (full report skeleton + summary table)"
```

---

### Task 4: `.claude/skills/reporting-executive-summary/SKILL.md`

**Files:**
- Create: `.claude/skills/reporting-executive-summary/SKILL.md`

**Source material:**
- Spec "Per-skill content → reporting-executive-summary".
- `docs/skill-conventions.md`.
- `.claude/skills/reporting-deliverable-report/SKILL.md` (Task 3 output) — provides the detailed-report content that this summary distills.

- [ ] **Step 1: Create directory + write SKILL.md**

```bash
mkdir -p /home/kali/Web-MCP/.claude/skills/reporting-executive-summary
```

**Frontmatter:**
```yaml
---
name: reporting-executive-summary
description: Write the 1-2 page executive summary for a web pentest report — risk posture, headline findings, business-impact framing, remediation priorities.
---
```

**Body — 8 H2 sections:**

1. `## When to use` — opens with: `` Prerequisite skills: `reporting-deliverable-report`. `` Paragraph: after the detailed report is drafted and findings are confirmed; last step before client delivery.
2. `## Signal to look for` — detailed report substantially complete; executive stakeholders are the primary audience for the cover summary; client requested a short-form summary for executive readout.
3. `## Test steps`:
   1. State the engagement context in one paragraph (client, dates, scope at a high level).
   2. State the overall risk posture in one sentence (e.g. "elevated risk — three critical findings").
   3. Summarise the top three findings in plain English using qualitative bands only (no CVE / CVSS / tool names).
   4. List remediation themes (not per-finding fixes).
   5. Note scope caveats or out-of-scope assets that should be tested separately.
   6. Enforce the length cap (≤ 2 pages rendered at 11pt).
4. `## Tool commands` — the five-section exec-summary template:
   ```
   ## Executive Summary
   
   ### Context
   [One paragraph — why the test was commissioned, what was in scope, dates.]
   
   ### Risk Posture
   [One sentence — overall risk level + headline count.]
   
   ### Headline Findings
   1. **[Qualitative band]** — [one-sentence plain-English description]
   2. **[Qualitative band]** — [one-sentence plain-English description]
   3. **[Qualitative band]** — [one-sentence plain-English description]
   
   ### Remediation Themes
   - [Theme 1 — e.g. "Input validation across user-facing endpoints"]
   - [Theme 2 — e.g. "Authentication and session hardening"]
   - [Theme 3 — e.g. "Access-control enforcement at API boundaries"]
   
   ### Scope Caveats
   [Any assets intentionally excluded; any coverage gaps.]
   ```
   Plus one worked example filled in (fictional client, three headline findings summarised without jargon).
   
   Plus a **banned terms** list: tool names (`sqlmap`, `Burp`, `ffuf`, etc.), CVSS vector strings, CVE identifiers. These belong in the detailed report, not the exec summary.
5. `## Interpret results` — "ready for client" = length check passes (≤ 2 pages at 11pt), no banned terms present, risk posture matches the findings-summary table in `reporting-deliverable-report`, non-technical reader would understand the implications.
6. `## Finding writeup` — HTML comment: `<!-- Reporting skill — this skill defines finding writeup conventions; it does not itself produce a finding. -->`
7. `## References` — two links:
   - PTES Executive Summary: `http://www.pentest-standard.org/index.php/Reporting#Executive_Summary`
   - NIST SP 800-115 §6: `https://csrc.nist.gov/pubs/sp/800/115/final`
8. `## Authorization note` — HTML comment: `<!-- Reporting skill — does not itself perform actions against a target; authorization is handled in methodology-scoping and methodology-rules-of-engagement. -->`

**Length target:** ≤ 260 lines.

- [ ] **Step 2: Verify structural checks**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/reporting-executive-summary/SKILL.md
grep -c '^## ' .claude/skills/reporting-executive-summary/SKILL.md
wc -l .claude/skills/reporting-executive-summary/SKILL.md
d=$(grep -m1 '^description:' .claude/skills/reporting-executive-summary/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
grep -c '^<!-- Reporting skill' .claude/skills/reporting-executive-summary/SKILL.md
grep -q "\.claude/skills/" .claude/skills/reporting-executive-summary/SKILL.md && echo "PATH REF FOUND" || echo "no path refs OK"
```
Expected: frontmatter; 8 sections; ≤ 260 lines; description ≤ 175; 2 omission comments; no path refs.

- [ ] **Step 3: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/reporting-executive-summary/SKILL.md
git commit -m "feat(skills): reporting-executive-summary (5-section template + banned-terms)"
```

---

### Task 5: Final verification

- [ ] **Step 1: Confirm all 4 files tracked**

```bash
cd /home/kali/Web-MCP
git ls-files .claude/skills/reporting-*/SKILL.md | wc -l
```
Expected: `4`.

- [ ] **Step 2: Name-vs-directory consistency**

```bash
cd /home/kali/Web-MCP
for d in .claude/skills/reporting-*; do
  dir=$(basename "$d"); name=$(grep -m1 '^name:' "$d/SKILL.md" | awk '{print $2}')
  if [ "$dir" = "$name" ]; then echo "OK: $dir"; else echo "MISMATCH: $dir vs $name"; fi
done
```
Expected: 4 `OK:` lines.

- [ ] **Step 3: Description length ≤ 175 chars**

```bash
cd /home/kali/Web-MCP
for f in .claude/skills/reporting-*/SKILL.md; do
  d=$(grep -m1 '^description:' "$f" | sed 's/^description:[[:space:]]*//')
  len=${#d}
  if [ "$len" -gt 175 ]; then echo "OVER: $f ($len chars)"; fi
done
echo "done"
```
Expected: only `done`.

- [ ] **Step 4: Section count**

```bash
cd /home/kali/Web-MCP
for f in .claude/skills/reporting-*/SKILL.md; do
  c=$(grep -c '^## ' "$f")
  if [ "$c" != "8" ]; then echo "$c sections: $f"; fi
done
echo "done"
```
Expected: only `done`.

- [ ] **Step 5: Both HTML-comment omissions present on all 4 files**

```bash
cd /home/kali/Web-MCP
expected_finding="<!-- Reporting skill — this skill defines finding writeup conventions; it does not itself produce a finding. -->"
expected_auth="<!-- Reporting skill — does not itself perform actions against a target; authorization is handled in methodology-scoping and methodology-rules-of-engagement. -->"
for f in .claude/skills/reporting-*/SKILL.md; do
  if ! grep -qF "$expected_finding" "$f"; then echo "MISSING finding-writeup comment: $f"; fi
  if ! grep -qF "$expected_auth" "$f"; then echo "MISSING authorization-note comment: $f"; fi
done
echo "done"
```
Expected: only `done`.

- [ ] **Step 6: No path-form cross-references**

```bash
cd /home/kali/Web-MCP
grep -l "\.claude/skills/" .claude/skills/reporting-*/SKILL.md 2>/dev/null || echo "OK: no path refs"
```
Expected: `OK: no path refs`.

- [ ] **Step 7: No specific testing-* skill named in reporting-* bodies**

```bash
cd /home/kali/Web-MCP
# Match any testing-<specific-name> reference that is NOT the wildcard testing-*
grep -rnE 'testing-[a-z][a-z-]*[a-z]' .claude/skills/reporting-*/SKILL.md | grep -v 'testing-\*' || echo "OK: no specific testing-* refs"
```
Expected: `OK: no specific testing-* refs`. (A reference like ``category-level testing-*`` is allowed because the `-*` suffix matches the wildcard form.)

- [ ] **Step 8: No italic-glob rendering bugs**

```bash
cd /home/kali/Web-MCP
grep -rnE '_[a-z-]+-\*_|\*[a-z-]+-\*[^*]' .claude/skills/reporting-*/SKILL.md || echo "OK: no italic-glob"
```
Expected: `OK: no italic-glob`.

- [ ] **Step 9: If any of steps 1-8 fail, fix inline and make a single follow-up commit**

```bash
cd /home/kali/Web-MCP
git add .
git commit -m "fix(skills): reporting-* — corrections from final verification"
```

---

## Plan-end verification

- [ ] Four `feat(skills):` commits on top of the spec commit, in chain order: reporting-severity-rubric → reporting-finding-writeup → reporting-deliverable-report → reporting-executive-summary.
- [ ] All 8 final structural checks (Task 5) pass, or a single follow-up commit resolves them.
- [ ] Each skill's `## When to use` opens with the correct `Prerequisite skills:` line per the chain map.
- [ ] Both HTML-comment omissions (Finding writeup + Authorization note) are byte-exact in all 4 files.
- [ ] No path-form cross-references; no specific testing-* skill names; no italic-glob rendering bugs.
