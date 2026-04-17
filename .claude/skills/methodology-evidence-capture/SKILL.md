---
name: methodology-evidence-capture
description: Reproducible evidence conventions for web pentest findings — screenshots, raw request/response, numbered MCP tool-call reproduction, source references.
---

# Evidence Capture for Web Pentest Findings

## When to use

Use this skill every time a finding is confirmed and must be documented. Return
to it before closing out a proxy session — evidence dies with the session. Apply
it immediately when a run-once runtime observation must be preserved: a dynamic
token, a one-time redirect, or any other state that cannot be recreated later.

## Signal to look for

- A probe produced a positive result that now needs a finding.
- Claude is about to move on from a reproducible runtime observation.
- A finding's reproduction depends on session state that is about to be lost.

## Test steps

1. Save the raw HTTP request via `burp_proxy_request(id=N)` — capture both the
   `request` and `response` fields.
2. Capture a rendered screenshot via `browser_screenshot(full_page=true)` —
   required if the bug has a visible UI component; optional otherwise.
3. Record the numbered MCP tool-call sequence that reproduced the bug, verbatim.
   Another operator must be able to paste the sequence into a fresh Claude
   session and reproduce the same outcome.
4. If the finding references source code, include repo + commit SHA + line range
   (e.g. `src/api/export.py#L42-L57 @ abc123`). Use `mcp-github` tools for the
   lookup if the repo is on GitHub.
5. Record timestamps in UTC for each step.

## Tool commands

- `burp_proxy_request(id=12)` — save full raw request + response.
- `browser_screenshot(full_page=true)` — save rendered screenshot as PNG
  (base64 in the response; decode and write to a file in the engagement's
  evidence directory).
- `burp_repeater_send(raw_base64=<b64>, host=..., port=443, secure=true, tab_name="repro-<finding-id>")` — parameterized reproduction.
- `get_file_contents(repo_url="https://github.com/org/name", path="src/api/export.py", ref="<sha>")` — source-side evidence.

Preferred evidence-directory layout:

```
evidence/
├── F-001-exposed-git/
│   ├── request.http
│   ├── response.http
│   ├── screenshot.png
│   └── repro.md
```

## Interpret results

**Reproducible:** a third party can re-run the numbered tool-call sequence and
see the same outcome. This is the bar every finding must meet before write-up.

**Non-reproducible:** state was lost — session cookie expired, one-time token
burned, or proxy history cleared. Re-capture before proceeding to write-up. If
re-capture is impossible, document what was observed and why it cannot be
replayed, and flag the finding as evidence-incomplete.

## Finding writeup

<!-- Methodology skill — this file defines the finding writeup shape the rest of the library consumes. -->

## References

- OWASP WSTG Reporting:
  https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/
- NIST SP 800-115 §6:
  https://csrc.nist.gov/pubs/sp/800/115/final

## Authorization note

<!-- Methodology skill — does not itself perform actions against a target; authorization is handled in methodology-scoping and methodology-rules-of-engagement. -->
