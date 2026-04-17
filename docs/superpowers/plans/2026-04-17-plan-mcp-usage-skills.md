# MCP Usage Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce three `SKILL.md` files — `mcp-burp`, `mcp-parley`, `mcp-github` — following the format locked in by sub-project 1.

**Architecture:** Three prose markdown files in `.claude/skills/<name>/SKILL.md`. Each follows the 8-section template documented in `docs/skill-conventions.md` with the content plan laid out in the spec.

**Tech Stack:** Markdown + YAML frontmatter. No code, no tests. Content is derived from each MCP's server tool list + README.

**Spec:** `docs/superpowers/specs/2026-04-17-mcp-usage-skills-design.md`
**Exemplar:** `.claude/skills/mcp-browser/SKILL.md` (sub-project 1)

---

### Task 1: `.claude/skills/mcp-burp/SKILL.md`

**Files:**
- Create: `.claude/skills/mcp-burp/SKILL.md`

**Source material (the implementer must read these):**
- Spec section "Per-skill content → `mcp-burp`" — dictates content.
- `MCPs/burp-mcp/burp_mcp/server.py` — authoritative tool names and their JSON schemas.
- `MCPs/burp-mcp/README.md` — upstream usage notes.
- `.claude/skills/mcp-browser/SKILL.md` — format exemplar.
- `docs/skill-conventions.md` — rules.

- [ ] **Step 1: Create directory + write SKILL.md**

`mkdir -p /home/kali/Web-MCP/.claude/skills/mcp-burp`.

Write a complete `SKILL.md` with:

**Frontmatter (exact):**
```yaml
---
name: mcp-burp
description: Drive Burp Suite (Community or Professional) via the burp-mcp MCP server for proxy history analysis, Repeater replay, scope management, sitemap review, and Pro-only Scanner/Intruder control.
---
```

**Body (8 H2 sections in order, all filled):**

1. `## When to use` — situations that require Burp vs the browser (HTTP/S traffic inspection, replay with mutations, scope management, audit scanning). Prereq lines: (a) burp-mcp registered in Claude Code, (b) Kotlin bridge jar loaded in running Burp — point to `MCPs/burp-mcp/burp-ext/BUILD.md`.
2. `## Signal to look for` — HTTP-level target, need for historical replay, need to add/remove scope, Pro-tool required.
3. `## Test steps` — numbered flow: `burp_meta` to verify bridge is live → scope modify if needed → observe via `burp_proxy_history` (filters: host/method/status/contains) → pull specific entry via `burp_proxy_request(id=N)` → replay via `burp_repeater_send(raw_base64, host, port)` → for Pro: `burp_scanner_scan`, poll `burp_scanner_issues` → for Pro: `burp_intruder_launch` → end with match-replace ops if site-wide rewrites are needed.
4. `## Tool commands` — concrete example tool calls for each of the 12 tools with expected success/error envelope shape. Include a `base64` one-liner pattern for the `raw_base64` parameter. **Required:** cover at minimum `burp_meta`, `burp_proxy_history`, `burp_proxy_request`, `burp_repeater_send`, `burp_scope_modify`, `burp_scanner_scan`, `burp_scanner_issues`, `burp_sitemap`, `burp_match_replace_get`, `burp_match_replace_set`. The two Pro-only Scanner and Intruder examples must show the `PRO_REQUIRED` error-envelope shape in a comment so the reader knows what to expect on Community.
5. `## Interpret results` — `ok: true/false` envelope shape. Error codes: `BURP_UNAVAILABLE` (bridge not loaded — fix: load jar, check Burp's Extensions → Output), `PRO_REQUIRED` (Community running a Pro tool — fix: upgrade or skip that tool), `BAD_INPUT` (id/url out of range), `UPSTREAM_HTTP` (bridge returned non-standard error). Also include at least one false-positive pitfall (e.g. "proxy_history total=0 when Burp's upstream proxy setting filters traffic before history recording — verify browser traffic is actually passing through 127.0.0.1:8080").
6. `## Finding writeup` — proxy-history-sourced issue template. Title pattern, severity guidance referencing `reporting-severity-rubric` (forward reference, fine), description template, reproduction steps written as `burp_*` tool calls, suggested fix.
7. `## References` — `MCPs/burp-mcp/README.md`, `MCPs/burp-mcp/burp-ext/BUILD.md`, upstream PortSwigger Montoya API docs (`https://portswigger.github.io/burp-extensions-montoya-api/javadoc/`), OWASP Proxy Testing section of the WSTG.
8. `## Authorization note` — verbatim standard paragraph: *"Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding."*

**Length target:** ≤220 lines total.

- [ ] **Step 2: Verify frontmatter + section count + length**

```bash
cd /home/kali/Web-MCP
head -4 .claude/skills/mcp-burp/SKILL.md
grep -c '^## ' .claude/skills/mcp-burp/SKILL.md
wc -l .claude/skills/mcp-burp/SKILL.md
```

Expected: frontmatter block (`---` / `name:` / `description:` / `---`), grep count = 8, line count ≤ 220.

- [ ] **Step 3: Verify description length**

```bash
d=$(grep -m1 '^description:' .claude/skills/mcp-burp/SKILL.md | sed 's/^description:[[:space:]]*//')
echo "${#d} chars"
```
Expected: ≤ 180.

- [ ] **Step 4: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/mcp-burp/SKILL.md
git commit -m "feat(skills): mcp-burp runbook (12 tools, Pro-gated notes)"
```

---

### Task 2: `.claude/skills/mcp-parley/SKILL.md`

**Files:**
- Create: `.claude/skills/mcp-parley/SKILL.md`

**Source material:**
- Spec section "Per-skill content → `mcp-parley`".
- `MCPs/parley-mcp/README.md` — upstream documentation with full tool list.
- `MCPs/parley-mcp/MCP_SETUP.md` — per-tool usage patterns.
- `MCPs/parley-mcp/run_server.py` — authoritative tool registration.
- `.claude/skills/mcp-browser/SKILL.md` — format exemplar.
- `docs/skill-conventions.md` — rules.

- [ ] **Step 1: Create directory + write SKILL.md**

`mkdir -p /home/kali/Web-MCP/.claude/skills/mcp-parley`.

**Frontmatter:**
```yaml
---
name: mcp-parley
description: Drive Parley-MCP for non-HTTP MiTM proxying (raw TCP/TLS, FIX, ISO 8583, LDAP) and protocol-level traffic capture, modification via custom Python modules, and SQLite-backed analysis.
---
```

**Body — 8 sections:**

1. `## When to use` — non-HTTP or HTTP-plus-protocol-concerns targets; raw TCP/TLS interception; runtime traffic-modification logic in Python (beyond what Burp's match-replace can do). Prereq: parley-mcp registered. Cross-reference: for pure HTTP targets, reach for `mcp-burp` first.
2. `## Signal to look for` — curl / browser inappropriate; target speaks a known non-HTTP protocol (FIX, ISO 8583, LDAP); HTTP traffic needs Python-level mutation.
3. `## Test steps` — numbered flow: `web_proxy_setup` for HTTP; `proxy_start` for raw protocols; create mutation module with `module_create`; let traffic flow; analyze captures via `traffic_query` / `traffic_search` / `traffic_summarize`; query the SQLite DB at `MCPs/parley-mcp/data/parley_mcp.db` for custom joins when needed; `proxy_stop` when done.
4. `## Tool commands` — concrete examples for the 15 tools (group by category: web-proxy, lifecycle, module management, traffic analysis, database). If a specific tool name in upstream differs from the list, use whatever is in `run_server.py`.
5. `## Interpret results` — upstream returns its own success/failure shapes — we do NOT re-wrap them; consume as returned. Include an example of each observed result shape. Flag one false positive: "a module compile error surfaces as a Parley tool error, not a traffic-flow issue — check `module_update` response for syntax errors before assuming proxy isn't routing."
6. `## Finding writeup` — protocol-level issue template. Title pattern includes protocol name. Include byte-level reproduction (hex dump or Parley capture ID) and Parley module source if the finding was triggered by a mutation.
7. `## References` — `MCPs/parley-mcp/README.md`, `MCPs/parley-mcp/MCP_SETUP.md`, OWASP WSTG Testing for Error Handling section, relevant protocol specs (FIX / ISO 8583).
8. `## Authorization note` — verbatim standard paragraph.

**Length target:** ≤200 lines.

- [ ] **Step 2: Verify (same checks as Task 1)**

- [ ] **Step 3: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/mcp-parley/SKILL.md
git commit -m "feat(skills): mcp-parley runbook (non-HTTP MiTM + module system)"
```

---

### Task 3: `.claude/skills/mcp-github/SKILL.md`

**Files:**
- Create: `.claude/skills/mcp-github/SKILL.md`

**Source material:**
- Spec section "Per-skill content → `mcp-github`".
- `MCPs/github-mcp/README.md` — upstream documentation.
- `MCPs/github-mcp/MCPs/github_mcp/server.py` — authoritative tool registration.
- `MCPs/github-mcp/MCPs/libs/mcp_armor/` — secret-redaction library (read to understand what `[REDACTED]` means).
- `.claude/skills/mcp-browser/SKILL.md` and `.claude/skills/mcp-burp/SKILL.md` (the one Task 1 just produced) — cross-referenced by this skill.
- `docs/skill-conventions.md` — rules.

- [ ] **Step 1: Create directory + write SKILL.md**

`mkdir -p /home/kali/Web-MCP/.claude/skills/mcp-github`.

**Frontmatter:**
```yaml
---
name: mcp-github
description: Query GitHub repositories for source-code-informed pentesting — browse files/commits/PRs, search code and issues, review Dependabot alerts — with automatic secret redaction via MCP Armor.
---
```

**Body — 8 sections:**

1. `## When to use` — target is open-source or tester has repo access; want to derive test inputs from source; want to check Dependabot alerts for known-vulnerable deps; want to search for known-bad sinks (`eval`, `exec`, SQL concat, unsanitized HTML). Prereq: github-mcp registered with `GITHUB_TOKEN` in its env (PAT scopes: `repo`, `security_events`). Optional `GHE_TOKEN` for GitHub Enterprise.
2. `## Signal to look for` — endpoint backed by known source; want to correlate runtime with source; want actual deployed library versions.
3. `## Test steps` — numbered source-informed loop: `github_search_code(repo, q)` → `github_get_file_contents(repo, path)` → read to derive targeted input → use `mcp-browser` or `mcp-burp` to probe the endpoint → `burp_proxy_history(contains=<marker>)` to correlate with captured traffic → `github_list_dependabot_alerts(repo)` for known CVEs in deployed deps.
4. `## Tool commands` — concrete examples grouped by use case: repository enumeration (`list_repos`, `get_repo`, `list_branches`, `list_commits`, `list_tags`), code access (`get_file_contents`, `get_directory_tree`), search (`search_repos`, `search_code`, `search_issues`), issues/PRs (`list_issues`, `get_issue`, `list_issue_comments`, `list_pulls`, `get_pull`, `list_pull_files`, `list_pull_comments`), security (`get_security_overview`, `list_dependabot_alerts`), server (`list_servers`).
5. `## Interpret results` — upstream response shapes (per github-mcp). **MCP Armor note (important):** responses pass through a 95+-pattern secret scanner. Any secret is replaced with a placeholder (typically `[REDACTED]` or similar — consult mcp_armor source for exact format). Claude does NOT see the original secret. Do not infer that redacted content "proves" a secret exists in the code — the scanner may false-positive on high-entropy strings. Flag one additional false positive: GitHub rate limits. When hit, `list_*` tools may return partial results; note the 429/403 in the finding.
6. `## Finding writeup` — source-referenced issue template. Include file path, commit SHA, line range (e.g. `src/api/export.py#L42-L57 @ abc123`), and the specific runtime probe (`browser_navigate` or `burp_repeater_send` call) that demonstrates impact against the source-observed sink.
7. `## References` — `MCPs/github-mcp/README.md` (upstream), CWE-200 (Exposure of Sensitive Information), GitHub REST API docs (`https://docs.github.com/en/rest`), OWASP WSTG Information Gathering section.
8. `## Authorization note` — verbatim standard paragraph.

**Length target:** ≤240 lines.

- [ ] **Step 2: Verify (same checks as Task 1)**

- [ ] **Step 3: Commit**

```bash
cd /home/kali/Web-MCP
git add .claude/skills/mcp-github/SKILL.md
git commit -m "feat(skills): mcp-github runbook (source-informed loop + MCP Armor note)"
```

---

### Task 4: Final verification (no commits)

- [ ] **Step 1: Confirm all three files tracked**

```bash
cd /home/kali/Web-MCP
git ls-files .claude/skills/mcp-burp/SKILL.md .claude/skills/mcp-parley/SKILL.md .claude/skills/mcp-github/SKILL.md
```
Expected: all three paths appear.

- [ ] **Step 2: Name-vs-directory consistency check**

```bash
cd /home/kali/Web-MCP
for d in .claude/skills/mcp-burp .claude/skills/mcp-parley .claude/skills/mcp-github; do
  dirname=$(basename "$d")
  name=$(grep -m1 '^name:' "$d/SKILL.md" | awk '{print $2}')
  if [ "$dirname" = "$name" ]; then echo "OK: $dirname"; else echo "MISMATCH: $dirname vs $name"; fi
done
```
Expected: three `OK:` lines.

- [ ] **Step 3: Description length check**

```bash
cd /home/kali/Web-MCP
for f in .claude/skills/mcp-burp/SKILL.md .claude/skills/mcp-parley/SKILL.md .claude/skills/mcp-github/SKILL.md; do
  d=$(grep -m1 '^description:' "$f" | sed 's/^description:[[:space:]]*//')
  echo "${#d} chars: $f"
done
```
Expected: all three ≤ 180.

- [ ] **Step 4: Section count check**

```bash
cd /home/kali/Web-MCP
for f in .claude/skills/mcp-burp/SKILL.md .claude/skills/mcp-parley/SKILL.md .claude/skills/mcp-github/SKILL.md; do
  c=$(grep -c '^## ' "$f")
  echo "$c sections: $f"
done
```
Expected: all three = 8.

- [ ] **Step 5: Authorization paragraph presence**

```bash
cd /home/kali/Web-MCP
for f in .claude/skills/mcp-burp/SKILL.md .claude/skills/mcp-parley/SKILL.md .claude/skills/mcp-github/SKILL.md; do
  if grep -q "Only use against systems you are authorized to test" "$f"; then echo "OK: $f"; else echo "MISSING: $f"; fi
done
```
Expected: three `OK:` lines.

- [ ] **Step 6: If any check above fails, fix inline and make one follow-up commit**

`git commit -m "fix(skills): ..."` describing what was corrected.

---

## Plan-end verification

- [ ] Three feature commits on top of the spec commit: `feat(skills): mcp-burp …`, `feat(skills): mcp-parley …`, `feat(skills): mcp-github …`.
- [ ] All four Task-4 structural checks pass (name/description/sections/authorization).
- [ ] Each of the three skills references concrete MCP tool calls in its `## Tool commands`.
- [ ] Cross-references use skill names only, no paths.
