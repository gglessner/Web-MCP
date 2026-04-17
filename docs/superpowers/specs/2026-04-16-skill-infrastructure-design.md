# Skill Infrastructure — Design

**Date:** 2026-04-16
**Author:** Garland Glessner (gglessner@gmail.com)
**Status:** Approved for planning
**Sub-project:** 1 of 5 in the Web-MCP skill-library track

## Purpose

Establish the format, conventions, and one worked example for a library of Claude Code skills covering web application penetration testing and Web-MCP usage. Later sub-projects (MCP usage, methodology, attack techniques, reporting) build on this foundation.

## Non-goals (deferred to later sub-projects)

- All MCP usage skills except the `mcp-browser` exemplar (Sub-project 2)
- Methodology and recon skills (Sub-project 3)
- Attack technique runbooks — XSS, SQLi, IDOR, SSRF, etc. (Sub-project 4)
- Reporting / deliverable skills (Sub-project 5)
- Plugin packaging for wider distribution (may be layered on later)

## Deliverables

Three files under `/home/kali/Web-MCP/`:

```
Web-MCP/
├── .claude/
│   └── skills/
│       ├── _template/
│       │   └── SKILL.md                # reference skeleton future skills copy
│       └── mcp-browser/
│           └── SKILL.md                # first worked example (MCP-browser usage)
└── docs/
    └── skill-conventions.md            # naming, frontmatter, file layout, ethics
```

**Rationale:**

- `.claude/skills/` is Claude Code's convention — auto-discovered when Claude is launched in the repo root; a cloner gets the skills "just by opening the repo".
- `_template/` uses an underscore prefix and a `description` starting with `[TEMPLATE]` so Claude's matcher skips it — it is a reference, not an executable skill.
- `docs/skill-conventions.md` sits alongside other design docs so it is discoverable and diffable with the rest of the spec track.

## SKILL.md template

Every skill file — including `_template/SKILL.md` — has this shape:

```markdown
---
name: <skill-name-with-prefix>
description: <one-line trigger text; used by Claude to decide relevance>
---

# <Human-readable title>

## When to use
One paragraph describing the situations where this skill applies. Must mention
prerequisite skills or MCPs needed.

## Signal to look for
Observable conditions that indicate this technique is relevant.

## Test steps
Numbered manual procedure. Each step is an action, not prose. For MCP skills,
steps are `Call tool_name(arg=value)` form.

## Tool commands
Copy-pasteable commands (curl, sqlmap, ffuf, MCP tool calls). Include expected
output shape or success criteria per command.

## Interpret results
How to tell success from failure. False-positive pitfalls. When to escalate.

## Finding writeup
Title pattern, severity guidance, description template, reproduction steps,
suggested fix. Consistent shape across skills so reporting can aggregate.

## References
External links: OWASP WSTG section, PortSwigger Web Security Academy, relevant
CWE. No in-depth reproduction of public content.

## Authorization note
Standard caveat: "Only use against systems you are authorized to test. This
skill assumes the user has obtained written authorization."
```

### Deliberate choices

- **Authorization note on every skill** — not only in a global doc. Each skill reminds Claude and the human reader at the point of use.
- **References section, not inline content** — skills link to OWASP / PortSwigger / NIST rather than re-publishing text. Keeps skills short and avoids staleness.
- **Finding-writeup section on every skill** — shared shape enables Sub-project 5 (reporting) to aggregate findings mechanically.
- **Tool commands section is MCP-aware** — runbooks reference `burp_repeater_send`, `browser_eval`, etc., so they leverage the stack rather than defaulting to shell-outs.

## Naming conventions (written into `docs/skill-conventions.md`)

**Prefixes by category:**

| Prefix        | Purpose                                               | Example                   |
|---------------|-------------------------------------------------------|---------------------------|
| `mcp-*`       | How to use a specific MCP (one per MCP)               | `mcp-browser`, `mcp-burp` |
| `methodology-*` | Process skills (scoping, phases, RoE)               | `methodology-scoping`     |
| `recon-*`     | Information gathering                                 | `recon-subdomain-enum`    |
| `testing-*`   | Attack-technique runbooks                             | `testing-xss`             |
| `reporting-*` | Finding write-up, severity, deliverables              | `reporting-severity-rubric` |
| `_template`   | Reserved directory for the reference skeleton         | `_template`               |

**Frontmatter rules:**

- `name:` must match the directory name exactly.
- `description:` ≤ 180 characters, third-person active voice, so Claude's matcher picks it up from user context.
- Exactly those two fields — no others.

**File & directory rules:**

- Every skill is a directory containing at minimum `SKILL.md`.
- Optional subdirs used only when actually needed:
  - `references/` — verbatim quoted docs (rare)
  - `scripts/` — copy-pasteable payload files or helper scripts
  - `examples/` — sample request/response pairs
- No nesting deeper than one level below the skill directory.
- `SKILL.md` stays under ~400 lines; overflow moves into `references/`.

**Cross-references between skills:**

- Refer by name in prose: `see the \`testing-xss\` skill`. No path links — they break on reorganization.
- `When to use` may declare prerequisites: `Prerequisite skills: mcp-browser, mcp-burp.`

**Authorization & scope (standardized language):**

- Every pentest-technique skill ends with the standard Authorization note.
- `methodology-*` skills cover scoping and rules of engagement centrally — `testing-*` skills reference those rather than re-deriving.
- Skills focus on authorized testing. They do not include defeat/evasion techniques aimed at detection bypass for malicious purposes.

**Quality bar for a committed skill:**

- All template sections filled or explicitly omitted with a one-line comment.
- Description under 180 chars.
- At least one concrete tool command or MCP tool call.
- Authorization note present verbatim.
- All external links are real URLs (no fabricated references). Links verified at commit time by the author; stale-link audits are a future ops task.

## Worked example: `mcp-browser`

The first skill doubles as exemplar and real runbook. Outline (full text produced during implementation):

- **name:** `mcp-browser`
- **description:** "Drive a real Chrome browser via the browser-mcp MCP server for reconnaissance, manual interaction, DOM inspection, and JS execution during web application penetration testing."
- **When to use:** manual interaction (clicks, forms, auth); DOM/JS inspection after client-side rendering; real-user-agent network observation; screenshots for evidence. Prerequisite: browser-mcp registered in Claude Code.
- **Signal:** SPA targets; multi-step auth; client-side-rendered vulnerabilities (DOM XSS, postMessage).
- **Test steps:** `browser_launch` → `browser_navigate` → `browser_snapshot` → `browser_query` / `browser_click` / `browser_fill` → `browser_eval` → `browser_network_log` → `browser_screenshot` → `browser_close`.
- **Tool commands:** 8-10 concrete MCP tool calls with expected response shapes.
- **Interpret results:** envelope `ok: true` vs standard error codes (`TARGET_NOT_ATTACHED`, `TIMEOUT`, `BAD_INPUT`).
- **Finding writeup:** when browser-level behavior is the issue (DOM XSS, client-side auth bypass, postMessage). Title pattern, evidence: screenshot + DOM excerpt + `browser_eval` reproduction.
- **References:** `MCPs/browser-mcp/README.md`, Chrome DevTools Protocol docs, OWASP WSTG Client-side Testing.
- **Authorization note:** standard paragraph.

Later sub-projects write ~40 more skills following this template.

## Discoverability & testing

**Discoverability:**
- Claude Code scans `.claude/skills/*/SKILL.md` on session start in the repo root.
- The `description:` field is what Claude's skill-matcher uses to decide relevance.

**Testing:**
- No automated test harness for prose-only skills.
- Quality is enforced by the template + the checklist in "Quality bar" above.
- Manual smoke test after implementation: open Claude Code in the repo root, ask a browser-related pentest question, confirm Claude proposes the `mcp-browser` skill.

## Out of scope

- No skill loader / validator script — the Quality bar is author-enforced.
- No automated link checker — future ops task.
- No translation into a distributable plugin — packaging deferred; same files can later be referenced from a plugin manifest without moving them.

## Acceptance criteria

1. `.claude/skills/_template/SKILL.md` exists, follows the template, has `description: [TEMPLATE] ...` so Claude's matcher skips it.
2. `.claude/skills/mcp-browser/SKILL.md` exists, is a complete and usable skill (all template sections filled), and was written by following the conventions in `docs/skill-conventions.md`.
3. `docs/skill-conventions.md` exists and covers: naming prefixes, frontmatter rules, file/directory rules, cross-references, authorization standard, quality bar.
4. Committed under the Web-MCP repo with clean, atomic commits.
5. Manual smoke test: starting Claude Code in the repo root and asking a browser-pentest question surfaces the `mcp-browser` skill.
