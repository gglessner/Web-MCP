# MCP Usage Skills — Design

**Date:** 2026-04-17
**Author:** Garland Glessner (gglessner@gmail.com)
**Status:** Approved for planning
**Sub-project:** 2 of 5 in the Web-MCP skill-library track

## Purpose

Produce three `mcp-*` skills (`mcp-burp`, `mcp-parley`, `mcp-github`) that teach Claude how to use each MCP server during a web application penetration test. Together with the existing `mcp-browser` (sub-project 1's exemplar), the four skills form the complete MCP usage map.

## Non-goals

- No per-tool dedicated skills (`mcp-burp-proxy`, `mcp-burp-scanner`, etc.) — coarse-grained covers the exemplar pattern.
- No deep Pro-gated Burp workflows (Scanner/Intruder async polling, Intruder payload set design). Those belong in sub-project 4 as `testing-*` skills that orchestrate the MCP tools toward a specific attack class.
- No packaging changes — skills drop into `.claude/skills/` alongside the existing files.

## Deliverables

Three files under `.claude/skills/`:

```
.claude/skills/
├── mcp-burp/SKILL.md
├── mcp-parley/SKILL.md
└── mcp-github/SKILL.md
```

Each follows the 8-section template locked in by sub-project 1 (`docs/skill-conventions.md`).

## Per-skill content

### `mcp-burp`

- **name:** `mcp-burp`
- **description:** "Drive Burp Suite (Community or Professional) via the burp-mcp MCP server for proxy history analysis, Repeater replay, scope management, sitemap review, and Pro-only Scanner/Intruder control."
- **When to use:** HTTP/S traffic is the subject; need to inspect history, replay with modifications, manage scope, or launch an audit.
- **Prerequisite:** burp-mcp registered in Claude Code AND the Kotlin `burp-mcp-bridge.jar` loaded in a running Burp (see `MCPs/burp-mcp/README.md` and `MCPs/burp-mcp/burp-ext/BUILD.md`).
- **Signal to look for:** HTTP-level testing target; need for historical replay; need to add/remove scope entries; scanning or intruder required.
- **Tools covered (12):** `burp_meta`, `burp_proxy_history`, `burp_proxy_request`, `burp_repeater_send`, `burp_scope_check`, `burp_scope_modify`, `burp_sitemap`, `burp_scanner_scan` (Pro), `burp_scanner_issues` (Pro), `burp_intruder_launch` (Pro), `burp_match_replace_get`, `burp_match_replace_set`.
- **Interpret results:** `BURP_UNAVAILABLE` → bridge not loaded; `PRO_REQUIRED` → Community edition attempting Pro-only tool; `BAD_INPUT` → invalid id/URL.
- **Finding writeup:** proxy-history-sourced issue template — reproduce with Repeater, include raw request/response.
- **Target length:** ≤200 lines.

### `mcp-parley`

- **name:** `mcp-parley`
- **description:** "Drive Parley-MCP for non-HTTP MiTM proxying (raw TCP/TLS, FIX, ISO 8583, LDAP) and protocol-level traffic capture, modification via custom Python modules, and SQLite-backed analysis."
- **When to use:** target is non-HTTP or HTTP plus protocol-level concerns; need raw TCP/TLS interception; need runtime traffic-modification logic written in Python.
- **Prerequisite:** parley-mcp registered in Claude Code; `GITHUB_TOKEN` not needed. See `MCPs/parley-mcp/README.md` and `MCPs/parley-mcp/MCP_SETUP.md`.
- **Signal to look for:** curl/browser are inappropriate; traffic is not HTTP; target speaks a known protocol (FIX, ISO 8583, LDAP, custom TCP); or HTTP traffic needs Python-level modification beyond match-replace.
- **Tools covered (15 across 5 categories):** web-proxy setup (`web_proxy_setup`), proxy lifecycle (start/stop/list/status), module management (create/update/delete), traffic analysis (query/search/summarize/clear), SQLite database.
- **Interpret results:** per-tool error shapes follow upstream; consult Parley-MCP's own error messages verbatim. No in-house wrapper.
- **Finding writeup:** protocol-level issue template — include protocol name, byte-level reproduction, Parley module source if relevant.
- **Cross-reference:** for HTTP targets, reach for `mcp-burp` first.
- **Target length:** ≤180 lines.

### `mcp-github`

- **name:** `mcp-github`
- **description:** "Query GitHub repositories for source-code-informed pentesting — browse files/commits/PRs, search code and issues, review Dependabot alerts — with automatic secret redaction via MCP Armor."
- **When to use:** target is an open-source project or one the tester has repo access to; want to derive targeted inputs from source; want to check Dependabot alerts for known vulnerable deps; want to search for specific sinks (`eval`, `exec`, SQL-string-concat, etc.).
- **Prerequisite:** github-mcp registered in Claude Code with `GITHUB_TOKEN` exported in the MCP's env; optionally `GHE_TOKEN` for Enterprise. See `MCPs/github-mcp/README.md` (upstream).
- **Signal to look for:** endpoint under test is backed by known source; want to correlate runtime observation with source; want to know the library versions actually deployed; looking for known-bad sinks in the code.
- **Tools covered (~20):** repository (list/get/branches/commits/tags), issues (list/get/comments), pull requests (list/get/files/comments), code access (file contents, directory tree), search (repos/code/issues), security (overview, Dependabot alerts), server meta.
- **MCP Armor note:** every response passes through a 95+-pattern secret scanner. If the scan redacts content, Claude will see `[REDACTED]` placeholders, not the original secret. Mention this explicitly in the skill so Claude does not over-interpret redactions as evidence.
- **Source-informed loop:** `github_search_code` → `github_get_file_contents` → derive test input → `browser_navigate` (or `burp_repeater_send`) → correlate with `burp_proxy_history`. Show this loop concretely in `## Test steps`.
- **Finding writeup:** source-referenced issue template — include file path, SHA, line range, and the specific runtime probe that demonstrates impact.
- **Cross-references:** `mcp-burp`, `mcp-browser` (the source-informed loop pulls in both).
- **Target length:** ≤220 lines.

## Cross-reference map

```
mcp-burp     ← referenced by: mcp-parley (for HTTP targets)
mcp-burp     ← referenced by: mcp-github (source-informed loop)
mcp-browser  ← referenced by: mcp-github (source-informed loop)
mcp-parley   stand-alone
```

References are name-only, per the conventions doc.

## Authorization note

All three skills include the standard Authorization paragraph verbatim.

## Quality bar

Each skill passes the sub-project-1 checklist from `docs/skill-conventions.md`:

- Directory name = `name` frontmatter.
- Description under 180 characters.
- All 8 H2 sections present and filled.
- At least one concrete MCP tool call in `## Tool commands`.
- Authorization note present verbatim.
- All external links resolve.
- Under ~400 lines.

## Discoverability & testing

- Claude Code discovers each via `.claude/skills/*/SKILL.md`.
- Manual smoke test after implementation: ask Claude questions that should surface each skill:
  - "The target app is a FIX-protocol trading system, what MCP should I use?" → `mcp-parley`.
  - "I want to check if the target's source has any known Dependabot alerts." → `mcp-github`.
  - "I need to re-send a request from proxy history with a modified header." → `mcp-burp`.

## Acceptance criteria

1. `.claude/skills/mcp-burp/SKILL.md` exists, 8 sections, under 220 lines.
2. `.claude/skills/mcp-parley/SKILL.md` exists, 8 sections, under 200 lines.
3. `.claude/skills/mcp-github/SKILL.md` exists, 8 sections, under 240 lines.
4. Each skill's frontmatter passes the quality bar (name match, description ≤180 chars, two fields only).
5. Each has at least one concrete MCP tool call in `## Tool commands`.
6. Each includes the Authorization note verbatim.
7. Cross-references use skill names only, no paths.
8. Three atomic commits, one per skill.
