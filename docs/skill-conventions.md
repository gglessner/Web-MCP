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
