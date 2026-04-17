---
name: reporting-deliverable-report
description: Assemble the final pentest deliverable — engagement overview, scope, methodology, findings summary, detailed findings, appendices — from captured findings.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `methodology-phases`, `reporting-finding-writeup`.

Use this skill at the end of the engagement when scoped testing is complete and every confirmed finding has been written per `reporting-finding-writeup`.

## Signal to look for

- All findings have been drafted and reviewed.
- Client is expecting the deliverable by an agreed deadline.
- Executive summary must be written after this skill completes (see `reporting-executive-summary`).

## Test steps

1. Assemble cover and metadata: client name, engagement dates, tester name, and scope reference.
2. Recap scope and RoE from `methodology-scoping` and `methodology-rules-of-engagement`.
3. Recap methodology from `methodology-phases` — phases walked and tools/MCPs used (`mcp-burp`, `mcp-browser`, `mcp-parley`, `mcp-github` as applicable).
4. Build a findings-at-a-glance table sorted by severity (Critical → Informational).
5. Insert each `reporting-finding-writeup` output in full under "Detailed findings".
6. Add appendices: tooling inventory, engagement timeline, and supporting evidence index.
7. Reserve a top placeholder for the executive summary.
8. Review for consistency in severity language with `reporting-severity-rubric`.

## Tool commands

Top-level report skeleton:

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

Findings-summary table skeleton:

```
| ID     | Title                                          | Severity | Status   |
|--------|------------------------------------------------|----------|----------|
| F-001  | SQL Injection in /api/users/search (q param)   | Critical | Reported |
| F-002  | IDOR at /api/orders/<id>                       | High     | Reported |
| F-003  | Reflected XSS in /search?term=                 | Medium   | Reported |
```

Sample populated report stub (sections 1-7 with Detailed Findings linking out by ID):

```
 # Acme Corp — Web Application Penetration Test Report

 **Engagement dates:** 2026-04-01 to 2026-04-14
 **Tester(s):** G. Glessner
 **Scope reference:** ACME-PENTEST-2026-Q2

 ## 1. Executive Summary
 [Placeholder — to be completed via reporting-executive-summary.]

 ## 2. Engagement Overview
 Acme Corp commissioned a black-box web application penetration test of their
 customer-facing API platform to assess risk ahead of a planned public launch.

 ## 3. Scope and Rules of Engagement
 In-scope: api.acme.com (production read-only clone), authenticated and
 unauthenticated endpoints. Out-of-scope: internal admin panel, third-party
 SSO provider. Testing window: 09:00–18:00 ET, no DoS activity.

 ## 4. Methodology
 Phases: Reconnaissance, Mapping, Authentication Testing, Authorization Testing,
 Input Validation, Reporting. Tools: mcp-burp (proxy + scanner), mcp-browser
 (DOM recon), mcp-github (source review).

 ## 5. Findings Summary
 | ID    | Title                                        | Severity | Status   |
 |-------|----------------------------------------------|----------|----------|
 | F-001 | SQL Injection in /api/users/search (q param) | Critical | Reported |
 | F-002 | IDOR at /api/orders/<id>                     | High     | Reported |
 | F-003 | Reflected XSS in /search?term=               | Medium   | Reported |

 ## 6. Detailed Findings
 See per-finding writeups: F-001, F-002, F-003
 (Each writeup produced via reporting-finding-writeup and attached in full.)

 ## 7. Appendices
 ### A. Tooling Inventory
 Burp Suite Pro 2025.x, mcp-burp, mcp-browser, mcp-github, mcp-parley

 ### B. Engagement Timeline
 2026-04-01: Kickoff. 2026-04-07: Mid-point sync. 2026-04-14: Final debrief.

 ### C. Evidence Index
 Screenshots and request/response logs stored in /evidence/ per finding ID.
```

## Interpret results

"Ready for internal review" means all findings appear in both the summary table and the detailed sections, the scope/RoE/methodology recaps match the actual engagement artifacts, and the executive summary placeholder is marked.

"Ready for client" means the report has been peer-reviewed, any sensitive internal references have been redacted, and the executive summary has been written via `reporting-executive-summary`.

## Finding writeup

<!-- Reporting skill — this skill defines finding writeup conventions; it does not itself produce a finding. -->

## References

- PTES Reporting Standard: http://www.pentest-standard.org/index.php/Reporting
- OWASP WSTG Reporting: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/
- SANS reading room: https://www.sans.org/white-papers/

## Authorization note

<!-- Reporting skill — does not itself perform actions against a target; authorization is handled in methodology-scoping and methodology-rules-of-engagement. -->
