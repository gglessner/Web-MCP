# Reporting & Deliverables Skills — Design

**Date:** 2026-04-17
**Author:** Garland Glessner (gglessner@gmail.com)
**Status:** Approved for planning
**Sub-project:** 5 of 5 (final) in the Web-MCP skill-library track

## Purpose

Produce four `reporting-*` skills that turn captured pentest findings into client-facing deliverables. They consume the evidence shape defined in `methodology-evidence-capture` and the finding data produced by every `testing-*` skill, and they close out the engagement loop (scope → RoE → recon → testing → reporting) started by sub-projects 3 and 4.

## Non-goals

- No peer `testing-*` cross-references by specific name — testing skills are referenced at the category level only.
- No pandoc/DOCX/PDF toolchain tied into the skills — they produce format-agnostic markdown templates that a tester can render with their preferred toolchain.
- No `scripts/` subdirectories for sample-report fixtures at initial write.
- No distinct reporting skills for vulnerability-management workflows (Jira import, ticket hand-off) — those belong in a future sub-project if scoped.

## Deliverables

Four files under `.claude/skills/`:

```
.claude/skills/
├── reporting-severity-rubric/SKILL.md
├── reporting-finding-writeup/SKILL.md
├── reporting-deliverable-report/SKILL.md
└── reporting-executive-summary/SKILL.md
```

**Target lengths:** 150-200 lines per skill. Rubric may run slightly longer (~220) to cover CVSS 3.1 bands plus specific-trigger examples.

**Library total after this sub-project:** 79 skills (75 existing + 4 new).

## Skill template conventions (applies to all 4)

**Frontmatter:**

```yaml
---
name: reporting-<name>
description: <one-line action phrase, ≤ 175 chars>
---
```

**Body — 8 H2 sections in canonical order.** Two sections are HTML-comment omissions on every reporting-* skill (these skills do not perform actions against a target and do not themselves produce a finding):

- `## Finding writeup`: `<!-- Reporting skill — this skill defines finding writeup conventions; it does not itself produce a finding. -->`
- `## Authorization note`: `<!-- Reporting skill — does not itself perform actions against a target; authorization is handled in methodology-scoping and methodology-rules-of-engagement. -->`

The other six sections (`## When to use`, `## Signal to look for`, `## Test steps`, `## Tool commands`, `## Interpret results`, `## References`) are substantive.

**Hard rules (from prior sub-projects):**

1. American English in body. Frontmatter description may retain spec wording.
2. Skill-name globs (`methodology-*`, `recon-*`, `testing-*`, `reporting-*`, `mcp-*`) inside backticks — never italic.
3. No path-form cross-references (e.g. never `.claude/skills/mcp-burp/SKILL.md`); reference by backtick-wrapped name only.
4. Prerequisite line at the top of `## When to use` on its own line with all skill names in backticks.
5. `## Test steps` and `## Tool commands` contain at least one concrete template block or example per skill (these are template skills — the templates are the deliverable).

## Per-skill content

### reporting-severity-rubric

- **Description:** `CVSS 3.1 severity rubric for web pentest findings — base-score calculation, qualitative bands (Critical/High/Medium/Low), and specific-trigger examples.`
- **Prereqs:** `methodology-scoping`, `methodology-evidence-capture`.
- **When to use:** before filing any finding with a severity tag; during report write-up when tester and reviewer disagree; when reconciling inline severity calls made in individual testing-* skills.
- **Signal to look for:** a finding whose severity is ambiguous (e.g. "authenticated IDOR reading low-sensitivity data"); disagreement between testers; severity tier needed for exec summary.
- **Test steps:** (1) gather attack outcome + trigger conditions from the finding's evidence; (2) compute CVSS 3.1 base score by selecting AV/AC/PR/UI/S/C/I/A metric values; (3) read the resulting score off the qualitative band; (4) cross-check against the specific-trigger table below; (5) record both the CVSS vector string and the qualitative band in the finding writeup.
- **Tool commands:** a CVSS 3.1 vector template block with every metric labeled and its allowed values listed, plus a specific-trigger table mapping common attack outcomes (unauth RCE, auth'd RCE, unauth data exfil, auth'd cross-user read, internal service SSRF, info disclosure via stack trace, etc.) to sample CVSS vectors and qualitative bands.
- **Interpret results:** qualitative bands: **Critical** 9.0-10.0, **High** 7.0-8.9, **Medium** 4.0-6.9, **Low** 0.1-3.9, **Informational** 0.0. When CVSS and business impact diverge significantly, prefer the higher of the two and document the reason in the finding.
- **References:** FIRST CVSS 3.1 specification (`https://www.first.org/cvss/v3.1/specification-document`), CVSS 3.1 calculator (`https://www.first.org/cvss/calculator/3.1`), OWASP Risk Rating Methodology (`https://owasp.org/www-community/OWASP_Risk_Rating_Methodology`).

### reporting-finding-writeup

- **Description:** `Write a single web pentest finding — title, severity, description, impact, reproduction steps, evidence references, remediation — from captured artifacts.`
- **Prereqs:** `methodology-scoping`, `methodology-evidence-capture`, `reporting-severity-rubric`.
- **When to use:** per confirmed finding, after evidence is captured and severity is rated.
- **Signal to look for:** a confirmed positive from any `testing-*` skill with evidence satisfying `methodology-evidence-capture`; need to hand off a single finding for review.
- **Test steps:** (1) populate the canonical 7-section finding template; (2) apply `reporting-severity-rubric` to fix the severity; (3) ensure reproduction steps are numbered MCP tool calls per `methodology-evidence-capture`; (4) link evidence files by relative path within the engagement directory; (5) redact sensitive data (real credentials, real PII) before delivery; (6) run a peer-review pass for language and accuracy.
- **Tool commands:** the canonical finding template, fully worked, with seven sections: **Title** (action + asset + severity band), **Severity** (CVSS vector + qualitative band), **Description** (1-paragraph technical summary), **Impact** (1-paragraph business framing), **Reproduction** (numbered MCP/shell tool calls, copy-pasteable), **Evidence** (pointers to request/response files, screenshots, source refs), **Remediation** (concrete code/config change, not just "sanitize inputs"). Plus three worked examples (SQLi, IDOR, Reflected XSS).
- **Interpret results:** the finding is "ready to ship" when every section is populated and the reproduction steps work from a fresh Claude session (third-party reproducibility).
- **References:** OWASP WSTG Reporting (`https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/`), NIST SP 800-115 §6 (`https://csrc.nist.gov/pubs/sp/800/115/final`).

### reporting-deliverable-report

- **Description:** `Assemble the final pentest deliverable — engagement overview, scope, methodology, findings summary, detailed findings, appendices — from captured findings.`
- **Prereqs:** `methodology-scoping`, `methodology-rules-of-engagement`, `methodology-phases`, `reporting-finding-writeup`.
- **When to use:** end of engagement; scoped testing is complete and every confirmed finding has been written per `reporting-finding-writeup`.
- **Signal to look for:** all findings drafted; client is expecting the deliverable; executive summary must be written after this (see `reporting-executive-summary`).
- **Test steps:** (1) assemble cover + metadata (client name, engagement dates, tester name, scope reference); (2) recap scope and RoE from `methodology-scoping` and `methodology-rules-of-engagement`; (3) recap methodology from `methodology-phases` (phases walked, tools used); (4) build a findings-at-a-glance table sorted by severity (Critical → Informational); (5) insert each `reporting-finding-writeup` output in full under "Detailed findings"; (6) add appendices (tooling inventory, timeline, supporting evidence index); (7) reserve a top placeholder for the executive summary; (8) review for consistency in severity language.
- **Tool commands:** the top-level report skeleton (numbered headings, markdown structure); a findings-summary table template with columns for ID, Title, Severity, Status; an appendices skeleton. A sample populated report with 2-3 findings stubbed in.
- **Interpret results:** "ready for internal review" = all findings present, table accurate, exec summary placeholder marked, scope/RoE/methodology recaps match the actual engagement. "Ready for client" = peer-reviewed, redacted, and the executive summary has been written via `reporting-executive-summary`.
- **References:** PTES Reporting Standard (`http://www.pentest-standard.org/index.php/Reporting`), OWASP WSTG Reporting section, SANS Sample Penetration Test Report (`https://www.sans.org/`).

### reporting-executive-summary

- **Description:** `Write the 1-2 page executive summary for a web pentest report — risk posture, headline findings, business-impact framing, remediation priorities.`
- **Prereqs:** `reporting-deliverable-report`.
- **When to use:** after the detailed report is drafted and findings are confirmed; last step before client delivery.
- **Signal to look for:** detailed report is substantially complete; executive stakeholders are the primary audience for the cover summary.
- **Test steps:** (1) state the engagement context in one paragraph (client, dates, scope at a high level); (2) state the overall risk posture in one sentence (e.g. "elevated risk — three critical findings"); (3) summarise the top three findings in plain English using qualitative bands only (no CVE/CVSS/tool names); (4) list remediation themes (not per-finding fixes); (5) note scope caveats or out-of-scope assets that should be tested separately; (6) enforce the length cap (1-2 pages rendered).
- **Tool commands:** the five-section exec-summary template (Context / Risk Posture / Headline Findings / Remediation Themes / Scope Caveats) with one worked example filled in. A "banned words" list: tool names (`sqlmap`, `Burp`, etc.), CVSS vector strings, CVE identifiers — these belong in the detailed report, not the exec summary.
- **Interpret results:** "ready for client" = length check passes (≤ 2 pages at 11pt), no banned terms present, risk posture matches the findings table in the detailed report, non-technical reader would understand the implications.
- **References:** PTES Executive Summary (`http://www.pentest-standard.org/index.php/Reporting#Executive_Summary`), NIST SP 800-115 §6, OWASP Risk Rating (for the framing of likelihood vs impact in plain English).

## Cross-reference map (chain model — Approach A)

```
reporting-severity-rubric
  prereqs: methodology-scoping, methodology-evidence-capture
  referenced by: reporting-finding-writeup

reporting-finding-writeup
  prereqs: methodology-scoping, methodology-evidence-capture, reporting-severity-rubric
  referenced by: reporting-deliverable-report

reporting-deliverable-report
  prereqs: methodology-scoping, methodology-rules-of-engagement, methodology-phases,
           reporting-finding-writeup
  referenced by: reporting-executive-summary

reporting-executive-summary
  prereqs: reporting-deliverable-report
```

**Testing-* references:** category-level only (e.g., "findings produced by `testing-*` skills"); no specific testing-* skill is named.

**No path-form cross-references anywhere.** All references use skill names in backticks.

## Authorization stance

All four reporting-* skills omit the verbatim authorization paragraph and use the HTML-comment omission shape (matching `methodology-phases` and `methodology-evidence-capture`). None of these skills performs actions against a target.

Specific omission comments:

- `## Finding writeup`: `<!-- Reporting skill — this skill defines finding writeup conventions; it does not itself produce a finding. -->`
- `## Authorization note`: `<!-- Reporting skill — does not itself perform actions against a target; authorization is handled in methodology-scoping and methodology-rules-of-engagement. -->`

## Quality bar

Per `docs/skill-conventions.md`:

- [ ] Directory name matches `name:` frontmatter.
- [ ] Frontmatter has exactly two fields; description ≤ 175 chars.
- [ ] All 8 H2 sections present in canonical order (two are HTML-comment omissions).
- [ ] At least one concrete template block or worked example in `## Test steps` or `## Tool commands` — these skills are template skills and the templates are the deliverable.
- [ ] Prerequisite line at the top of `## When to use` on its own line, all skill names backticked.
- [ ] External links in `## References` resolve.
- [ ] SKILL.md under ~400 lines; target 150-200 (rubric up to 220).

Additional sub-project 5 constraints:

- [ ] No specific `testing-*` skill named in cross-references — category-level only.
- [ ] No path-form cross-references.
- [ ] HTML-comment omissions on both `## Finding writeup` and `## Authorization note` use the exact shape specified above.

## Discoverability & testing

Claude Code auto-discovers each skill via `.claude/skills/*/SKILL.md` on session start. Manual smoke tests (one per skill, run after the full sub-project is merged):

- "How do I rate this finding's severity?" → `reporting-severity-rubric`.
- "I need to write up this SQL injection finding." → `reporting-finding-writeup`.
- "Assemble the final pentest report." → `reporting-deliverable-report`.
- "Write the 1-page executive summary." → `reporting-executive-summary`.

## Commit strategy

Four atomic `feat(skills):` commits in chain order so dependency order is clear in `git log`:

1. `feat(skills): reporting-severity-rubric`
2. `feat(skills): reporting-finding-writeup`
3. `feat(skills): reporting-deliverable-report`
4. `feat(skills): reporting-executive-summary`

Plus fix commits as needed.

## Out of scope

- Vulnerability-management integrations (Jira, ServiceNow) — future work.
- Re-testing / retest reports (distinct deliverable, distinct lifecycle).
- Client-template DOCX/PDF files — format-agnostic by design.
- Automated report-rendering toolchain.

## Acceptance criteria

1. All four SKILL.md files exist at the paths in the Deliverables section.
2. Each passes the quality-bar checklist above.
3. Cross-references follow the chain map; names only, no paths.
4. Descriptions ≤ 175 chars.
5. Spec committed to `docs/superpowers/specs/2026-04-17-reporting-skills-design.md`.
6. Four atomic feat commits in chain order.
7. Manual smoke-test prompts above each surface the intended skill when Claude Code is launched in the repo root.
