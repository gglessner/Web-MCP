# Web-MCP — To-Do

Items that can't be automated by the build — manual steps and follow-ups. Tick as you go.

## Manual bring-up

### 1. Build + load the Burp extension
- [ ] `cd MCPs/burp-mcp/burp-ext && ./gradlew shadowJar` — confirms `BUILD SUCCESSFUL` and writes `build/libs/burp-mcp-bridge.jar` (already built once during Plan B Task 10; re-run after code changes).
- [ ] Launch Burp Suite.
- [ ] Extensions → Add → Extension type: **Java** → file: `${WEB_MCP_ROOT}/MCPs/burp-mcp/burp-ext/build/libs/burp-mcp-bridge.jar` → Next.
- [ ] Burp → Extensions → Output tab shows: `burp-mcp-bridge listening on 127.0.0.1:8775`.
- [ ] From a shell: `curl -s http://127.0.0.1:8775/meta | python -m json.tool` returns `{"ok": true, "data": {...}}`.

### 2. Claude Code registration
- [ ] `cp claude_config.example.json claude_config.json` (the copy is gitignored).
- [ ] In `claude_config.json`, replace `"${GITHUB_TOKEN}"` with your real GitHub PAT (needs `repo` + `security_events` scopes).
- [ ] Merge the `mcpServers` block into `~/.claude/settings.json` (or whichever registration path your Claude Code version uses).
- [ ] Restart Claude Code.
- [ ] Run `/mcp` → verify all four listed as `connected`: `browser-mcp`, `burp-mcp`, `parley-mcp`, `github-mcp`.

### 3. End-to-end smoke test (from README)
- [ ] `curl http://127.0.0.1:8775/meta` → `{"ok": true, ...}`.
- [ ] Start the fixture: `python tests/fixtures/target_app.py` (in its own terminal).
- [ ] Claude prompt: *"Run browser_launch headless=true, then browser_navigate to http://127.0.0.1:5055/search?q=hello, screenshot, then close."* — end-to-end succeeds, `logs/browser-mcp.log` shows the navigation.
- [ ] Claude prompt: *"Set 127.0.0.1:8080 as the browser proxy, navigate to http://127.0.0.1:5055/echo?q=probe, then query burp_proxy_history with contains='probe'."* — history contains the probe request.
- [ ] Claude prompt: *"Use github_search_code to find 'def login' in `gglessner/Parley-MCP`."* — results returned, any secrets redacted by MCP Armor.
- [ ] Claude prompt: *"Use parley tools to list available parley modules."* — Parley responds.

### 4. Integration test with live Burp
- [ ] Start Burp + extension (steps in section 1).
- [ ] Start Flask fixture.
- [ ] `source .venv/bin/activate && pytest -m integration -v` — both integration tests should now PASS (no more SKIP on the chain test).

## Deferred / nice-to-have

### Code-quality follow-ups flagged during reviews (non-blocking)
- [ ] `common/config.py` — consider `frozen=True` on dataclasses if you want misconfig-at-runtime prevention (see code review on Task 3).
- [ ] `common/cdp.py` — consider typing tightening: `Callable[[str, dict[str, Any]], None]` for `EventCallback`, `dict[str, Any]` instead of bare `dict` on `send(params=...)`.
- [ ] `common/cdp.py` — replace the `assert self._ws is not None` guards with explicit `RuntimeError` raises (survives `python -O`).
- [ ] Timestamp format in `common/logging.py` — add `.%fZ` for sub-second precision and `Z` suffix; useful for correlating MCP logs against Chrome/Burp timestamps.

### UX polish
- [ ] Add a one-line comment above `[tool.setuptools.packages.find]` in `pyproject.toml` explaining why it's there (setuptools flat-layout auto-discovery fails with sibling non-package dirs).
- [ ] Write a short `docs/source-informed-workflow.md` with a worked example of combining `github-mcp` + `browser-mcp` + `burp-mcp` for source-aware testing (spec has the concept, no worked example exists yet).

### Burp extension
- [ ] Task 9 (match-replace) used `exportUserOptionsAsJson` / `importUserOptionsFromJson`. Confirm this works end-to-end against a Burp Community instance (the API is present, but round-trip fidelity isn't yet verified against real Burp state).
- [ ] Commit `burp-mcp-bridge.jar` as a release artifact? Currently `MCPs/burp-mcp/burp-ext/build/` is gitignored. Reason to commit: testers without JDK don't need to build. Reason to keep gitignored: jar diffs are noisy. **Decision:** leave gitignored; document in README that build is required. (Already done.)

### Upstream vendoring
- [ ] Subscribe to upstream PRs / tags on `gglessner/Parley-MCP` and `gglessner/github-MCP` so you know when to re-vendor.
- [ ] Add a script `scripts/update-vendored.sh` that does the clone-copy-pin dance documented in the README, reducing the chance of stale `UPSTREAM.txt`.

### Operational
- [ ] Add `scripts/build-all.sh` — single entry point that rebuilds the Kotlin jar, reinstalls Python editable packages, and runs the test suite. Useful for CI or a fresh-clone tester.
- [ ] Add basic log rotation or size cap — `logs/*.log` currently grow unbounded.
- [ ] Consider adding `pre-commit` hooks for ruff + basic Kotlin lint.

## Done (for reference)
- ✅ Plan A (19 tasks): foundation + browser-mcp
- ✅ Plan B (16 tasks): burp-mcp Kotlin extension + Python wrapper
- ✅ Plan C (8 tasks): Parley + github vendored, Flask fixture, integration tests, README
- ✅ 61 unit tests + 1 integration test passing
- ✅ 47 commits across all three plans
- ✅ Skill-library track (sub-projects 1-5): 49 skills under `.claude/skills/`
  - Sub-project 1: infrastructure + `_template` + `mcp-browser` exemplar
  - Sub-project 2: `mcp-burp`, `mcp-parley`, `mcp-github` (3 MCP usage skills)
  - Sub-project 3: 4 `methodology-*` + 6 `recon-*` (10 skills)
  - Sub-project 4: 30 `testing-*` attack-technique runbooks
  - Sub-project 5: 4 `reporting-*` deliverable skills
