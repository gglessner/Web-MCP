---
name: _template
description: "[TEMPLATE] Skeleton for new skills. Copy this directory, rename it, and fill in the sections. Claude's matcher skips this entry because the description starts with [TEMPLATE]."
---

# Skill title

Replace this heading with a human-readable title. The title is informational
only — Claude selects this skill via `name` and `description` in the
frontmatter above.

## When to use

One paragraph describing the situations where this skill applies. State any
prerequisite skills or MCP servers here:

> Prerequisite skills: `mcp-browser`.

Example for an attack-technique skill:

> Use when testing HTTP responses that reflect user-supplied input into HTML
> without encoding. Effective against both server-reflected (GET / POST echo)
> and stored sinks. Prerequisite skills: `mcp-browser`, `mcp-burp`.

## Signal to look for

Observable conditions that indicate this technique is relevant. Keep bullets
short and concrete. Example:

- Input parameter value appears verbatim in the response body.
- Response `Content-Type` is `text/html` (or missing, treated as HTML).
- No evidence of HTML-encoding on the reflection path (`<` stays as `<`,
  not `&lt;`).

## Test steps

Numbered manual procedure. One action per step. For MCP skills, steps read as
`Call tool_name(arg=value)`. Example:

1. Identify a reflected parameter via `burp_proxy_history` filtering on
   `contains=<marker>`.
2. `browser_navigate(url=<target-with-payload>)` where the payload is
   `"><svg onload=alert(1)>`.
3. `browser_eval("document.body.innerText.includes('marker')")` to confirm
   reflection reached the DOM.
4. `browser_snapshot()` and inspect whether the payload is within an HTML tag
   or an attribute.

## Tool commands

Copy-pasteable commands. Include expected output shape or success criteria per
command. Mix shell commands and MCP tool calls as appropriate. Example:

```
# via browser-mcp
browser_navigate(url="https://target.example.com/search?q=%22%3E%3Csvg%20onload%3Dalert(1)%3E")
# Success: browser_eval below returns true
browser_eval(expression="!!document.querySelector('svg[onload]')")

# via burp-mcp
burp_proxy_history(contains="svg onload", limit=5)
# Success: at least one entry where request.url contains the payload
```

## Interpret results

How to tell success from failure. Name specific error envelopes from the MCP
tools and what each means. Call out false positives. Example:

- `browser_eval` returns `true` → payload rendered as an element, XSS confirmed.
- `browser_eval` returns `false` → payload was encoded or inside a text node.
  Examine `browser_snapshot()` DOM to see the literal reflection.
- `TARGET_NOT_ATTACHED` from any `browser_*` tool → call `browser_launch` first.
- False positive: the payload reflected but the page has a strict CSP that
  blocks execution. Check `burp_proxy_history` for a `Content-Security-Policy`
  response header; note it in the writeup.

## Finding writeup

Fixed shape — Reporting skills aggregate across skills using this section.

- **Title pattern:** `<Issue> in <parameter> on <endpoint>`
- **Severity guidance:** how to map observed impact to the project's severity
  rubric. Reference `reporting-severity-rubric`.
- **Description template:** a 3-5 sentence paragraph template describing the
  finding, the affected parameter, and user impact.
- **Reproduction steps:** numbered, complete, copy-pasteable. Each step names
  the MCP tool call or shell command and the observed outcome.
- **Suggested fix:** one paragraph, specific to the issue class. Link to the
  relevant CWE and OWASP remediation cheat sheet.

## References

External links only. Do not copy OWASP content verbatim.

- OWASP WSTG (Web Security Testing Guide) section for this technique
- PortSwigger Web Security Academy labs for this class
- Relevant CWE entry

## Authorization note

Only use against systems you are authorized to test. This skill assumes the
user has obtained written authorization. If authorization is uncertain, stop
and confirm scope before proceeding.
