# Skill Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the three files that establish the skill library format for Web-MCP — `docs/skill-conventions.md`, `.claude/skills/_template/SKILL.md`, and `.claude/skills/mcp-browser/SKILL.md` — so later sub-projects can mass-produce pentest skills from a known-good pattern.

**Architecture:** Three prose markdown files under an existing Python/Kotlin repo. `.claude/skills/` is Claude Code's auto-discovery convention; `_template/` is non-executable (description starts with `[TEMPLATE]`); `mcp-browser/` is both a usable runbook for driving browser-mcp and the exemplar the template promises.

**Tech Stack:** Markdown + YAML frontmatter. No code, no tests — prose quality is enforced by the conventions doc itself and by spot-verification (`git show`, manual Claude Code session).

**Spec:** `docs/superpowers/specs/2026-04-16-skill-infrastructure-design.md`

---

### Task 1: Conventions document (`docs/skill-conventions.md`)

**Files:**
- Create: `docs/skill-conventions.md`

- [ ] **Step 1: Write the full file**

Create `/home/kali/Web-MCP/docs/skill-conventions.md` with exactly this content:

```markdown
# Skill Conventions for Web-MCP

This document defines how skills are written, named, and organized under
`.claude/skills/` in this repository. Any new skill — whether added by a human
or produced by an automated workflow — must follow these rules.

Spec reference: `docs/superpowers/specs/2026-04-16-skill-infrastructure-design.md`.

## Location

All skills live under `/home/kali/Web-MCP/.claude/skills/`. This path is
auto-discovered by Claude Code when it is launched in the repo root. Cloners of
the repository get the skills active with no additional install steps.

## Directory layout

- One directory per skill. Directory name matches the `name:` field in the
  skill's frontmatter exactly.
- Every skill directory contains at minimum a file named `SKILL.md`.
- Optional subdirectories, used only when a skill genuinely needs them:
  - `references/` — verbatim quotes from external specifications or papers.
    Prefer a short link in the `SKILL.md` over copying text.
  - `scripts/` — copy-pasteable payload files or helper scripts that would
    clutter the main body if inlined.
  - `examples/` — sample request/response pairs illustrating the technique.
- No nesting deeper than one level below the skill directory.
- `SKILL.md` stays under roughly 400 lines. Overflow moves into `references/`.

## Naming prefixes

Every skill directory name uses one of these prefixes:

| Prefix        | Purpose                                              | Example                    |
|---------------|------------------------------------------------------|----------------------------|
| `mcp-*`       | How to use a specific MCP server                     | `mcp-browser`, `mcp-burp`  |
| `methodology-*` | Process skills (scoping, phases, rules of engagement) | `methodology-scoping`   |
| `recon-*`     | Information-gathering techniques                     | `recon-subdomain-enum`     |
| `testing-*`   | Attack-technique runbooks                            | `testing-xss`              |
| `reporting-*` | Finding write-up, severity rubric, deliverables      | `reporting-severity-rubric`|
| `_template`   | Reserved name for the reference skeleton (one only)  | `_template`                |

The `_template` directory's `description:` field begins with `[TEMPLATE]` so
Claude's matcher never recommends it during real work.

## Frontmatter

Every `SKILL.md` begins with a YAML frontmatter block containing exactly two
fields:

```yaml
---
name: <skill-name-with-prefix>
description: <one line, third-person active voice, <= 180 characters>
---
```

- `name` must match the directory name exactly (e.g. directory `testing-xss/`
  → `name: testing-xss`).
- `description` is what Claude's skill matcher uses to decide relevance. Write
  it so the intended invocation keywords appear naturally (e.g. "Test for
  reflected and stored XSS in HTTP responses and DOM sinks.").
- No other frontmatter fields. The schema stays tight so existing tooling
  keeps working.

## Body sections

Every `SKILL.md` body has these H2 sections in this order. If a section
genuinely does not apply, keep the heading and write a one-line comment
explaining why — do not delete the heading, because aggregators rely on the
shape.

1. `## When to use` — one paragraph. Mentions any prerequisite skills or MCPs.
2. `## Signal to look for` — observable conditions that indicate the technique
   is relevant.
3. `## Test steps` — numbered manual procedure. One action per step. For MCP
   skills, steps are `Call tool_name(arg=value)` form.
4. `## Tool commands` — copy-pasteable commands (curl, sqlmap, ffuf, MCP tool
   calls) with expected success criteria.
5. `## Interpret results` — how to tell success from failure, what false
   positives to watch for, when to escalate.
6. `## Finding writeup` — title pattern, severity guidance, description
   template, reproduction steps, suggested fix. Consistent shape so
   `reporting-*` skills can aggregate.
7. `## References` — external links only. Do not reproduce OWASP / PortSwigger
   content verbatim.
8. `## Authorization note` — the standard paragraph (see below).

## Authorization note (standard paragraph)

Every pentest-technique skill (`recon-*`, `testing-*`) ends with this exact
paragraph:

> Only use against systems you are authorized to test. This skill assumes the
> user has obtained written authorization. If authorization is uncertain, stop
> and confirm scope before proceeding.

`methodology-*`, `mcp-*`, and `reporting-*` skills may omit this note if the
skill does not itself perform an action against a target.

## Cross-references between skills

- Refer to other skills by name in prose, not by path:
  `see the \`testing-xss\` skill`.
- Declare prerequisites explicitly in `## When to use`:
  `Prerequisite skills: mcp-browser, mcp-burp.`
- Paths can and will change when the library grows; names are stable.

## Scope boundary

Skills focus on authorized testing. They do not contain detection-evasion
techniques whose only purpose is malicious use. When a technique has both
legitimate testing applications and abuse potential (e.g. phishing payload
generation), the skill states the legitimate use case up front and keeps the
content proportional to it.

## Quality bar for committing a new skill

Before committing:

- [ ] Directory name matches `name:` frontmatter.
- [ ] `description:` is under 180 characters.
- [ ] All template sections are present and filled (or explicitly omitted with
      a one-line comment).
- [ ] At least one concrete MCP tool call or shell command appears in
      `## Tool commands`.
- [ ] Authorization note is present verbatim (for `recon-*`/`testing-*` skills).
- [ ] All external links in `## References` resolve (spot-check).
- [ ] `SKILL.md` is under ~400 lines.

## Out of scope (not enforced here)

- No automated skill loader or validator script. Quality is author-enforced
  via the checklist above.
- No automated external-link checker. Stale-link audits are a future ops task.
- No plugin packaging. The same files can later be referenced from a plugin
  manifest without moving them.
```

- [ ] **Step 2: Verify file length is reasonable**

Run:
```bash
wc -l /home/kali/Web-MCP/docs/skill-conventions.md
```
Expected: roughly 100-150 lines.

- [ ] **Step 3: Commit**

```bash
cd /home/kali/Web-MCP
git add docs/skill-conventions.md
git commit -m "docs: skill conventions (naming, frontmatter, layout, quality bar)"
```

---

### Task 2: Reference template (`.claude/skills/_template/SKILL.md`)

**Files:**
- Create: `.claude/skills/_template/SKILL.md`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p /home/kali/Web-MCP/.claude/skills/_template
```

- [ ] **Step 2: Write the template file**

Create `/home/kali/Web-MCP/.claude/skills/_template/SKILL.md` with exactly this content:

```markdown
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
```

- [ ] **Step 3: Verify frontmatter**

Run:
```bash
head -4 /home/kali/Web-MCP/.claude/skills/_template/SKILL.md
```
Expected output:
```
---
name: _template
description: "[TEMPLATE] Skeleton for new skills. Copy this directory, rename it, and fill in the sections. Claude's matcher skips this entry because the description starts with [TEMPLATE]."
---
```

- [ ] **Step 4: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/_template/SKILL.md
git commit -m "feat(skills): reference template with all required sections"
```

---

### Task 3: Worked example (`.claude/skills/mcp-browser/SKILL.md`)

**Files:**
- Create: `.claude/skills/mcp-browser/SKILL.md`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p /home/kali/Web-MCP/.claude/skills/mcp-browser
```

- [ ] **Step 2: Write the skill file**

Create `/home/kali/Web-MCP/.claude/skills/mcp-browser/SKILL.md` with exactly this content:

```markdown
---
name: mcp-browser
description: Drive a real Chrome browser via the browser-mcp MCP server for reconnaissance, manual interaction, DOM inspection, and JS execution during web application penetration testing.
---

# Using browser-mcp for web pentest interactions

## When to use

When a test step requires a real browser: multi-step authentication flows,
DOM-level inspection after client-side rendering, confirming JavaScript-level
behavior (DOM XSS, postMessage, SameSite cookie effects), or capturing
screenshots as evidence. `curl` is fine for simple request/response checks;
come here when the page relies on JS or when you need to observe the rendered
state.

Prerequisite: the `browser-mcp` server is registered in Claude Code (see
`README.md` in the Web-MCP repo root).

## Signal to look for

- Target is a single-page app: `curl <target>` returns a stub HTML shell with
  JS bundle references and almost no content.
- Authentication is a multi-step flow (SSO redirect, CAPTCHA, WebAuthn).
- The suspected bug requires client-side JS to execute: DOM XSS, postMessage,
  location-based redirects, local/session storage handling.
- Evidence must include a screenshot of the rendered page.

## Test steps

1. `browser_launch(headless=true, proxy="127.0.0.1:8080")` — routes traffic
   through Burp for recording. Omit the `proxy` argument to test without
   interception.
2. `browser_navigate(url="<target-url>")` — waits for the `Page.loadEventFired`
   event (default 30 s timeout).
3. `browser_snapshot()` — returns the full DOM plus the accessibility tree.
   Use for high-level structure.
4. Interact with the page as needed:
   - `browser_query(selector="<css-selector>")` — returns `outerHTML` of the
     first match.
   - `browser_click(selector="<css-selector>")` — dispatches a real mouse
     event at the element's centroid.
   - `browser_fill(selector="<css-selector>", text="<value>")` — focuses and
     types into an input.
5. `browser_eval(expression="<javascript>")` — returns the value or the
   exception text. Use for concrete proof of client-side behavior.
6. `browser_network_log(since_seq=<N>)` — returns CDP `Network.*` events
   accumulated since sequence `N` (use `0` on first call).
7. `browser_cookies(urls=["<origin>"])` / `browser_set_cookie(...)` — inspect
   or modify cookies for the active session.
8. `browser_screenshot(full_page=true)` — capture evidence as base64 PNG.
9. `browser_close()` — terminate the Chrome subprocess. Idempotent.

## Tool commands

Concrete examples — replace angle-bracketed placeholders with real values.

```
# 1. Start Chrome routed through Burp for recording
browser_launch(headless=true, proxy="127.0.0.1:8080")
# Success: {"ok": true, "data": {"chrome_binary": "...", "cdp_url": "..."}}

# 2. Navigate to the target
browser_navigate(url="https://target.example.com/login")
# Success: {"ok": true, "data": {"url": "..."}}
# Failure: {"ok": false, "error": {"code": "TIMEOUT", ...}} — proxy or target unreachable

# 3. Inspect the rendered DOM
browser_snapshot()
# Success: {"ok": true, "data": {"dom": {...}, "accessibility": {...}}}

# 4. Grab a specific element
browser_query(selector="form#login")
# Success: {"ok": true, "data": {"html": "<form id=\"login\">...</form>", "nodeId": 42}}

# 5. Fill + submit a form
browser_fill(selector="input[name=user]", text="tester")
browser_fill(selector="input[name=pass]", text="hunter2")
browser_click(selector="button[type=submit]")
browser_navigate(url="https://target.example.com/home")  # wait for navigation

# 6. Confirm JS-level behavior (DOM XSS probe)
browser_eval(expression="!!document.querySelector('svg[onload]')")
# Success: {"ok": true, "data": {"value": true, "type": "boolean", "exception": null}}

# 7. Review requests that happened during the flow
browser_network_log(since_seq=0)
# Success: {"ok": true, "data": {"events": [...], "next_seq": 27}}

# 8. Capture evidence
browser_screenshot(full_page=true)
# Success: {"ok": true, "data": {"format": "png", "base64": "iVBORw0K..."}}

# 9. Clean up
browser_close()
# Success: {"ok": true, "data": {"closed": true}}
```

## Interpret results

Every browser-mcp tool returns either `{"ok": true, "data": {...}}` or
`{"ok": false, "error": {"code": "...", "message": "...", "detail": {...}}}`.

Error codes you will actually see:

- `TARGET_NOT_ATTACHED` — `browser_launch` was never called, or Chrome died.
  Call `browser_launch` and retry.
- `TIMEOUT` (on navigate) — target or proxy unreachable, or the page never
  fired `Page.loadEventFired` within the timeout. Confirm target is reachable
  (`curl <target>`), confirm Burp is listening on the configured proxy port.
- `BAD_INPUT` (on query/click/fill) — the selector matched nothing. Re-run
  `browser_snapshot()` to find the right selector.
- `INTERNAL` — unexpected failure. Inspect `logs/browser-mcp.log` for the
  stack trace.

False positives to watch for:

- JS that runs but is blocked by a strict CSP: the payload reflected, the DOM
  looks vulnerable, but execution is prevented. Check the response's
  `Content-Security-Policy` header via `burp_proxy_history` and call it out in
  the finding.
- Elements present in the DOM but hidden via CSS. `browser_click` still
  succeeds — but a real user could not reach them. Note the hidden-state in
  the writeup.

## Finding writeup

- **Title pattern:** `<Issue> in <component> (client-side)` — e.g. "DOM-based
  XSS in `#search` query parameter (client-side)".
- **Severity guidance:** If the confirmed impact is arbitrary JS execution in
  the authenticated origin, use High or Critical per `reporting-severity-rubric`.
  If the trigger requires unusual user interaction (hover plus click in a
  specific order), drop one severity level and note the interaction cost.
- **Description template:** *"The `<parameter>` value is rendered into the DOM
  at `<location>` without encoding, allowing an attacker who controls
  `<parameter>` to execute JavaScript in the context of `<origin>`. Impact:
  session hijacking, UI redress, and access to any data visible to the
  authenticated user."*
- **Reproduction steps:** the numbered `browser_*` calls that produced the
  evidence, verbatim. Reviewers must be able to paste them into another
  Claude session and reproduce.
- **Suggested fix:** context-aware output encoding at the rendering site, plus
  a Content-Security-Policy as defense in depth. Link to CWE-79 and the OWASP
  XSS Prevention Cheat Sheet.

## References

- browser-mcp README: `MCPs/browser-mcp/README.md`
- Chrome DevTools Protocol: https://chromedevtools.github.io/devtools-protocol/
- OWASP Web Security Testing Guide — Client-side Testing:
  https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/

## Authorization note

Only use against systems you are authorized to test. This skill assumes the
user has obtained written authorization. If authorization is uncertain, stop
and confirm scope before proceeding.
```

- [ ] **Step 3: Verify structure matches conventions**

Run:
```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/mcp-browser/SKILL.md
grep -c '^## ' .claude/skills/mcp-browser/SKILL.md
wc -l .claude/skills/mcp-browser/SKILL.md
```
Expected:
- Frontmatter opens with `---`, `name: mcp-browser`, description under 180 chars, closes with `---`.
- Grep count is 8 (eight H2 sections as required by the template).
- Line count well under 400.

- [ ] **Step 4: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/mcp-browser/SKILL.md
git commit -m "feat(skills): mcp-browser runbook (first worked example)"
```

---

### Task 4: Smoke test and final verification

**Files:** None created; verification only.

- [ ] **Step 1: Confirm all three files exist and are tracked by git**

Run:
```bash
cd /home/kali/Web-MCP
git ls-files docs/skill-conventions.md .claude/skills/_template/SKILL.md .claude/skills/mcp-browser/SKILL.md
```
Expected: all three paths appear, one per line.

- [ ] **Step 2: Confirm frontmatter is valid for both skills**

Run:
```bash
cd /home/kali/Web-MCP
for f in .claude/skills/_template/SKILL.md .claude/skills/mcp-browser/SKILL.md; do
  echo "=== $f ==="
  head -4 "$f"
done
```
Expected: each file opens with `---` on line 1, `name:` on line 2, `description:` on line 3, `---` on line 4.

- [ ] **Step 3: Confirm `name` field matches directory name for both skills**

Run:
```bash
cd /home/kali/Web-MCP
for d in .claude/skills/_template .claude/skills/mcp-browser; do
  dirname=$(basename "$d")
  name=$(grep -m1 '^name:' "$d/SKILL.md" | awk '{print $2}')
  if [ "$dirname" = "$name" ]; then
    echo "OK: $dirname"
  else
    echo "MISMATCH: directory=$dirname name=$name"
  fi
done
```
Expected: two lines, both starting with `OK:`.

- [ ] **Step 4: Confirm the template's description starts with `[TEMPLATE]`**

Run:
```bash
grep -m1 '^description:' /home/kali/Web-MCP/.claude/skills/_template/SKILL.md
```
Expected: a line whose content (after `description:`) begins with `"[TEMPLATE]` or `[TEMPLATE]`.

- [ ] **Step 5: Confirm descriptions are under 180 characters**

Run:
```bash
cd /home/kali/Web-MCP
for f in .claude/skills/_template/SKILL.md .claude/skills/mcp-browser/SKILL.md; do
  d=$(grep -m1 '^description:' "$f" | sed 's/^description:[[:space:]]*//')
  echo "${#d} chars: $f"
done
```
Expected: both under 180. (The `[TEMPLATE]` prefix counts; the template's description is right at the edge — it is intentionally kept under 180.)

- [ ] **Step 6: Manual smoke test (interactive, not automatable)**

Not done by the implementing subagent — this step is for the human reviewer.
Open a fresh Claude Code session in `/home/kali/Web-MCP/`. Ask a browser-pentest
question such as:

> "I want to test if a parameter reflects into the DOM on a target. What should I do?"

Claude should surface the `mcp-browser` skill as relevant. If it does not,
either the `description:` field needs a rewrite or the skill is not being
discovered — investigate before moving on to Sub-project 2.

- [ ] **Step 7: No commit (verification-only task)**

Nothing to commit; Tasks 1-3 already produced the three required commits. If a
fix is needed (e.g. description rewrite for Step 6), make it as a targeted
follow-up commit.

---

## Plan-end verification

- [ ] Three commits on top of the spec commit: `docs: skill conventions`,
      `feat(skills): reference template`, `feat(skills): mcp-browser runbook`.
- [ ] `docs/skill-conventions.md` exists and passes its own quality-bar checklist.
- [ ] `.claude/skills/_template/SKILL.md` exists; description begins with
      `[TEMPLATE]`; all eight H2 sections present.
- [ ] `.claude/skills/mcp-browser/SKILL.md` exists; all eight H2 sections
      present and filled; authorization note verbatim; at least one concrete
      MCP tool call in `## Tool commands`.
- [ ] Spec acceptance criteria (items 1-4) are satisfied; item 5 (manual smoke
      test) is for the human reviewer.
