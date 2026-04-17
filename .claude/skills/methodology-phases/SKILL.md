---
name: methodology-phases
description: Sequence a web pentest across five phases (scope, recon, discovery, exploit, report) — guides which methodology, recon, testing, or reporting skill to reach for next.
---

# Web Pentest Engagement Phases

## When to use

Use this skill at engagement start to plan the overall sequence of work. Return
to it mid-engagement to decide whether enough recon has been done before moving
to active exploitation. Consult it again when a finding has been confirmed but
no write-up exists yet, to determine whether to continue testing or transition
to the report phase.

## Signal to look for

- The user asks "what should I do next?" without a specific step in mind.
- Claude has just produced a recon artifact and must decide whether to move to
  active testing or continue surface enumeration.
- A finding has been confirmed and reproduced, but no write-up or evidence
  capture has occurred yet.

## Test steps

Work through the phases in order. Each phase has an entry condition, the skills
to reach for, and exit criteria that must be met before advancing.

**Phase 1: Scope & Rules of Engagement.**
Enter: engagement kickoff.
Skills: `methodology-scoping`, `methodology-rules-of-engagement`.
Exit criteria: signed-off scope and RoE artifact exists.

**Phase 2: Recon.**
Enter: Phase 1 exit met.
Skills (in rough order of use): `recon-subdomain-enum`,
`recon-tech-fingerprinting`, `recon-content-discovery`, `recon-js-analysis`,
`recon-api-enum`, `recon-sitemap-crawl`.
Exit criteria: attack-surface inventory exists; `burp_sitemap` returns a
populated list for every in-scope host.

**Phase 3: Discovery.**
Enter: Phase 2 exit met.
Skills: the `testing-*` category (future sub-project 4).
Exit criteria: at least one reproducible positive or negative result for each
attack class the tester decides to cover.

**Phase 4: Exploit.**
Enter: Phase 3 produces a positive.
Skills: relevant `testing-*` skill + `methodology-evidence-capture` for every
confirmed issue.
Exit criteria: reproducible PoC + captured evidence for every finding.

**Phase 5: Report.**
Enter: exploitation phase concluded or testing window closed.
Skills: the `reporting-*` category (future sub-project 5) +
`methodology-evidence-capture` consumed by that category.
Exit criteria: deliverable produced + findings handed off.

## Tool commands

This skill is orchestrative — it does not issue tool calls of its own. The one
concrete checkpoint to confirm Phase 2 is complete is the recon-complete check:

```
burp_sitemap(prefix="https://target.example.com", limit=500)
```

If the returned list is densely populated across all in-scope hosts (varied
paths, parameters, and content types visible), Phase 2 exit criteria are met
and Phase 3 may begin. If the list is sparse or covers only the root, return
to `recon-content-discovery` or `recon-subdomain-enum` before advancing.

## Interpret results

**Phase 1** produces paperwork: a written scope record and a signed-off RoE confirmation.
**Phase 2** produces an inventory: a populated attack-surface map covering subdomains, technologies, endpoints, and JS-exposed API routes.
**Phase 3** produces decisions: for each attack class the tester plans to cover, at least one positive or negative result is confirmed.
**Phase 4** produces findings with evidence: each issue has a reproducible proof of concept and captured evidence.
**Phase 5** produces a deliverable: a report with findings handed off to the sponsor.

## Finding writeup

<!-- Methodology skill — does not itself produce findings. -->

## References

- PTES Execution Standard: http://www.pentest-standard.org/
- OWASP WSTG Framework:
  https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/

## Authorization note

<!-- Methodology skill — does not itself perform actions against a target; authorization is handled in methodology-scoping and methodology-rules-of-engagement. -->
