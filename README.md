# Web-MCP

Four-MCP Python stack **plus a 49-skill Claude Code skill library** for
AI-driven web application security auditing and PoC validation. Built to run
on a tester's workstation, registered with Claude Code via stdio.

**MCP servers:**

- **browser-mcp** — CDP-driven browser (no Node.js, no Playwright)
- **burp-mcp** — Burp Suite via a Kotlin Montoya extension + HTTP bridge
- **parley-mcp** — user's TCP/TLS MiTM proxy (vendored from upstream)
- **github-mcp** — user's source-aware GitHub MCP with secret redaction (vendored)

**Skill library** (`.claude/skills/`, auto-loaded when Claude Code is launched
in this repo):

- 4 `mcp-*` usage guides (one per MCP server)
- 4 `methodology-*` process skills (scoping, rules of engagement, phases, evidence capture)
- 6 `recon-*` information-gathering runbooks
- 30 `testing-*` attack-technique runbooks across the OWASP 2021 Top 10 and adjacent classes
- 4 `reporting-*` deliverable skills (severity rubric, finding writeup, full report, executive summary)
- 1 `_template` reference skeleton

See `docs/superpowers/specs/2026-04-16-web-mcp-stack-design.md` for the stack
design and `docs/skill-conventions.md` for the skill-library conventions.
See `docs/source-informed-workflow.md` for a worked example of source-aware testing.
Per-sub-project specs and plans live under `docs/superpowers/specs/` and
`docs/superpowers/plans/`.

## Prerequisites

- Python 3.13
- Burp Suite (Community or Professional) on PATH
- JDK 17+ and Gradle (for building the burp-mcp Kotlin extension) — the project
  ships `./gradlew` wrapper so a system Gradle install is optional, but JDK is required.
- Chromium or Chrome (for browser-mcp)
- A GitHub Personal Access Token with at least `repo` and `security_events`
  scopes (for github-mcp). Optionally `GHE_TOKEN` for GitHub Enterprise.

## Setup

Run these from the root of your local clone:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e ".[dev]"
pip install -e MCPs/browser-mcp
pip install -e MCPs/burp-mcp
# Parley and github upstream deps:
pip install -r MCPs/parley-mcp/requirements.txt
if [ -f MCPs/github-mcp/MCPs/libs/mcp_armor/requirements.txt ]; then
  pip install -r MCPs/github-mcp/MCPs/libs/mcp_armor/requirements.txt
fi
if [ -f MCPs/github-mcp/requirements.txt ]; then
  pip install -r MCPs/github-mcp/requirements.txt
fi

# Build the Burp Kotlin extension
(cd MCPs/burp-mcp/burp-ext && ./gradlew shadowJar)
# Produces MCPs/burp-mcp/burp-ext/build/libs/burp-mcp-bridge.jar

# Optional: install pre-commit hooks for ruff
pip install pre-commit && pre-commit install
```

## Register with Claude Code

The repo ships a project-scoped `.mcp.json` at the root that Claude Code
auto-loads when you run `claude` inside the repo. All paths in that file use
the `${WEB_MCP_ROOT}` environment variable, so no per-user JSON edits are
required — just export the variable once.

**One-time setup after cloning:**

```bash
cd /wherever/you/cloned/Web-MCP
export WEB_MCP_ROOT="$(pwd)"
export GITHUB_TOKEN="<your-github-pat>"   # repo + security_events scopes
```

Add those two `export` lines to your shell profile (`~/.bashrc`, `~/.zshrc`)
so future sessions pick them up automatically.

**Then:**

```bash
claude   # launched from inside the repo
/mcp     # should list browser-mcp, burp-mcp, parley-mcp, github-mcp as connected
```

### Optional: make the MCPs available outside this repo

If you want the four MCPs registered globally (available from any directory,
not just when Claude Code is launched in this repo), merge the `mcpServers`
block from `claude_config.example.json` into your user settings at
`~/.claude/settings.json`. The same `${WEB_MCP_ROOT}` and `${GITHUB_TOKEN}`
variables apply.

**Note on `github-mcp`:** Its package is nested one level deep at
`MCPs/github-mcp/MCPs/github_mcp/`, so both config files set
`cwd: "${WEB_MCP_ROOT}/MCPs/github-mcp/MCPs"` to make `python -m github_mcp`
resolve. If upstream flattens the layout in the future, update `cwd`.

## Load the Burp extension

1. Launch Burp Suite.
2. Extensions → Add → Extension type: Java → File:
   `MCPs/burp-mcp/burp-ext/build/libs/burp-mcp-bridge.jar` → Next.
3. Open the Output tab and confirm: `burp-mcp-bridge listening on 127.0.0.1:8775`.
4. From a shell: `curl -s http://127.0.0.1:8775/meta` — should return edition
   and version.

## Running the tests

```bash
source .venv/bin/activate
pytest -v                          # unit tests (~60 currently)
pytest -m integration -v           # integration tests (need Chrome + live Burp)
```

## Smoke-test checklist

Run these manually to confirm the full stack is wired up.

- [ ] `curl http://127.0.0.1:8775/meta` returns `{"ok": true, ...}`.
- [ ] Claude Code `/mcp` lists `browser-mcp`, `burp-mcp`, `parley-mcp`,
      `github-mcp` as connected.
- [ ] Claude Code prompt: *"Use browser_launch headless=true, then
      browser_navigate to http://127.0.0.1:5055/search?q=hello (after starting
      the fixture: `python tests/fixtures/target_app.py`). Screenshot, then
      close."* — Succeeds end-to-end and `logs/browser-mcp.log` shows the
      activity.
- [ ] Claude Code prompt: *"Set `127.0.0.1:8080` as the browser proxy, then
      navigate to http://127.0.0.1:5055/echo?q=probe. After that, query
      burp_proxy_history with contains='probe' and show me the entries."* — Burp
      history contains the probe request.
- [ ] `curl -s -X POST http://127.0.0.1:8775/http/send -H 'Content-Type: application/json' \
      -d '{"raw_base64":"R0VUIC9lY2hvP3E9aGkgSFRUUC8xLjENCkhvc3Q6IDEyNy4wLjAuMTo1MDU1DQpDb25uZWN0aW9uOiBjbG9zZQ0KDQo=","host":"127.0.0.1","port":5055,"secure":false}'`
      → `{"ok": true, "data": {"status": 200, ...}}` (fixture must be running).
- [ ] Claude Code prompt: *"Use burp_http_send to GET http://127.0.0.1:5055/echo?q=hello
      with save_to='smoke/echo', then list the evidence dir."* — `evidence/smoke/echo.request.http`
      and `.response.http` appear on disk.
- [ ] Claude Code prompt: *"Use github_search_code to find 'def login' in repo
      `gglessner/Parley-MCP` (or any repo you have access to)."* — github-mcp
      returns results with any secrets redacted by MCP Armor.
- [ ] Claude Code prompt: *"Use parley tools to list available parley modules."*
      — Parley responds with its module list.
- [ ] Skill-library smoke tests (one per category):
  - *"How do I rate this finding's severity?"* → Claude surfaces `reporting-severity-rubric`.
  - *"The `q` parameter is reflected into the HTML response — how do I confirm XSS?"* → surfaces `testing-xss-reflected`.
  - *"I need the list of subdomains for target.com."* → surfaces `recon-subdomain-enum`.
  - *"What should I do before I touch this target?"* → surfaces `methodology-scoping`.

## Project layout

```
Web-MCP/
├── .claude/skills/    # 49-skill Claude Code skill library (auto-loaded)
├── .mcp.json          # project-scoped MCP config (auto-loaded by Claude Code)
├── common/            # shared Python lib (config, logging, CDP, BurpClient, MCP base)
├── MCPs/
│   ├── browser-mcp/   # CDP-driven browser MCP (our code)
│   ├── burp-mcp/      # Kotlin Burp extension + Python MCP wrapper (our code)
│   ├── parley-mcp/    # upstream clone (UPSTREAM.txt records pinned commit)
│   └── github-mcp/    # upstream clone (UPSTREAM.txt records pinned commit)
├── docs/
│   ├── skill-conventions.md   # skill-library naming/format/layout rules
│   └── superpowers/           # per-sub-project specs + plans
├── tests/
│   ├── integration/   # @pytest.mark.integration (opt-in)
│   └── fixtures/      # Flask target app (intentionally vulnerable, test-only)
├── logs/              # per-MCP JSON logs (gitignored)
├── config.toml        # shared config (paths, ports, proxy default)
├── config.local.toml  # per-tester overrides (gitignored; optional)
└── claude_config.example.json  # global-settings variant of the MCP config
```

## Updating vendored upstreams

```bash
cd "${WEB_MCP_ROOT}/MCPs/parley-mcp"   # or .../MCPs/github-mcp
git clone https://github.com/gglessner/Parley-MCP.git /tmp/parley-latest
rm -rf ./*
cp -r /tmp/parley-latest/* .
UPSTREAM=$(cd /tmp/parley-latest && git rev-parse HEAD)
echo "upstream: https://github.com/gglessner/Parley-MCP" > UPSTREAM.txt
echo "pinned_commit: $UPSTREAM" >> UPSTREAM.txt
date -u +"pinned_at: %Y-%m-%dT%H:%M:%SZ" >> UPSTREAM.txt
cd "${WEB_MCP_ROOT}"
pip install -r MCPs/parley-mcp/requirements.txt  # re-install in case deps changed
git add MCPs/parley-mcp/
git commit -m "chore(parley-mcp): bump vendored snapshot"
```

## Troubleshooting

- **`BURP_UNAVAILABLE` from burp-mcp tools** — Burp is not running, the jar is
  not loaded, or it failed to bind 8775. Check Burp → Output for the bridge
  startup line.
- **`TARGET_NOT_ATTACHED` from browser-mcp** — call `browser_launch` first.
  Chrome might have crashed; check `logs/browser-mcp.log`.
- **github-mcp startup error** — `GITHUB_TOKEN` not exported in the shell that
  launched Claude Code. The `env` block in `.mcp.json` references the parent
  environment; export it there.
- **`${WEB_MCP_ROOT}` appears in the MCP spawn command error** — the variable
  is unset in the shell that launched Claude Code. `export WEB_MCP_ROOT="$(pwd)"`
  from the repo root and restart Claude Code.
- **Integration tests skipped** — expected when chromium or Burp isn't running.
  Skip reasons are printed by pytest.

## License

Copyright (C) 2026 Garland Glessner &lt;gglessner@gmail.com&gt;

Web-MCP is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version. See the [`LICENSE`](LICENSE) file for the full text.

Web-MCP is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE. See the GNU General Public License for more details.

Vendored upstreams (`MCPs/parley-mcp`, `MCPs/github-mcp`) retain their
respective upstream licences — both GPL-3.0 per their source repositories.
