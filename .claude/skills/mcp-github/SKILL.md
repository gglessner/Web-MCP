---
name: mcp-github
description: Query GitHub repos for source-code-informed pentesting — browse files/commits/PRs, search code, review Dependabot alerts — with automatic secret redaction via MCP Armor.
---

# Using github-mcp for source-code-informed pentesting

## When to use

When the application under test is open-source, or you have repository
access, and you want to derive targeted test inputs from the actual source
code. Also use to check whether known-vulnerable dependency versions are
in use (Dependabot alerts) or to search for dangerous sinks (`eval`,
`exec`, raw SQL concatenation, unsanitised template rendering) before
crafting runtime probes.

Prerequisites:

1. `github-mcp` registered in Claude Code with `GITHUB_TOKEN` in the
   MCP's environment (PAT scopes required: `repo`, `security_events`).
2. For GitHub Enterprise: also export `GHE_TOKEN` and configure the
   enterprise hostname. See `MCPs/github-mcp/README.md`.

## Signal to look for

- Endpoint under test is backed by source you can read (open-source
  project, or you have repo access via the engagement scope).
- Want to correlate a runtime observation (error message, stack trace,
  redirect URL) with the exact source file and line that produced it.
- Want the actual deployed dependency versions rather than inferred ones.
- Looking for specific dangerous patterns in code: `eval`, `exec`,
  `subprocess`, raw SQL string concat, `innerHTML`, `dangerouslySetInnerHTML`.

## Test steps

Source-informed attack loop:

1. Discover the codebase layout:
   `get_directory_tree(repo_url="https://github.com/owner/repo")`
2. Search for a dangerous sink:
   `search_code(query="eval repo:owner/repo language:javascript")`
3. Read the file containing the sink:
   `get_file_contents(repo_url="https://github.com/owner/repo", path="src/render.js", ref="main")`
4. Note the surrounding logic and identify the controlled input.
5. Probe the live endpoint using `mcp-browser`
   (`browser_navigate` + `browser_eval`) or `mcp-burp`
   (`burp_repeater_send` with a crafted payload).
6. Correlate the response with `burp_proxy_history(contains="<marker>")`
   to confirm the code path was reached.
7. Check for known-vulnerable dependencies:
   `list_dependabot_alerts(repo_url="https://github.com/owner/repo", state="open")`
8. Cross-reference the CVE identifiers with the runtime behaviour you
   observed in steps 5–6.
9. Record the file path, commit SHA, and line range for the finding writeup.

## Tool commands

```
# Server + repository enumeration
list_servers()
# Success: [{"name": "...", "hostname": "github.com", "authenticated": true}]

list_repos(owner="target-org", repo_type="public", max_results=20)
# Success: list of repo summaries with full_name, language, stars, etc.

get_repo(repo_url="https://github.com/owner/repo")
# Success: detailed dict including languages, license, topics, dependency files

list_branches(repo_url="https://github.com/owner/repo")
# Success: [{"name": "main", "protected": true, "sha": "abc123"}]

list_commits(repo_url="https://github.com/owner/repo", branch="main",
             since="2025-01-01", max_results=20)
# Success: list with sha, message, author, date

list_tags(repo_url="https://github.com/owner/repo")
# Success: [{"name": "v2.3.1", "sha": "...", "tarball_url": "..."}]

# Code access
get_directory_tree(repo_url="https://github.com/owner/repo", path="src", max_depth=3)
# Success: {"repo": "owner/repo", "ref": "main", "total_entries": 47, "entries": [...]}

get_file_contents(repo_url="https://github.com/owner/repo",
                  path="src/api/export.py", ref="abc123")
# Success: {"type": "file", "path": "...", "content": "...", "sha": "abc123", ...}

# Search
search_repos(query="target-product language:python")
# Success: list of repos matching query

search_code(query="eval repo:owner/repo language:javascript")
# Success: [{"name": "render.js", "path": "src/render.js", "sha": "...", "html_url": "..."}]

search_issues(query="security is:issue state:open repo:owner/repo")
# Success: list of issues with number, title, labels, html_url

# Issues and PRs
list_issues(repo_url="https://github.com/owner/repo", state="open", max_results=20)
get_issue(repo_url="https://github.com/owner/repo", number=42)
list_issue_comments(repo_url="https://github.com/owner/repo", number=42)
list_pulls(repo_url="https://github.com/owner/repo", state="open")
get_pull(repo_url="https://github.com/owner/repo", number=17)
list_pull_files(repo_url="https://github.com/owner/repo", number=17)
list_pull_comments(repo_url="https://github.com/owner/repo", number=17)

# Security
get_security_overview(repo_url="https://github.com/owner/repo")
# Success: dict with default_branch_protected, security_policy, codeowners,
#           dependabot_config, dependency_files

list_dependabot_alerts(repo_url="https://github.com/owner/repo",
                       state="open", severity="critical")
# Success: list with package_name, severity, vulnerable_version_range,
#           patched_version, cve_id, cvss_score, cwes, html_url
# 403 error: {"error": true, "message": "Dependabot alerts require 'security_events' scope..."}
```

## Interpret results

Tools return Python dicts or lists directly (no `{"ok": ...}` envelope).
On error, they return `{"error": true, "status": <N>, "message": "..."}`.

**MCP Armor — important:** every response passes through a 95+-pattern
secret scanner before Claude sees it. Matched secrets are replaced with
placeholders. The base placeholder string is `[REDACTED]`; type-specific
variants include `[REDACTED_GITHUB_TOKEN]`, `[REDACTED_PASSWORD]`,
`[REDACTED_API_KEY]`, `Bearer [REDACTED]`, and others defined in
`MCPs/github-mcp/MCPs/libs/mcp_armor/config.py`. Claude does NOT see the
original value. Do not conclude that a redaction proves a secret exists in
the code — the scanner may false-positive on high-entropy strings (base64
blobs, UUIDs, encoded tokens in tests). Note the redaction in the finding
as a potential exposure indicator, but confirm with a second signal.

Additional false positives:

- **GitHub rate limiting:** `list_*` tools may return partial results
  without an explicit error when the REST API 429/403 rate limit is hit.
  If results seem truncated, reduce `max_results` and retry.
- **PAT scope gaps:** `list_dependabot_alerts` returns a 403 with a
  descriptive message when the PAT lacks `security_events` scope.

## Finding writeup

- **Title pattern:** `<Sink type> in <file path> (source-confirmed)` — e.g.
  "Server-Side Template Injection sink in `src/render.py` (source-confirmed)".
- **Severity guidance:** Reference the `reporting-severity-rubric` skill.
  Source-confirmed RCE sink with a controlled runtime input is Critical.
  Unpatched Dependabot CVE with known PoC exploit is High.
- **Description template:** *"Source review of `<repo>` at commit `<SHA>`
  reveals that `<parameter>` is passed unsanitised to `<dangerous function>`
  at `<path>#L<start>-L<end>`. A runtime probe with payload `<payload>`
  sent via `<tool>` confirmed execution, demonstrating `<impact>`."*
- **Reproduction steps:** include the `search_code` query, the
  `get_file_contents` call with `ref=<SHA>`, the line range
  (`src/api/export.py#L42-L57 @ abc123`), and the `browser_navigate` or
  `burp_repeater_send` call that confirmed the runtime impact.
- **Suggested fix:** apply input validation at the point of ingestion and
  use a safe API (parameterised query, sandboxed template, etc.) at the
  point of use. Link to the relevant CWE.

## References

- github-mcp upstream README: `MCPs/github-mcp/README.md`
- CWE-200 Exposure of Sensitive Information:
  https://cwe.mitre.org/data/definitions/200.html
- GitHub REST API documentation:
  https://docs.github.com/en/rest
- OWASP WSTG — Information Gathering:
  https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
