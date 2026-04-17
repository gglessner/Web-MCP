---
name: reporting-severity-rubric
description: CVSS 3.1 severity rubric for web pentest findings — base-score calculation, qualitative bands (Critical/High/Medium/Low), and specific-trigger examples.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-evidence-capture`.

Use this skill before filing any finding with a severity tag; during report write-up when tester and reviewer disagree on severity; and when reconciling inline severity calls made in individual `testing-*` skills.

## Signal to look for

- Finding with ambiguous severity (e.g. authenticated IDOR on low-sensitivity data).
- Tester/reviewer disagreement on qualitative band.
- Severity tier needed for `reporting-executive-summary`.

## Test steps

1. Gather attack outcome and trigger conditions from the finding's evidence (per `methodology-evidence-capture`).
2. Compute CVSS 3.1 base score by selecting AV/AC/PR/UI/S/C/I/A metric values.
3. Read the resulting score off the qualitative band table.
4. Cross-check against the specific-trigger table in `## Tool commands`.
5. Record both the CVSS vector string and the qualitative band in the finding writeup (use `reporting-finding-writeup`).

## Tool commands

### CVSS 3.1 vector template

```
CVSS:3.1/AV:[N|A|L|P]/AC:[L|H]/PR:[N|L|H]/UI:[N|R]/S:[U|C]/C:[N|L|H]/I:[N|L|H]/A:[N|L|H]
```

**Metric legend:**

| Abbr | Metric               | Values                                              |
|------|----------------------|-----------------------------------------------------|
| AV   | Attack Vector        | N=Network, A=Adjacent, L=Local, P=Physical          |
| AC   | Attack Complexity    | L=Low, H=High                                       |
| PR   | Privileges Required  | N=None, L=Low, H=High                               |
| UI   | User Interaction     | N=None, R=Required                                  |
| S    | Scope                | U=Unchanged, C=Changed                              |
| C    | Confidentiality      | N=None, L=Low, H=High                               |
| I    | Integrity            | N=None, L=Low, H=High                               |
| A    | Availability         | N=None, L=Low, H=High                               |

### Specific-trigger table

| Attack outcome                        | Sample CVSS vector                                        | Band     |
|---------------------------------------|-----------------------------------------------------------|----------|
| Unauthenticated RCE                   | CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H             | Critical |
| Authenticated RCE                     | CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H             | High     |
| Unauthenticated data exfiltration     | CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N             | High     |
| Authenticated cross-user data read    | CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N             | High     |
| Unauthenticated SSRF to cloud metadata| CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:L/A:N             | Critical |
| SSRF to internal service (auth'd)     | CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:L/I:L/A:N             | Medium   |
| Reflected XSS (authenticated)         | CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:L/I:L/A:N             | Medium   |
| Stored XSS                            | CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:H/I:L/A:N             | High     |
| Info disclosure via stack trace       | CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N             | Medium   |
| Missing Secure flag on session cookie | CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N             | Low      |

## Interpret results

Qualitative bands per CVSS 3.1:

| Band          | Score range |
|---------------|-------------|
| **Critical**  | 9.0 – 10.0  |
| **High**      | 7.0 – 8.9   |
| **Medium**    | 4.0 – 6.9   |
| **Low**       | 0.1 – 3.9   |
| **Informational** | 0.0     |

When CVSS and business impact diverge (e.g. a medium-CVSS finding leaks PII of a sensitive population), prefer the higher of the two and document the reason for the adjustment in the finding writeup.

## Finding writeup

<!-- Reporting skill — this skill defines finding writeup conventions; it does not itself produce a finding. -->

## References

- FIRST CVSS 3.1 specification document: <https://www.first.org/cvss/v3.1/specification-document>
- CVSS 3.1 calculator: <https://www.first.org/cvss/calculator/3.1>
- OWASP Risk Rating Methodology: <https://owasp.org/www-community/OWASP_Risk_Rating_Methodology>

## Authorization note

<!-- Reporting skill — does not itself perform actions against a target; authorization is handled in methodology-scoping and methodology-rules-of-engagement. -->
