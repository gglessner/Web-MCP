---
name: methodology-rules-of-engagement
description: Operational limits for an authorised web pentest — testing windows, rate limits, destructive-action ban, escalation path, safe-shutdown — consulted before any invasive probe.
---

# Rules of Engagement for a Web Application Penetration Test

## When to use

Prerequisite skills: `methodology-scoping`.

Consult this skill before active testing begins to confirm that all operational
limits have been signed off in writing. Return to it whenever a probe causes a
service anomaly and you need to decide whether to continue or pause, when a
finding's proof-of-concept would require a destructive demonstration, or when
the agreed testing window is about to close and you must confirm whether to
stop, extend, or hand off.

## Signal to look for

- You are about to launch an automated scan or brute force and have
  not yet confirmed the allowed request rate.
- You are about to demonstrate impact through an account takeover, privilege
  escalation, or data exfiltration step.
- The user asks "is it okay to do X?" — a direct signal that an RoE item may
  not be settled.
- The user reports "the site is acting weird after my last test" — a mid-test
  anomaly that may exceed the agreed disruption threshold.
- The testing window end time is approaching and no stop-or-extend procedure
  has been confirmed.

## Test steps

1. Confirm the testing window: start and end time in UTC, permitted days of the
   week, and any blackout periods (e.g., business-critical release days).
2. Confirm rate limits per host: maximum requests per second, maximum concurrent
   connections, and the agreed back-off procedure if a threshold is approached
   (e.g., halve rate, pause 60 s, notify sponsor).
3. Confirm banned actions:
   - No denial-of-service probes or resource-exhaustion attacks.
   - No destructive data actions beyond the minimum needed for a proof of
     concept: change one benign record to demonstrate write access, do not
     truncate or drop tables.
   - No lateral movement beyond the in-scope boundary defined in the scoping
     artifact.
   - No data exfiltration beyond what is necessary to demonstrate the finding
     (e.g., retrieve one row of non-PII test data to prove SQL injection;
     do not bulk-export production records).
4. Confirm the outage-escalation path: name and 24×7 phone or pager number of
   the primary sponsor contact, plus a Slack channel or email address as
   fallback for non-urgent queries.
5. Confirm the safe-shutdown procedure: the exact steps to take if your traffic
   triggers an incident response — stop tooling, notify the escalation contact
   immediately, preserve logs, and await written clearance before resuming.

## Tool commands

This skill is consultative. Before go-live, send the sponsor the following
confirmation message and retain the signed-off reply as an artifact.

```
RULES OF ENGAGEMENT CONFIRMATION — [Engagement name] — [Date UTC]

1. Testing window
   Start (UTC):              _______________
   End (UTC):                _______________
   Permitted days:           _______________
   Blackout periods:         _______________

2. Rate limits
   Max requests/sec per host: _______________
   Max concurrent connections: _______________
   Back-off procedure:        _______________

3. Banned actions (confirm each)
   [ ] No DoS or resource-exhaustion probes
   [ ] No destructive data actions beyond minimal PoC
   [ ] No lateral movement past in-scope boundary
   [ ] No bulk data exfiltration

4. Escalation contact (24×7)
   Name:       _______________
   Phone/pager: _______________
   Slack/email fallback: _______________

5. Safe-shutdown procedure
   _______________________________________________

Authorizing sponsor (name, title, date): _______________
```

Cross-reference the `methodology-evidence-capture` skill to preserve the
before-and-after state when running an invasive probe so that any anomaly can
be attributed and the system restored.

## Interpret results

**Green-light conditions** — all five checklist items are signed off in writing
by the authorizing sponsor. Testing may proceed up to the boundaries recorded.

**Pause and escalate conditions:**

- Any checklist item is missing or answered with "TBD" or equivalent.
- A mid-test anomaly (service latency spike, unexpected error rates, alert from
  the sponsor's ops team) exceeds the agreed disruption threshold.
- The testing window has ended and no written extension has been received.
- The sponsor contact is unreachable and the situation requires a judgment call
  about continuing.

When any pause-and-escalate condition is met: stop active tooling, document
the state of the test, and contact the escalation path defined in item 4 of
the checklist before resuming any probes.

## Finding writeup

<!-- Methodology skill — does not itself produce findings. -->

## References

- PTES Rules of Engagement:
  http://www.pentest-standard.org/index.php/Pre-engagement#Rules_of_Engagement
- OWASP Web Security Testing Guide:
  https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/

## Authorization note

The signed-off Rules of Engagement document is what converts otherwise-invasive
testing actions into legitimate, contracted work. The scope artifact from
`methodology-scoping` establishes *what* may be tested; the RoE confirmation
establishes *how*, *when*, and *with what constraints*. Without both documents
in hand, none of the `recon-*` or `testing-*` skills should run — the tester
has no documented permission for the specific actions those skills perform, and
proceeding exposes both the tester and the sponsor to legal and operational
risk. The RoE confirmation should be obtained from the authorizing individual
named in the scope document, must be dated, and must be retained for the
duration of the engagement and any contractually required retention period.

_If any RoE item is unconfirmed, stop and obtain confirmation in writing before proceeding._
