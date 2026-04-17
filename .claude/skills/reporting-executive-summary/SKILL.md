---
name: reporting-executive-summary
description: Write the 1-2 page executive summary for a web pentest report — risk posture, headline findings, business-impact framing, remediation priorities.
---

## When to use

Prerequisite skills: `reporting-deliverable-report`.

Use this skill after the detailed report is drafted and all findings are confirmed. This is the last step before client delivery — the exec summary is written once the underlying evidence is locked.

## Signal to look for

- Detailed report is substantially complete and findings have been validated.
- Executive stakeholders are the primary audience for the cover summary.
- Client requested a short-form summary for executive readout or board presentation.

## Test steps

1. State the engagement context in one paragraph (client, dates, scope at a high level).
2. State the overall risk posture in one sentence (e.g. "elevated risk — three critical findings").
3. Summarise the top three findings in plain English using qualitative bands only (no CVE / CVSS / tool names).
4. List remediation themes (not per-finding fixes).
5. Note scope caveats or out-of-scope assets that should be tested separately.
6. Enforce the length cap (≤ 2 pages rendered at 11pt).

## Tool commands

Five-section exec-summary template:

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

Worked example (fictional client):

```
 ## Executive Summary

 ### Context
 Acme Payments commissioned a black-box web application penetration test of its
 customer-facing payment portal and internal merchant dashboard during March 2026.
 Testing covered two production hostnames and the associated REST API endpoints;
 mobile applications and the corporate network were out of scope.

 ### Risk Posture
 Elevated risk — three critical findings require immediate remediation before the
 next scheduled release.

 ### Headline Findings
 1. **Critical** — Unauthenticated attackers can retrieve arbitrary customer
    payment records by manipulating a numeric identifier in the account-lookup
    endpoint.
 2. **Critical** — The merchant login form allows unlimited password-guessing
    attempts with no lockout, enabling automated credential attacks.
 3. **High** — Session tokens do not expire after logout, allowing a stolen token
    to be replayed indefinitely.

 ### Remediation Themes
 - Access-control enforcement at every data-retrieval endpoint
 - Authentication hardening (rate limiting, lockout, and token lifecycle)
 - Secure session management across the full request lifecycle

 ### Scope Caveats
 Mobile applications and the corporate VPN were excluded from this engagement.
 The internal developer portal (dev.acmepayments.internal) was identified during
 reconnaissance but was explicitly out of scope; a targeted assessment is recommended.
```

**Banned terms** — the following must not appear in the executive summary; they belong in the detailed report only: tool names such as `sqlmap`, `Burp`, `ffuf`, `dalfox`, `jwt_tool`, `nikto`, `nmap`, and similar; CVSS vector strings; CVE identifiers. Using any of these in the exec summary signals that the audience-appropriate abstraction has not been applied.

## Interpret results

A summary is ready for client delivery when all of the following hold:

- Length check passes: ≤ 2 pages at 11pt, roughly ≤ 700 words.
- No banned terms are present (tool names, CVSS vectors, CVE identifiers).
- The stated risk posture matches the findings-summary table in `reporting-deliverable-report`.
- A non-technical reader would understand the business implications without referencing the detailed report.

## Finding writeup

<!-- Reporting skill — this skill defines finding writeup conventions; it does not itself produce a finding. -->

## References

- PTES Executive Summary: http://www.pentest-standard.org/index.php/Reporting#Executive_Summary
- NIST SP 800-115 §6: https://csrc.nist.gov/pubs/sp/800/115/final

## Authorization note

<!-- Reporting skill — does not itself perform actions against a target; authorization is handled in methodology-scoping and methodology-rules-of-engagement. -->
