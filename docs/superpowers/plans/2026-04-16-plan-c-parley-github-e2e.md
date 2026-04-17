# Plan C — parley-mcp + github-mcp Integration + E2E + README

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pull in the two upstream MCPs (Parley-MCP and github-MCP) unchanged, wire them into Claude Code, add a Flask fixture target app and integration tests that exercise the browser → Burp → fixture chain, and finish with a complete setup/smoke README.

**Architecture:** Both upstream MCPs are `git clone`d into `MCPs/parley-mcp/` and `MCPs/github-mcp/` and installed into the shared venv. No modifications — future upstream updates flow via `git pull`. Integration tests live under `tests/integration/` behind the `@pytest.mark.integration` marker (not run by default CI). The Flask fixture is a deliberately small, known-vulnerable-by-design target used only by our tests.

**Tech Stack:** git, Python 3.13, `flask`, `pytest-asyncio`, `httpx` (test client), existing common/ + browser-mcp + burp-mcp.

**Prereqs:** Plans A and B complete. Internet access for `git clone`. A GitHub Personal Access Token exported as `GITHUB_TOKEN` with at minimum `repo` and `security_events` scopes.

**Spec:** `docs/superpowers/specs/2026-04-16-web-mcp-stack-design.md`

---

### Task 1: Clone Parley-MCP and install into shared venv

**Files:**
- Create: `MCPs/parley-mcp/` (via git clone)
- Modify: `/home/kali/Web-MCP/.gitignore` (exclude upstream clones' own history)

- [ ] **Step 1: Clone Parley-MCP upstream**

```bash
cd /home/kali/Web-MCP/MCPs
git clone https://github.com/gglessner/Parley-MCP.git parley-mcp
cd parley-mcp
git log --oneline -1  # sanity: we're on some commit
```
Expected: clone succeeds, produces a `parley-mcp/run_server.py` (or equivalent entry point per upstream README).

- [ ] **Step 2: Decide how to track upstream state — option A (submodule) vs option B (plain subdir with upstream commit recorded)**

We pick **option B** (simpler for solo work; easier `git pull` without submodule ceremony). Record the upstream commit hash in a file so it is visible in `git log`:

```bash
cd /home/kali/Web-MCP/MCPs/parley-mcp
UPSTREAM=$(git rev-parse HEAD)
echo "upstream: https://github.com/gglessner/Parley-MCP" > UPSTREAM.txt
echo "pinned_commit: $UPSTREAM" >> UPSTREAM.txt
date -u +"pinned_at: %Y-%m-%dT%H:%M:%SZ" >> UPSTREAM.txt
# Remove the nested .git so the outer repo tracks files directly
rm -rf .git
```

- [ ] **Step 3: Install Parley requirements into the shared venv**

```bash
cd /home/kali/Web-MCP
source .venv/bin/activate
pip install -r MCPs/parley-mcp/requirements.txt
python -c "import sys; sys.path.insert(0, 'MCPs/parley-mcp'); import run_server" 2>&1 | tail -5
```
Expected: requirements install cleanly. The import smoke test may print a startup warning or immediately start the server; as long as there is no `ModuleNotFoundError`, we're good. If it starts the server, Ctrl-C.

- [ ] **Step 4: Verify entry point runs**

```bash
cd /home/kali/Web-MCP
timeout 3 .venv/bin/python MCPs/parley-mcp/run_server.py < /dev/null 2>&1 | head -10 || true
```
Expected: the server prints a startup line (tool list or ready message). We terminate after 3 seconds because MCP stdio servers wait for a client.

- [ ] **Step 5: Commit**

```bash
git add MCPs/parley-mcp/
git commit -m "chore(parley-mcp): vendor upstream Parley-MCP (pinned in UPSTREAM.txt)"
```

---

### Task 2: Clone github-MCP and install into shared venv

**Files:**
- Create: `MCPs/github-mcp/` (via git clone)

- [ ] **Step 1: Clone upstream**

```bash
cd /home/kali/Web-MCP/MCPs
git clone https://github.com/gglessner/github-MCP.git github-mcp
cd github-mcp
UPSTREAM=$(git rev-parse HEAD)
echo "upstream: https://github.com/gglessner/github-MCP" > UPSTREAM.txt
echo "pinned_commit: $UPSTREAM" >> UPSTREAM.txt
date -u +"pinned_at: %Y-%m-%dT%H:%M:%SZ" >> UPSTREAM.txt
rm -rf .git
```

- [ ] **Step 2: Install its MCP Armor requirements**

```bash
cd /home/kali/Web-MCP
source .venv/bin/activate
# Per upstream README: armor lib is at MCPs/libs/mcp_armor within the repo
if [ -f MCPs/github-mcp/MCPs/libs/mcp_armor/requirements.txt ]; then
  pip install -r MCPs/github-mcp/MCPs/libs/mcp_armor/requirements.txt
fi
if [ -f MCPs/github-mcp/requirements.txt ]; then
  pip install -r MCPs/github-mcp/requirements.txt
fi
```
Expected: requirements install. If neither file exists (upstream restructured), run `find MCPs/github-mcp -name requirements.txt` and install what is there.

- [ ] **Step 3: Import smoke test**

```bash
cd /home/kali/Web-MCP/MCPs/github-mcp
/home/kali/Web-MCP/.venv/bin/python -c "import github_mcp; print('ok')" 2>&1 | tail -3
```
Expected: `ok`. If it fails with `ModuleNotFoundError: github_mcp`, inspect the upstream layout (`ls` the repo); the module may be at a different path and the Claude config's `cwd` will need to point to its root.

- [ ] **Step 4: Commit**

```bash
cd /home/kali/Web-MCP
git add MCPs/github-mcp/
git commit -m "chore(github-mcp): vendor upstream github-MCP (pinned in UPSTREAM.txt)"
```

---

### Task 3: Wire parley-mcp and github-mcp into `claude_config.example.json`

**Files:**
- Modify: `/home/kali/Web-MCP/claude_config.example.json`

- [ ] **Step 1: Replace `claude_config.example.json` with the full four-MCP block**

```json
{
  "mcpServers": {
    "browser-mcp": {
      "command": "/home/kali/Web-MCP/.venv/bin/python",
      "args": ["-m", "browser_mcp.server"]
    },
    "burp-mcp": {
      "command": "/home/kali/Web-MCP/.venv/bin/python",
      "args": ["-m", "burp_mcp.server"]
    },
    "parley-mcp": {
      "command": "/home/kali/Web-MCP/.venv/bin/python",
      "args": ["/home/kali/Web-MCP/MCPs/parley-mcp/run_server.py"],
      "cwd": "/home/kali/Web-MCP/MCPs/parley-mcp"
    },
    "github-mcp": {
      "command": "/home/kali/Web-MCP/.venv/bin/python",
      "args": ["-m", "github_mcp"],
      "cwd": "/home/kali/Web-MCP/MCPs/github-mcp",
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

**Note:** Claude Code does not do shell-style env expansion of `${GITHUB_TOKEN}` in config files — the tester replaces `"${GITHUB_TOKEN}"` with their actual PAT **in a non-committed copy of the file** (see next step). We ship the placeholder in the example.

- [ ] **Step 2: Document the non-committed copy pattern in `.gitignore`**

Append to `.gitignore`:
```
# Per-tester copy of Claude config with real PAT
claude_config.json
```

- [ ] **Step 3: Commit**

```bash
git add claude_config.example.json .gitignore
git commit -m "chore: register parley-mcp and github-mcp in Claude config example"
```

---

### Task 4: Flask fixture target app

**Files:**
- Create: `tests/fixtures/__init__.py`
- Create: `tests/fixtures/target_app.py`
- Create: `tests/fixtures/README.md`

- [ ] **Step 1: Write the failing test first (which pulls in a not-yet-existent fixture)**

`tests/test_target_app.py`:
```python
import pytest
from flask.testing import FlaskClient

from tests.fixtures.target_app import create_app


@pytest.fixture
def client() -> FlaskClient:
    return create_app().test_client()


def test_echo_returns_query(client: FlaskClient):
    r = client.get("/echo?q=hi")
    assert r.status_code == 200
    assert r.json == {"q": "hi"}


def test_reflected_xss_reflects_q_unsafely(client: FlaskClient):
    r = client.get("/search?q=%3Cscript%3Ealert(1)%3C/script%3E")
    assert r.status_code == 200
    assert "<script>alert(1)</script>" in r.get_data(as_text=True)


def test_login_accepts_hardcoded_creds(client: FlaskClient):
    r = client.post("/login", data={"user": "admin", "pass": "hunter2"})
    assert r.status_code == 200
    assert "welcome, admin" in r.get_data(as_text=True).lower()


def test_login_rejects_bad_creds(client: FlaskClient):
    r = client.post("/login", data={"user": "admin", "pass": "x"})
    assert r.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/kali/Web-MCP
source .venv/bin/activate
pip install flask
pytest tests/test_target_app.py -v
```
Expected: FAIL — `tests.fixtures.target_app` missing.

- [ ] **Step 3: Implement `tests/fixtures/target_app.py`**

```python
"""Flask fixture target: deliberately small, *intentionally* vulnerable, used only by tests."""
from __future__ import annotations

from flask import Flask, request, abort


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/echo")
    def echo():
        return {"q": request.args.get("q", "")}

    @app.get("/search")
    def search():
        # DELIBERATELY UNSAFE: unescaped reflection for XSS fixture.
        q = request.args.get("q", "")
        return f"<html><body>You searched for: {q}</body></html>", 200, {"Content-Type": "text/html"}

    @app.post("/login")
    def login():
        user = request.form.get("user", "")
        pwd = request.form.get("pass", "")
        if user == "admin" and pwd == "hunter2":
            return f"<html><body>Welcome, {user}</body></html>"
        abort(401)

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5055, debug=False)
```

- [ ] **Step 4: Write `tests/fixtures/README.md`**

```markdown
# Test fixtures

`target_app.py` is a **deliberately vulnerable** Flask app used by integration tests.
Do not deploy it. Do not use it outside `tests/integration/`.

It provides:
- `GET /echo?q=...` — JSON echo
- `GET /search?q=...` — reflected XSS (unescaped)
- `POST /login` — hardcoded creds `admin`/`hunter2`

Run standalone for manual exploration:
```bash
python tests/fixtures/target_app.py
# Browse to http://127.0.0.1:5055/search?q=<script>alert(1)</script>
```
```

- [ ] **Step 5: `tests/fixtures/__init__.py`** — empty file.

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_target_app.py -v
```
Expected: PASS (four tests).

- [ ] **Step 7: Add `flask` to dev deps**

Modify `/home/kali/Web-MCP/pyproject.toml`, append to `project.optional-dependencies.dev`:
```toml
  "flask>=3",
```
So the full `dev` list is:
```toml
dev = [
  "pytest>=8",
  "pytest-asyncio>=0.23",
  "pytest-cov>=5",
  "respx>=0.21",
  "ruff>=0.5",
  "flask>=3",
]
```
Then:
```bash
pip install -e ".[dev]"
```

- [ ] **Step 8: Commit**

```bash
git add tests/fixtures/ tests/test_target_app.py pyproject.toml
git commit -m "test: Flask fixture target app (intentional XSS + login) + unit tests"
```

---

### Task 5: Integration test — browser-only (real Chrome, no Burp)

**Files:**
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/conftest.py`
- Create: `tests/integration/test_browser_only.py`

- [ ] **Step 1: Write `tests/integration/conftest.py`** (fixture that runs the Flask app in a thread)

```python
"""Integration test fixtures: run the Flask fixture as a live server in a thread."""
from __future__ import annotations

import threading
import time
from collections.abc import Iterator

import httpx
import pytest
from werkzeug.serving import make_server

from tests.fixtures.target_app import create_app


@pytest.fixture(scope="session")
def live_target() -> Iterator[str]:
    app = create_app()
    server = make_server("127.0.0.1", 5055, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # Wait for liveness
    for _ in range(50):
        try:
            httpx.get("http://127.0.0.1:5055/echo?q=1", timeout=0.5)
            break
        except Exception:
            time.sleep(0.1)
    else:
        pytest.fail("fixture target did not start")
    yield "http://127.0.0.1:5055"
    server.shutdown()
    thread.join(timeout=2)
```

- [ ] **Step 2: Write `tests/integration/test_browser_only.py`**

```python
"""Real Chrome + real fixture target; requires chromium on PATH."""
from __future__ import annotations

import shutil
import tempfile

import pytest

from browser_mcp.tools import BrowserSession


pytestmark = pytest.mark.integration


def _chrome_available() -> bool:
    return any(shutil.which(n) for n in ("chromium", "chromium-browser", "google-chrome", "chrome"))


@pytest.mark.skipif(not _chrome_available(), reason="no Chrome binary on PATH")
@pytest.mark.asyncio
async def test_launch_navigate_snapshot(live_target: str):
    with tempfile.TemporaryDirectory() as udd:
        sess = BrowserSession(
            chrome_candidates=["chromium", "chromium-browser", "google-chrome", "chrome"],
            cdp_port=9222,
            default_proxy=None,
            user_data_dir_root=udd,
            navigation_timeout_s=15,
        )
        try:
            r_launch = await sess.launch(headless=True, proxy=None)
            assert r_launch["ok"] is True, r_launch
            r_nav = await sess.navigate(f"{live_target}/search?q=<script>alert(1)</script>")
            assert r_nav["ok"] is True, r_nav
            r_snap = await sess.snapshot()
            assert r_snap["ok"] is True
            # DOM serialization is massive; just assert presence.
            import json as _j
            blob = _j.dumps(r_snap["data"])
            assert "script" in blob.lower()
        finally:
            await sess.close()
```

- [ ] **Step 3: Run the integration test (opt-in)**

```bash
cd /home/kali/Web-MCP
source .venv/bin/activate
pytest -m integration tests/integration/test_browser_only.py -v
```
Expected: PASS if chromium is installed; SKIPPED if not.

If chromium is missing:
```bash
sudo apt-get install -y chromium
```

- [ ] **Step 4: Commit**

```bash
git add tests/integration/
git commit -m "test(integration): browser-only E2E against live Flask fixture"
```

---

### Task 6: Integration test — browser → Burp → fixture chain

**Files:**
- Create: `tests/integration/test_chain_browser_burp.py`

- [ ] **Step 1: Write the integration test**

```python
"""Chain test: browser drives through Burp (user-launched) → fixture target.

Preconditions (documented in README, enforced via a liveness check):
1. Burp Suite is running with the bridge extension loaded.
2. `curl http://127.0.0.1:8775/meta` succeeds.
3. Burp proxy is listening on 127.0.0.1:8080.
"""
from __future__ import annotations

import shutil
import tempfile

import httpx
import pytest

from browser_mcp.tools import BrowserSession
from common.burp_client import BurpClient, BurpUnavailable


pytestmark = pytest.mark.integration


def _chrome_available() -> bool:
    return any(shutil.which(n) for n in ("chromium", "chromium-browser", "google-chrome", "chrome"))


def _bridge_available() -> bool:
    try:
        httpx.get("http://127.0.0.1:8775/meta", timeout=0.5)
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _chrome_available(), reason="no Chrome binary on PATH")
@pytest.mark.skipif(not _bridge_available(),
                    reason="burp-mcp-bridge not responding on 127.0.0.1:8775 — launch Burp + load extension")
@pytest.mark.asyncio
async def test_browser_through_burp_to_fixture(live_target: str):
    # Must accept Burp's untrusted CA for https targets; our fixture is http://, so fine.
    with tempfile.TemporaryDirectory() as udd:
        sess = BrowserSession(
            chrome_candidates=["chromium", "chromium-browser", "google-chrome", "chrome"],
            cdp_port=9222,
            default_proxy="127.0.0.1:8080",
            user_data_dir_root=udd,
            navigation_timeout_s=15,
        )
        try:
            assert (await sess.launch(headless=True))["ok"]
            marker = "xss-probe-9c2f"
            assert (await sess.navigate(f"{live_target}/search?q={marker}"))["ok"]
        finally:
            await sess.close()

        # Verify Burp saw the request
        async with BurpClient("http://127.0.0.1:8775") as c:
            history = await c.proxy_history(contains=marker, limit=20)
        entries = history.get("entries", [])
        assert any(marker in (e.get("url") or "") for e in entries), \
            f"probe marker not found in proxy history; entries={entries}"
```

- [ ] **Step 2: Run the chain test (opt-in; requires Burp running)**

Prerequisites checklist before invocation:
- Burp launched, bridge jar loaded, `curl http://127.0.0.1:8775/meta` succeeds.
- Burp proxy listening on `127.0.0.1:8080` (the default).

```bash
pytest -m integration tests/integration/test_chain_browser_burp.py -v
```
Expected: PASS if all prereqs met; SKIPPED if chromium or bridge not up.

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_chain_browser_burp.py
git commit -m "test(integration): browser → Burp → fixture chain verification"
```

---

### Task 7: Top-level README with full setup + smoke-test checklist

**Files:**
- Modify: `/home/kali/Web-MCP/README.md`

- [ ] **Step 1: Rewrite `README.md`** (full setup guide)

```markdown
# Web-MCP

Four-MCP Python stack for AI-driven web application security auditing and PoC
validation. Built to run on a tester's workstation, registered with Claude Code
via stdio.

- **browser-mcp** — CDP-driven browser (no Node.js, no Playwright)
- **burp-mcp** — Burp Suite via a Kotlin Montoya extension + HTTP bridge
- **parley-mcp** — user's TCP/TLS MiTM proxy (vendored from upstream)
- **github-mcp** — user's source-aware GitHub MCP with secret redaction (vendored)

See `docs/superpowers/specs/2026-04-16-web-mcp-stack-design.md` for the design.

## Prerequisites

- Python 3.13
- Burp Suite (Community or Professional) on PATH
- JDK 17+ and Gradle (for building the burp-mcp Kotlin extension)
- Chromium or Chrome (for browser-mcp)
- A GitHub Personal Access Token with at least `repo` and `security_events`
  scopes (for github-mcp). Optionally `GHE_TOKEN` for GitHub Enterprise.

## Setup

```bash
cd /home/kali/Web-MCP
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e ".[dev]"
pip install -e MCPs/browser-mcp
pip install -e MCPs/burp-mcp
# Parley and github upstream deps:
pip install -r MCPs/parley-mcp/requirements.txt
pip install -r MCPs/github-mcp/MCPs/libs/mcp_armor/requirements.txt || true
[ -f MCPs/github-mcp/requirements.txt ] && pip install -r MCPs/github-mcp/requirements.txt

# Build the Burp Kotlin extension
cd MCPs/burp-mcp/burp-ext
gradle shadowJar
# Produces build/libs/burp-mcp-bridge.jar
cd /home/kali/Web-MCP
```

## Register with Claude Code

1. Copy `claude_config.example.json` to `claude_config.json`.
2. Replace `"${GITHUB_TOKEN}"` with your real PAT (this file is gitignored).
3. Merge the `mcpServers` block into your Claude Code user settings
   (`~/.claude/settings.json` under `mcpServers`), or point Claude Code at the
   file per your version's convention.
4. Restart Claude Code. Run `/mcp` — you should see all four as `connected`.

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
pytest -v                          # unit tests
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
- [ ] Claude Code prompt: *"Use github_search_code to find 'def login' in repo
      `gglessner/Parley-MCP` (or any repo you have access to)."* — github-mcp
      returns results with any secrets redacted by MCP Armor.
- [ ] Claude Code prompt: *"Use parley tools to list available parley modules."*
      — Parley responds with its module list.

## Project layout

```
Web-MCP/
├── common/            # shared Python lib (config, logging, CDP, BurpClient, MCP base)
├── MCPs/
│   ├── browser-mcp/   # CDP-driven browser MCP (our code)
│   ├── burp-mcp/      # Kotlin Burp extension + Python MCP wrapper (our code)
│   ├── parley-mcp/    # upstream clone (UPSTREAM.txt records pinned commit)
│   └── github-mcp/    # upstream clone (UPSTREAM.txt records pinned commit)
├── docs/superpowers/  # specs + plans (this directory)
├── tests/
│   ├── integration/   # @pytest.mark.integration (opt-in)
│   └── fixtures/      # Flask target app (intentionally vulnerable, test-only)
├── logs/              # per-MCP JSON logs
├── config.toml        # shared config (paths, ports, proxy default)
├── config.local.toml  # per-tester overrides (gitignored; optional)
└── claude_config.example.json  # Claude Code registration snippet
```

## Updating vendored upstreams

```bash
cd MCPs/parley-mcp  # or MCPs/github-mcp
git clone https://github.com/gglessner/Parley-MCP.git /tmp/parley-latest
rm -rf ./*
cp -r /tmp/parley-latest/* .
UPSTREAM=$(cd /tmp/parley-latest && git rev-parse HEAD)
echo "upstream: https://github.com/gglessner/Parley-MCP" > UPSTREAM.txt
echo "pinned_commit: $UPSTREAM" >> UPSTREAM.txt
date -u +"pinned_at: %Y-%m-%dT%H:%M:%SZ" >> UPSTREAM.txt
cd /home/kali/Web-MCP
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
- **github-mcp startup error** — `GITHUB_TOKEN` not exported to Claude Code's
  env for the MCP. Use the `env` block in `claude_config.json`.
- **Integration tests skipped** — expected when chromium or Burp isn't running.
  Skip reasons are printed by pytest.

## License

Our code: consult repository LICENSE file.
Vendored upstreams (`parley-mcp`, `github-mcp`): GPL-3.0 per upstream.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: full setup, smoke checklist, and update instructions"
```

---

### Task 8: Final verification pass

**Files:** (no files; validation only)

- [ ] **Step 1: Clean install check**

```bash
cd /home/kali/Web-MCP
# Sanity: ensure everything still imports cleanly and tests pass
source .venv/bin/activate
python -c "import common.config, common.logging, common.cdp, common.mcp_base, common.burp_client; print('common ok')"
python -c "import browser_mcp; import burp_mcp; print('MCPs ok')"
pytest -v
```
Expected: all unit tests pass. Integration tests not run (no `-m integration`).

- [ ] **Step 2: Run integration tests with available preconditions**

```bash
# Start fixture (other shell): python tests/fixtures/target_app.py
pytest -m integration -v
```
Expected: tests requiring Chrome/Burp pass if prereqs present, skip otherwise with clear messages.

- [ ] **Step 3: Register with Claude Code and run the smoke checklist**

Follow the checklist in `README.md`. Any failure → investigate root cause; do NOT destructively reset state.

- [ ] **Step 4: Final commit (if anything drifted)**

```bash
git status
# If there are forgotten files or doc fixes:
# git add <files>
# git commit -m "chore: post-verification tidy-up"
```

---

## Plan-end verification

- [ ] `MCPs/parley-mcp/UPSTREAM.txt` and `MCPs/github-mcp/UPSTREAM.txt` record pinned commits.
- [ ] All four MCPs appear `connected` under Claude Code `/mcp` after config registration.
- [ ] `curl http://127.0.0.1:8775/meta` succeeds when Burp is running.
- [ ] `pytest` passes; `pytest -m integration` passes with chromium + Burp up.
- [ ] The five smoke-checklist prompts in README succeed end-to-end.
- [ ] A source-informed workflow completes: Claude reads a file with `github_get_file_contents`, derives a test input, drives `browser_navigate` through Burp, and correlates the result against `burp_proxy_history`.
