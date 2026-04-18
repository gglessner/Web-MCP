# Engagement Layer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Repo note:** this machine does not use git commits (see project memory). Commit steps are omitted; just write files.

**Goal:** Add per-engagement scope enforcement, credential placeholder substitution + redaction, multi-identity request sending, and an OOB callback receiver to Web-MCP, driven by a single `engagement.toml`.

**Architecture:** A new `common/engagement.py` loads `engagement.toml`. `common/credstore.py` wraps a vendored `common/mcp_armor/` to expand `{{CRED:…}}` placeholders on tool inputs and redact credential/identity literals on tool outputs. Both MCP servers' `call_tool` chokepoints become `expand → scope-check → dispatch → redact`. browser-mcp gains `browser_capture_identity`/`browser_apply_identity`; burp-mcp gains `as_identity` on send tools and `oob_get_payload`/`oob_poll` backed by `common/oob.py` (interactsh).

**Tech Stack:** Python 3.13, `tomllib`/`tomli_w`, existing `mcp_armor` (regex ContentFilter), `subprocess` for interactsh-client, existing CDP/Burp-bridge plumbing.

**Spec:** `docs/superpowers/specs/2026-04-18-engagement-layer-design.md`

---

## File map

| New | Purpose |
|---|---|
| `common/engagement.py` | `Engagement` — load TOML, `in_scope()`, `write_identity()`, accessors |
| `common/credstore.py` | `CredStore` — `expand()` placeholders in, `filter()` redaction out |
| `common/mcp_armor/` | Vendored from `MCPs/github-mcp/MCPs/libs/mcp_armor/` + `UPSTREAM.txt` |
| `common/oob.py` | `OOBReceiver` — interactsh subprocess wrapper; selfhost stub |
| `engagement.example.toml` | Template testers copy to `engagement.toml` |
| `docs/engagement-setup.md` | Tester walkthrough |
| `tests/test_common_engagement.py` | |
| `tests/test_common_credstore.py` | |
| `tests/test_common_oob.py` | |
| `MCPs/browser-mcp/tests/test_tool_identity.py` | |
| `MCPs/burp-mcp/tests/test_as_identity.py` | |
| `MCPs/burp-mcp/tests/test_oob_tools.py` | |

| Modified | Change |
|---|---|
| `common/mcp_base.py` | `ErrorCode.OUT_OF_SCOPE` |
| `pyproject.toml` | add `tomli_w` dep |
| `.gitignore` | `engagement.toml` |
| `MCPs/browser-mcp/browser_mcp/server.py` | chokepoint pipeline; register 2 new tools |
| `MCPs/browser-mcp/browser_mcp/tools.py` | track `current_host`; `capture_identity`, `apply_identity` |
| `MCPs/burp-mcp/burp_mcp/server.py` | chokepoint pipeline; register `as_identity` + 2 oob tools |
| `MCPs/burp-mcp/burp_mcp/tool_handlers.py` | `as_identity` header injection; `oob_*` dispatch |
| `README.md` | link to `docs/engagement-setup.md` |
| `.claude/skills/methodology-scoping/SKILL.md` | add `engagement.toml` step |
| `.claude/skills/testing-{ssrf,xxe,command-injection,sqli}/SKILL.md` | blind-detection subsection |

---

### Task 1: Vendor `mcp_armor` into `common/`

**Files:** create `common/mcp_armor/` (copy), `common/mcp_armor/UPSTREAM.txt`

- [ ] **Step 1:** Copy the package.

```bash
cp -r MCPs/github-mcp/MCPs/libs/mcp_armor common/mcp_armor
cat > common/mcp_armor/UPSTREAM.txt <<'EOF'
upstream: https://github.com/gglessner/MCP-Armor
vendored_from: MCPs/github-mcp/MCPs/libs/mcp_armor (GitHub-MCP@d2462f8)
pinned_at: 2026-04-18
EOF
```

- [ ] **Step 2:** Verify it imports from the new location.

```bash
python3 -c "from common.mcp_armor import ContentFilter, FilterConfig, FilterPattern; print('ok')"
```
Expected: `ok`

---

### Task 2: `ErrorCode.OUT_OF_SCOPE` + `tomli_w` dep + `.gitignore`

**Files:** modify `common/mcp_base.py`, `pyproject.toml`, `.gitignore`

- [ ] **Step 1:** Read `common/mcp_base.py`, add `OUT_OF_SCOPE = "OUT_OF_SCOPE"` to the `ErrorCode` enum (alongside `INTERNAL`, `BAD_INPUT`, etc.).

- [ ] **Step 2:** Add `tomli_w>=1.0` to `[project].dependencies` in `pyproject.toml`; run `pip install tomli_w`.

- [ ] **Step 3:** Append `engagement.toml` to `.gitignore`.

- [ ] **Step 4:** Verify.

```bash
python3 -c "from common.mcp_base import ErrorCode; print(ErrorCode.OUT_OF_SCOPE)"
```
Expected: `ErrorCode.OUT_OF_SCOPE`

---

### Task 3: `common/engagement.py` — load + `in_scope()`

**Files:** create `tests/test_common_engagement.py`, `common/engagement.py`

- [ ] **Step 1: Write failing tests.**

```python
# tests/test_common_engagement.py
import textwrap
from pathlib import Path
import pytest
from common.engagement import Engagement


def write(tmp_path, body):
    p = tmp_path / "engagement.toml"
    p.write_text(textwrap.dedent(body))
    return p


def test_load_absent_returns_none(tmp_path):
    assert Engagement.load(tmp_path / "nope.toml") is None


def test_in_scope_exact_wildcard_cidr(tmp_path):
    p = write(tmp_path, """
        [scope]
        hosts = ["app.acme.com", "*.api.acme.com", "10.20.0.0/16"]
    """)
    e = Engagement.load(p)
    assert e.in_scope("app.acme.com")
    assert e.in_scope("https://app.acme.com/login")
    assert e.in_scope("v2.api.acme.com")
    assert not e.in_scope("api.acme.com")          # wildcard requires a sub-label
    assert e.in_scope("10.20.5.1")
    assert not e.in_scope("10.21.0.1")
    assert not e.in_scope("evil.com")


def test_empty_hosts_fail_closed(tmp_path):
    p = write(tmp_path, "[scope]\nhosts = []\n")
    e = Engagement.load(p)
    assert not e.in_scope("anything.com")


def test_credentials_and_identities_accessors(tmp_path):
    p = write(tmp_path, """
        [credentials.user1]
        username = "alice"
        password = "s3cr3t"
        [identities.user1]
        cookies = [{name="sid", value="abc", domain="app.acme.com"}]
        headers = {Authorization = "Bearer xyz"}
    """)
    e = Engagement.load(p)
    assert e.credential("user1", "password") == "s3cr3t"
    assert e.credential("user1", "nope") is None
    ident = e.identity("user1")
    assert ident["cookies"][0]["value"] == "abc"
    assert ident["headers"]["Authorization"] == "Bearer xyz"
    assert e.identity("ghost") is None
```

- [ ] **Step 2: Run — expect FAIL (module not found).**

```bash
python -m pytest tests/test_common_engagement.py -q
```

- [ ] **Step 3: Implement.**

```python
# common/engagement.py
from __future__ import annotations

import ipaddress
import tomllib
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class Engagement:
    def __init__(self, path: Path, data: dict[str, Any]):
        self._path = Path(path)
        self._data = data
        self._scope = [str(h) for h in data.get("scope", {}).get("hosts", [])]

    @classmethod
    def load(cls, path: str | Path = "engagement.toml") -> "Engagement | None":
        p = Path(path)
        if not p.exists():
            return None
        with p.open("rb") as fh:
            return cls(p, tomllib.load(fh))

    # ── scope ────────────────────────────────────────────────────────
    @staticmethod
    def _hostname(host_or_url: str) -> str:
        if "://" in host_or_url:
            return urlparse(host_or_url).hostname or ""
        return host_or_url.split(":", 1)[0]

    def in_scope(self, host_or_url: str) -> bool:
        host = self._hostname(host_or_url)
        if not host:
            return False
        for entry in self._scope:
            if entry.startswith("*."):
                if host.endswith(entry[1:]) and host != entry[2:]:
                    return True
            elif "/" in entry:
                try:
                    if ipaddress.ip_address(host) in ipaddress.ip_network(entry, strict=False):
                        return True
                except ValueError:
                    pass
            elif host == entry:
                return True
        return False

    def scope_hosts(self) -> list[str]:
        return list(self._scope)

    # ── credentials / identities ─────────────────────────────────────
    def credentials(self) -> dict[str, dict[str, str]]:
        return {k: dict(v) for k, v in self._data.get("credentials", {}).items()}

    def credential(self, name: str, field: str) -> str | None:
        return self._data.get("credentials", {}).get(name, {}).get(field)

    def identities(self) -> dict[str, dict[str, Any]]:
        return {k: dict(v) for k, v in self._data.get("identities", {}).items()}

    def identity(self, name: str) -> dict[str, Any] | None:
        ident = self._data.get("identities", {}).get(name)
        return dict(ident) if ident is not None else None

    def oob_provider(self) -> str:
        return self._data.get("oob", {}).get("provider", "interactsh")
```

- [ ] **Step 4: Run — expect PASS.**

```bash
python -m pytest tests/test_common_engagement.py -q
```

---

### Task 4: `Engagement.write_identity()` — atomic TOML update

**Files:** modify `common/engagement.py`, `tests/test_common_engagement.py`

- [ ] **Step 1: Add failing test.**

```python
# append to tests/test_common_engagement.py

def test_write_identity_roundtrip(tmp_path):
    p = write(tmp_path, """
        [scope]
        hosts = ["app.acme.com"]
        [credentials.user1]
        username = "alice"
    """)
    e = Engagement.load(p)
    e.write_identity("user1",
        cookies=[{"name": "sid", "value": "NEW", "domain": "app.acme.com"}],
        headers={"Authorization": "Bearer NEW"})
    e2 = Engagement.load(p)
    assert e2.identity("user1")["cookies"][0]["value"] == "NEW"
    assert e2.identity("user1")["headers"]["Authorization"] == "Bearer NEW"
    assert "captured_at" in e2.identity("user1")
    # creds untouched
    assert e2.credential("user1", "username") == "alice"
```

- [ ] **Step 2: Run — expect FAIL.**

- [ ] **Step 3: Implement (append to `common/engagement.py`).**

```python
import os
import tempfile
from datetime import datetime, timezone
import tomli_w


    def write_identity(self, name: str, *, cookies: list[dict], headers: dict[str, str]) -> None:
        idents = self._data.setdefault("identities", {})
        idents[name] = {
            "cookies": cookies,
            "headers": headers,
            "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        fd, tmp = tempfile.mkstemp(dir=self._path.parent, prefix=".engagement-", suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as fh:
                tomli_w.dump(self._data, fh)
            os.replace(tmp, self._path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
```

- [ ] **Step 4: Run — expect PASS.**

---

### Task 5: `common/credstore.py` — expand + redact

**Files:** create `tests/test_common_credstore.py`, `common/credstore.py`

- [ ] **Step 1: Write failing tests.**

```python
# tests/test_common_credstore.py
import base64
import textwrap
import pytest
from common.engagement import Engagement
from common.credstore import CredStore, UnknownPlaceholder


def make(tmp_path):
    p = tmp_path / "engagement.toml"
    p.write_text(textwrap.dedent("""
        [credentials.user1]
        username = "alice@acme.com"
        password = "p@ss/w0rd"
        [identities.user1]
        cookies = [{name="sid", value="SESSIONABC", domain="x"}]
        headers = {Authorization = "Bearer TOKEN123"}
    """))
    return CredStore(Engagement.load(p))


def test_expand_string_and_nested(tmp_path):
    cs = make(tmp_path)
    assert cs.expand("u={{CRED:user1.username}}") == "u=alice@acme.com"
    out = cs.expand({"a": ["{{CRED:user1.password}}", 1], "b": {"c": "{{CRED:user1.username}}"}})
    assert out == {"a": ["p@ss/w0rd", 1], "b": {"c": "alice@acme.com"}}


def test_expand_unknown_raises(tmp_path):
    cs = make(tmp_path)
    with pytest.raises(UnknownPlaceholder):
        cs.expand("{{CRED:ghost.password}}")


def test_expand_raw_base64_roundtrip(tmp_path):
    cs = make(tmp_path)
    raw = base64.b64encode(b"POST / HTTP/1.1\r\npass={{CRED:user1.password}}\r\n").decode()
    out = cs.expand({"raw_base64": raw})
    decoded = base64.b64decode(out["raw_base64"])
    assert b"pass=p@ss/w0rd" in decoded


def test_filter_redacts_cred_and_identity(tmp_path):
    cs = make(tmp_path)
    out = cs.filter({"body": "pw=p@ss/w0rd sid=SESSIONABC tok=Bearer TOKEN123"})
    assert "p@ss/w0rd" not in out["body"]
    assert "SESSIONABC" not in out["body"]
    assert "TOKEN123" not in out["body"]
    assert "[REDACTED:CRED:user1.password]" in out["body"]
    assert "[REDACTED:IDENT:user1.cookie]" in out["body"]
    assert "[REDACTED:IDENT:user1.header]" in out["body"]


def test_no_engagement_is_noop():
    cs = CredStore(None)
    assert cs.expand({"x": "{{CRED:a.b}}"}) == {"x": "{{CRED:a.b}}"}
    assert cs.filter({"x": "secret"}) == {"x": "secret"}
```

- [ ] **Step 2: Run — expect FAIL.**

- [ ] **Step 3: Implement.**

```python
# common/credstore.py
from __future__ import annotations

import base64
import re
from typing import Any

from common.engagement import Engagement
from common.mcp_armor import ContentFilter, FilterConfig, FilterPattern


_PLACEHOLDER = re.compile(r"\{\{CRED:([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)\}\}")


class UnknownPlaceholder(ValueError):
    pass


class CredStore:
    def __init__(self, engagement: Engagement | None):
        self._eng = engagement
        self._filter: ContentFilter | None = None
        if engagement is not None:
            self._rebuild_filter()

    # ── expansion (tool inputs) ──────────────────────────────────────
    def expand(self, obj: Any) -> Any:
        if self._eng is None:
            return obj
        return self._walk(obj)

    def _walk(self, obj: Any) -> Any:
        if isinstance(obj, str):
            return self._expand_str(obj)
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                if k == "raw_base64" and isinstance(v, str):
                    try:
                        decoded = base64.b64decode(v).decode("latin-1")
                        out[k] = base64.b64encode(
                            self._expand_str(decoded).encode("latin-1")
                        ).decode("ascii")
                        continue
                    except Exception:
                        pass
                out[k] = self._walk(v)
            return out
        if isinstance(obj, list):
            return [self._walk(x) for x in obj]
        return obj

    def _expand_str(self, s: str) -> str:
        def sub(m: re.Match) -> str:
            name, field = m.group(1), m.group(2)
            val = self._eng.credential(name, field)
            if val is None:
                raise UnknownPlaceholder(f"{{{{CRED:{name}.{field}}}}}")
            return str(val)
        return _PLACEHOLDER.sub(sub, s)

    # ── redaction (tool outputs) ─────────────────────────────────────
    def _rebuild_filter(self) -> None:
        patterns: list[FilterPattern] = []
        for cname, fields in self._eng.credentials().items():
            for fname, val in fields.items():
                if not val:
                    continue
                patterns.append(FilterPattern(
                    name=f"cred.{cname}.{fname}",
                    pattern=re.escape(str(val)),
                    replacement=f"[REDACTED:CRED:{cname}.{fname}]",
                    enabled=True,
                ))
        for iname, ident in self._eng.identities().items():
            for c in ident.get("cookies", []):
                v = c.get("value")
                if v:
                    patterns.append(FilterPattern(
                        name=f"ident.{iname}.cookie",
                        pattern=re.escape(str(v)),
                        replacement=f"[REDACTED:IDENT:{iname}.cookie]",
                        enabled=True,
                    ))
            for v in (ident.get("headers") or {}).values():
                if v:
                    patterns.append(FilterPattern(
                        name=f"ident.{iname}.header",
                        pattern=re.escape(str(v)),
                        replacement=f"[REDACTED:IDENT:{iname}.header]",
                        enabled=True,
                    ))
        self._filter = ContentFilter(FilterConfig(patterns=patterns, dry_run=False))

    def refresh_identities(self) -> None:
        if self._eng is not None:
            self._rebuild_filter()

    def filter(self, obj: Any) -> Any:
        if self._filter is None:
            return obj
        filtered, _ = self._filter.filter(obj)
        return filtered
```

- [ ] **Step 4: Run — expect PASS.** If `FilterConfig`/`FilterPattern` constructor signatures differ from above, read `common/mcp_armor/config.py` and adjust the keyword names — do **not** change `mcp_armor` itself.

```bash
python -m pytest tests/test_common_credstore.py -q
```

---

### Task 6: `common/oob.py` — interactsh wrapper

**Files:** create `tests/test_common_oob.py`, `common/oob.py`

- [ ] **Step 1: Write failing tests** (mock the subprocess; no real network).

```python
# tests/test_common_oob.py
import json
from common.oob import OOBReceiver


class FakeProc:
    def __init__(self, lines):
        import io
        self.stdout = io.StringIO("\n".join(lines) + "\n")
        self.returncode = None
    def poll(self):
        return None
    def terminate(self):
        pass


def test_parses_payload_and_interactions(monkeypatch):
    lines = [
        json.dumps({"type": "payload", "domain": "abc123.oast.fun"}),
        json.dumps({"type": "interaction", "protocol": "dns",
                    "remote_address": "1.2.3.4", "timestamp": "t1", "raw": "..."}),
        json.dumps({"type": "interaction", "protocol": "http",
                    "remote_address": "5.6.7.8", "timestamp": "t2", "raw": "GET /"}),
    ]
    monkeypatch.setattr("common.oob.OOBReceiver._spawn", lambda self: FakeProc(lines))
    r = OOBReceiver(provider="interactsh")
    p = r.get_payload()
    assert p["domain"] == "abc123.oast.fun"
    assert p["url"] == "http://abc123.oast.fun/"
    inter = r.poll(since_id=0)
    assert len(inter) == 2
    assert inter[0]["protocol"] == "dns" and inter[0]["id"] == 1
    assert inter[1]["protocol"] == "http" and inter[1]["id"] == 2
    assert r.poll(since_id=2) == []


def test_selfhost_not_implemented_yet():
    import pytest
    with pytest.raises(NotImplementedError):
        OOBReceiver(provider="selfhost").get_payload()
```

- [ ] **Step 2: Run — expect FAIL.**

- [ ] **Step 3: Implement.**

```python
# common/oob.py
from __future__ import annotations

import json
import shutil
import subprocess
import threading
from typing import Any


class OOBReceiver:
    def __init__(self, provider: str = "interactsh"):
        self._provider = provider
        self._proc = None
        self._payload: dict[str, str] | None = None
        self._interactions: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._reader: threading.Thread | None = None

    def _spawn(self):
        binary = shutil.which("interactsh-client")
        if not binary:
            raise RuntimeError("interactsh-client not on PATH")
        return subprocess.Popen(
            [binary, "-json", "-v"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        )

    def _ensure_started(self) -> None:
        if self._provider != "interactsh":
            raise NotImplementedError(f"oob provider {self._provider!r} not implemented")
        if self._proc is not None:
            return
        self._proc = self._spawn()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _read_loop(self) -> None:
        for line in self._proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            with self._lock:
                if msg.get("type") == "payload" or "unique-id" in msg or (
                    msg.get("domain") and self._payload is None
                ):
                    dom = msg.get("domain") or msg.get("data") or msg.get("unique-id")
                    if dom:
                        self._payload = {"domain": dom, "url": f"http://{dom}/"}
                elif msg.get("protocol"):
                    self._interactions.append({
                        "id": len(self._interactions) + 1,
                        "protocol": msg.get("protocol"),
                        "remote_addr": msg.get("remote_address") or msg.get("remote-address"),
                        "timestamp": msg.get("timestamp"),
                        "raw_request": msg.get("raw") or msg.get("raw-request"),
                    })

    def get_payload(self, timeout_s: float = 10.0) -> dict[str, str]:
        self._ensure_started()
        import time
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            with self._lock:
                if self._payload:
                    return dict(self._payload)
            time.sleep(0.1)
        raise TimeoutError("interactsh-client did not emit a payload domain")

    def poll(self, since_id: int = 0) -> list[dict[str, Any]]:
        self._ensure_started()
        with self._lock:
            return [i for i in self._interactions if i["id"] > since_id]

    def close(self) -> None:
        if self._proc:
            self._proc.terminate()
```

- [ ] **Step 4: Run — expect PASS.**

```bash
python -m pytest tests/test_common_oob.py -q
```

---

### Task 7: browser-mcp — track `current_host`; add `capture_identity` / `apply_identity`

**Files:** modify `MCPs/browser-mcp/browser_mcp/tools.py`; create `MCPs/browser-mcp/tests/test_tool_identity.py`

- [ ] **Step 1: Write failing tests.**

```python
# MCPs/browser-mcp/tests/test_tool_identity.py
import textwrap
from pathlib import Path
from unittest.mock import MagicMock
import pytest
from browser_mcp.tools import BrowserSession
from common.engagement import Engagement


@pytest.mark.asyncio
async def test_capture_identity_writes_engagement(monkeypatch, tmp_path):
    eng_path = tmp_path / "engagement.toml"
    eng_path.write_text(textwrap.dedent("""
        [scope]
        hosts = ["app.acme.com"]
    """))
    eng = Engagement.load(eng_path)

    sess = BrowserSession(
        chrome_candidates=["x"], cdp_port=0, default_proxy=None,
        user_data_dir_root=str(tmp_path), engagement=eng,
    )
    sess._current_host = "app.acme.com"

    class FakeCDP:
        async def send(self, method, params=None):
            if method == "Network.getAllCookies":
                return {"cookies": [
                    {"name": "sid", "value": "ABC", "domain": "app.acme.com"},
                    {"name": "x", "value": "Y", "domain": "evil.com"},
                ]}
            return {}
    sess._cdp = FakeCDP()
    sess._network_log = [
        {"request": {"url": "https://app.acme.com/api",
                     "headers": {"Authorization": "Bearer TOK"}}},
    ]

    result = await sess.capture_identity("user1")
    assert result["ok"]
    e2 = Engagement.load(eng_path)
    ident = e2.identity("user1")
    assert ident["cookies"] == [{"name": "sid", "value": "ABC", "domain": "app.acme.com"}]
    assert ident["headers"] == {"Authorization": "Bearer TOK"}


@pytest.mark.asyncio
async def test_apply_identity_sets_cookies(monkeypatch, tmp_path):
    eng_path = tmp_path / "engagement.toml"
    eng_path.write_text(textwrap.dedent("""
        [scope]
        hosts = ["app.acme.com"]
        [identities.user1]
        cookies = [{name="sid", value="ABC", domain="app.acme.com"}]
        headers = {}
    """))
    eng = Engagement.load(eng_path)
    sess = BrowserSession(
        chrome_candidates=["x"], cdp_port=0, default_proxy=None,
        user_data_dir_root=str(tmp_path), engagement=eng,
    )
    sent = []
    class FakeCDP:
        async def send(self, method, params=None):
            sent.append((method, params)); return {}
    sess._cdp = FakeCDP()
    r = await sess.apply_identity("user1")
    assert r["ok"]
    assert ("Network.setCookies", {"cookies": [
        {"name": "sid", "value": "ABC", "domain": "app.acme.com"}
    ]}) in sent
```

- [ ] **Step 2: Run — expect FAIL.**

- [ ] **Step 3: Modify `BrowserSession.__init__`** to accept `engagement: Engagement | None = None`, store `self._engagement = engagement`, and initialise `self._current_host: str | None = None`. In `navigate()`, after a successful load, set `self._current_host = urlparse(url).hostname`. Confirm there is a `self._network_log` list that `Network.requestWillBeSent` events append to (it already exists for `browser_network_log`); if the entries don't carry request headers, extend the event handler to store `params["request"]` so `capture_identity` can read `Authorization`.

- [ ] **Step 4: Add the two methods to `BrowserSession`.**

```python
    async def capture_identity(self, name: str) -> dict:
        if self._engagement is None:
            return error_envelope(ErrorCode.BAD_INPUT, "no engagement.toml loaded")
        if self._cdp is None:
            return error_envelope(ErrorCode.TARGET_NOT_ATTACHED, "browser not launched")
        all_cookies = (await self._cdp.send("Network.getAllCookies")).get("cookies", [])
        cookies = [
            {"name": c["name"], "value": c["value"], "domain": c["domain"]}
            for c in all_cookies
            if self._engagement.in_scope(c.get("domain", "").lstrip("."))
        ]
        headers: dict[str, str] = {}
        for entry in reversed(self._network_log):
            req = entry.get("request", {})
            if self._engagement.in_scope(req.get("url", "")):
                auth = (req.get("headers") or {}).get("Authorization")
                if auth:
                    headers["Authorization"] = auth
                break
        self._engagement.write_identity(name, cookies=cookies, headers=headers)
        return ok_envelope({"name": name, "cookies": len(cookies),
                            "headers": list(headers), "captured_at": "now"})

    async def apply_identity(self, name: str) -> dict:
        if self._engagement is None:
            return error_envelope(ErrorCode.BAD_INPUT, "no engagement.toml loaded")
        ident = self._engagement.identity(name)
        if ident is None:
            return error_envelope(ErrorCode.BAD_INPUT, f"unknown identity {name!r}")
        if self._cdp is None:
            return error_envelope(ErrorCode.TARGET_NOT_ATTACHED, "browser not launched")
        await self._cdp.send("Network.setCookies", {"cookies": ident.get("cookies", [])})
        return ok_envelope({"name": name, "cookies": len(ident.get("cookies", []))})
```

Add the necessary imports at the top of `tools.py`: `from urllib.parse import urlparse` and `from common.engagement import Engagement` (the latter only for the type hint; guard with `TYPE_CHECKING` if you prefer).

- [ ] **Step 5: Run — expect PASS.**

```bash
python -m pytest MCPs/browser-mcp/tests/test_tool_identity.py -q
```

---

### Task 8: burp-mcp — `as_identity` header injection

**Files:** modify `MCPs/burp-mcp/burp_mcp/tool_handlers.py`; create `MCPs/burp-mcp/tests/test_as_identity.py`

- [ ] **Step 1: Write failing test.**

```python
# MCPs/burp-mcp/tests/test_as_identity.py
import base64
import textwrap
import httpx
import pytest
import respx
from common.engagement import Engagement
from burp_mcp.tool_handlers import handle


@pytest.mark.asyncio
async def test_http_send_as_identity_injects_cookie_and_header(tmp_path):
    p = tmp_path / "engagement.toml"
    p.write_text(textwrap.dedent("""
        [scope]
        hosts = ["app.acme.com"]
        [identities.user1]
        cookies = [{name="sid", value="ABC", domain="app.acme.com"}]
        headers = {Authorization = "Bearer TOK"}
    """))
    eng = Engagement.load(p)

    raw = b"GET /x HTTP/1.1\r\nHost: app.acme.com\r\nCookie: old=1\r\n\r\n"
    captured = {}

    async with respx.mock(base_url="http://127.0.0.1:8775") as mock:
        def cap(request):
            captured["body"] = request.content
            return httpx.Response(200, json={"ok": True, "data": {"status": 200}})
        mock.post("/http/send").mock(side_effect=cap)

        r = await handle("burp_http_send",
            {"raw_base64": base64.b64encode(raw).decode(), "host": "app.acme.com",
             "port": 443, "as_identity": "user1"},
            bridge_url="http://127.0.0.1:8775", engagement=eng)
    assert r["ok"]
    import json as _json
    sent = base64.b64decode(_json.loads(captured["body"])["raw_base64"])
    assert b"Cookie: sid=ABC" in sent
    assert b"Authorization: Bearer TOK" in sent
    assert b"old=1" not in sent
```

- [ ] **Step 2: Run — expect FAIL.**

- [ ] **Step 3: Implement.** In `tool_handlers.py`:

1. Change `handle()` signature to accept `engagement: Engagement | None = None` (and `oob: "OOBReceiver | None" = None` for Task 9).
2. Add a helper:

```python
def _apply_identity(raw_b64: str, ident: dict) -> str:
    import base64
    raw = base64.b64decode(raw_b64)
    head, sep, body = raw.partition(b"\r\n\r\n")
    lines = head.split(b"\r\n")
    drop = {b"cookie"} | {h.lower().encode() for h in (ident.get("headers") or {})}
    kept = [lines[0]] + [
        ln for ln in lines[1:]
        if ln.split(b":", 1)[0].strip().lower() not in drop
    ]
    cookie = "; ".join(f"{c['name']}={c['value']}" for c in ident.get("cookies", []))
    if cookie:
        kept.append(f"Cookie: {cookie}".encode())
    for k, v in (ident.get("headers") or {}).items():
        kept.append(f"{k}: {v}".encode())
    return base64.b64encode(b"\r\n".join(kept) + sep + body).decode()
```

3. Before dispatching `burp_http_send` / `burp_repeater_send`:

```python
            if "as_identity" in args:
                if engagement is None:
                    return error_envelope(ErrorCode.BAD_INPUT, "as_identity requires engagement.toml")
                ident = engagement.identity(args["as_identity"])
                if ident is None:
                    return error_envelope(ErrorCode.BAD_INPUT,
                                          f"unknown identity {args['as_identity']!r}")
                args = {**args, "raw_base64": _apply_identity(args["raw_base64"], ident)}
                args.pop("as_identity")
```

- [ ] **Step 4: Run — expect PASS.**

---

### Task 9: burp-mcp — `oob_get_payload` / `oob_poll`

**Files:** modify `MCPs/burp-mcp/burp_mcp/tool_handlers.py`; create `MCPs/burp-mcp/tests/test_oob_tools.py`

- [ ] **Step 1: Write failing test.**

```python
# MCPs/burp-mcp/tests/test_oob_tools.py
import pytest
from burp_mcp.tool_handlers import handle


class FakeOOB:
    def get_payload(self):
        return {"domain": "abc.oast.fun", "url": "http://abc.oast.fun/"}
    def poll(self, since_id=0):
        return [{"id": 1, "protocol": "dns", "remote_addr": "1.2.3.4",
                 "timestamp": "t", "raw_request": ""}]


@pytest.mark.asyncio
async def test_oob_tools():
    oob = FakeOOB()
    r1 = await handle("oob_get_payload", {}, bridge_url="http://x", oob=oob)
    assert r1["data"]["domain"] == "abc.oast.fun"
    r2 = await handle("oob_poll", {"since_id": 0}, bridge_url="http://x", oob=oob)
    assert r2["data"][0]["protocol"] == "dns"
```

- [ ] **Step 2: Run — expect FAIL.**

- [ ] **Step 3: Implement.** In `tool_handlers.py` `handle()`, before the BurpClient block:

```python
        if tool == "oob_get_payload":
            if oob is None:
                return error_envelope(ErrorCode.INTERNAL, "OOB receiver not configured")
            return ok_envelope(oob.get_payload())
        if tool == "oob_poll":
            if oob is None:
                return error_envelope(ErrorCode.INTERNAL, "OOB receiver not configured")
            return ok_envelope(oob.poll(since_id=int(args.get("since_id", 0))))
```

- [ ] **Step 4: Run — expect PASS.**

---

### Task 10: browser-mcp `server.py` — chokepoint pipeline + register tools

**Files:** modify `MCPs/browser-mcp/browser_mcp/server.py`

- [ ] **Step 1:** At module setup (where `cfg`/`logger`/`session` are created), add:

```python
from common.engagement import Engagement
from common.credstore import CredStore, UnknownPlaceholder
from common.mcp_base import ErrorCode, error_envelope

engagement = Engagement.load(WORKSPACE / "engagement.toml")
credstore = CredStore(engagement)
session = BrowserSession(..., engagement=engagement)   # add kwarg
```

- [ ] **Step 2:** In `_tool_schemas()`, append:

```python
        Tool(name="browser_capture_identity",
             description="Capture in-scope cookies + Authorization header as a named identity in engagement.toml.",
             inputSchema={"type": "object", "required": ["name"],
                          "properties": {"name": {"type": "string"}}}),
        Tool(name="browser_apply_identity",
             description="Load a stored identity's cookies into the browser session.",
             inputSchema={"type": "object", "required": ["name"],
                          "properties": {"name": {"type": "string"}}}),
```

- [ ] **Step 3:** Replace the `call_tool` body with the pipeline:

```python
    _HOST_ARG = {"browser_navigate": "url"}

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            arguments = credstore.expand(arguments or {})
        except UnknownPlaceholder as e:
            return [TextContent(type="text", text=json.dumps(
                error_envelope(ErrorCode.BAD_INPUT, f"unknown credential placeholder {e}")))]

        if engagement is not None:
            host = None
            if name in _HOST_ARG:
                from urllib.parse import urlparse
                host = urlparse(arguments.get(_HOST_ARG[name], "")).hostname
            elif name.startswith("browser_") and name not in ("browser_launch", "browser_close"):
                host = session._current_host
            if host is not None and not engagement.in_scope(host):
                return [TextContent(type="text", text=json.dumps(
                    error_envelope(ErrorCode.OUT_OF_SCOPE,
                                   f"{host!r} not in engagement.toml [scope].hosts")))]

        try:
            if name == "browser_launch":
                result = await session.launch(...)
            # ... existing dispatch branches ...
            elif name == "browser_capture_identity":
                result = await session.capture_identity(arguments["name"])
                credstore.refresh_identities()
            elif name == "browser_apply_identity":
                result = await session.apply_identity(arguments["name"])
            else:
                result = error_envelope(ErrorCode.BAD_INPUT, f"unknown tool {name}")
        except Exception as e:
            logger.exception("tool crashed", extra={"tool": name})
            result = error_envelope(ErrorCode.INTERNAL, f"{type(e).__name__}: {e}")

        result = credstore.filter(result)
        return [TextContent(type="text", text=json.dumps(result))]
```

Keep all existing dispatch branches; only the wrapper around them changes.

- [ ] **Step 4: Smoke.** `python -m pytest MCPs/browser-mcp/tests/ -q` — all existing tests still pass.

---

### Task 11: burp-mcp `server.py` — chokepoint pipeline + register tools + scope push

**Files:** modify `MCPs/burp-mcp/burp_mcp/server.py`

- [ ] **Step 1:** At setup:

```python
from common.engagement import Engagement
from common.credstore import CredStore, UnknownPlaceholder
from common.oob import OOBReceiver
from common.mcp_base import ErrorCode, error_envelope

engagement = Engagement.load(WORKSPACE / "engagement.toml")
credstore = CredStore(engagement)
oob = OOBReceiver(provider=engagement.oob_provider()) if engagement else None
```

- [ ] **Step 2:** In `_tool_schemas()`, add `as_identity` to `burp_http_send` and `burp_repeater_send` schemas:

```python
                "as_identity": {"type": "string"},
```

and append:

```python
        Tool(name="oob_get_payload",
             description="Get the OOB interaction domain/url to embed in blind payloads.",
             inputSchema={"type": "object"}),
        Tool(name="oob_poll",
             description="Return OOB interactions since the given id.",
             inputSchema={"type": "object",
                          "properties": {"since_id": {"type": "integer"}}}),
```

- [ ] **Step 3:** Replace `call_tool` with the pipeline (mirror of Task 10):

```python
    _HOST_TOOLS = {"burp_http_send", "burp_repeater_send", "burp_intruder_launch"}
    _URL_TOOLS = {"burp_scanner_scan"}

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            arguments = credstore.expand(arguments or {})
        except UnknownPlaceholder as e:
            return [TextContent(type="text", text=json.dumps(
                error_envelope(ErrorCode.BAD_INPUT, f"unknown credential placeholder {e}")))]

        if engagement is not None:
            host = None
            if name in _HOST_TOOLS:
                host = arguments.get("host")
            elif name in _URL_TOOLS:
                from urllib.parse import urlparse
                host = urlparse(arguments.get("url", "")).hostname
            if host is not None and not engagement.in_scope(host):
                return [TextContent(type="text", text=json.dumps(
                    error_envelope(ErrorCode.OUT_OF_SCOPE,
                                   f"{host!r} not in engagement.toml [scope].hosts")))]

        result = await handle(name, arguments,
                              bridge_url=cfg.burp.bridge_url,
                              evidence_root=evidence_root,
                              engagement=engagement, oob=oob)
        result = credstore.filter(result)
        return [TextContent(type="text", text=json.dumps(result))]
```

- [ ] **Step 4:** After server init, push scope to Burp (best-effort):

```python
    if engagement is not None and engagement.scope_hosts():
        try:
            import asyncio as _aio
            from common.burp_client import BurpClient
            async def _push():
                async with BurpClient(cfg.burp.bridge_url) as c:
                    urls = []
                    for h in engagement.scope_hosts():
                        if "/" in h or h.startswith("*."):
                            continue
                        urls += [f"http://{h}/", f"https://{h}/"]
                    if urls:
                        await c.scope_modify(add=urls)
            _aio.get_event_loop().run_until_complete(_push())
        except Exception as e:
            logger.warning("scope push to Burp failed", extra={"err": str(e)})
```

- [ ] **Step 5: Smoke.** `python -m pytest MCPs/burp-mcp/tests/ -q` — existing tests pass (update `handle()` call sites in tests to pass `engagement=None` if signature became keyword-only; prefer giving the new params defaults so old tests need no change).

---

### Task 12: `engagement.example.toml`

**Files:** create `engagement.example.toml`

- [ ] **Step 1: Write.**

```toml
# Copy to engagement.toml (gitignored) and fill in. All sections optional;
# an absent file = no scope enforcement, no credential handling.

[engagement]
name = "client-YYYY-engagement"

[scope]
# Exact hosts, *.suffix wildcards, or CIDR ranges. Tools refuse anything else.
hosts = ["app.example.com", "*.api.example.com", "10.0.0.0/8"]

[credentials.user1]
username = "lowpriv@example.com"
password = "CHANGE_ME"

[credentials.admin]
username = "admin@example.com"
password = "CHANGE_ME"

# [identities.*] is normally written by browser_capture_identity, but you can
# seed it manually (paste a cookie/JWT) and the agent will use it immediately.
# [identities.user1]
# cookies = [{name = "session", value = "...", domain = "app.example.com"}]
# headers = {Authorization = "Bearer ..."}

[oob]
provider = "interactsh"
```

---

### Task 13: Tester docs — `docs/engagement-setup.md` + README link + `methodology-scoping`

**Files:** create `docs/engagement-setup.md`; modify `README.md`, `.claude/skills/methodology-scoping/SKILL.md`

- [ ] **Step 1: Write `docs/engagement-setup.md`** with these sections (write the prose in full — no placeholders):

  1. **What `engagement.toml` does** — one paragraph: scope guard, credential
     placeholders, identity store, OOB config.
  2. **Create the file** — `cp engagement.example.toml engagement.toml`, fill
     `[scope].hosts` and `[credentials.*]`.
  3. **First session walkthrough** — literal prompt sequence:
     ```
     browser_launch headless=false
     browser_navigate https://app.example.com/login
     browser_fill #email {{CRED:user1.username}}
     browser_fill #password {{CRED:user1.password}}
     browser_click button[type=submit]
     browser_capture_identity user1
     # repeat for admin → browser_capture_identity admin
     ```
  4. **Using identities** — `burp_http_send ... as_identity=user1` vs
     `as_identity=admin`; what `[REDACTED:CRED:…]` / `[REDACTED:IDENT:…]`
     mean in tool output.
  5. **OOB** — `oob_get_payload` → embed domain in payload → `oob_poll`.
  6. **Troubleshooting table** — `OUT_OF_SCOPE`, `unknown credential
     placeholder`, `unknown identity`, `interactsh-client not on PATH`,
     stale identity (re-run `browser_capture_identity`).

- [ ] **Step 2:** In `README.md`, under the "Running multiple engagements on
  one machine" section, append:

```markdown
Per-engagement scope, credentials, identities, and OOB are configured in
`engagement.toml` — see [`docs/engagement-setup.md`](docs/engagement-setup.md).
```

- [ ] **Step 3:** In `.claude/skills/methodology-scoping/SKILL.md`, add a step
  after the scope-record checklist:

```markdown
### Write `engagement.toml`

Once the scope record above is agreed, encode it as `engagement.toml` at the
repo root (copy `engagement.example.toml`). The `[scope].hosts` list is the
mechanical guardrail every `recon-*` and `testing-*` skill relies on —
browser-mcp and burp-mcp refuse hosts not listed there. Populate
`[credentials.*]` with the engagement-supplied test accounts.
```

---

### Task 14: Blind-detection subsection in 4 testing skills

**Files:** modify `.claude/skills/testing-ssrf/SKILL.md`, `testing-xxe/SKILL.md`, `testing-command-injection/SKILL.md`, `testing-sqli/SKILL.md`

- [ ] **Step 1:** In each, before the `## Scope` section, insert:

```markdown
## Blind detection (OOB)

When the response gives no direct signal, use the OOB receiver:

1. `oob_get_payload` → note the `domain`.
2. Embed the domain in the payload (e.g. `http://<domain>/`, `nslookup <domain>`,
   `<!ENTITY x SYSTEM "http://<domain>/">`).
3. Send the request.
4. `oob_poll since_id=0` — a `dns` or `http` interaction from the target's
   egress IP confirms the blind vulnerability.
```

Adjust the example payload per skill (SSRF: URL; XXE: external entity;
command-injection: `nslookup`/`curl`; SQLi: `LOAD_FILE`/`UTL_HTTP`/`xp_cmdshell`
as appropriate to the engine section already in that skill).

---

### Task 15: Full test sweep

- [ ] **Step 1:**

```bash
python -m pytest tests/ MCPs/browser-mcp/tests/ MCPs/burp-mcp/tests/ -q
```

Expected: all pass; new test count ≥ existing + ~18.

- [ ] **Step 2:** Manual smoke (requires running Burp + Chrome): write a
  minimal `engagement.toml` with `hosts = ["127.0.0.1"]` and one credential,
  then in Claude Code: `browser_navigate http://127.0.0.1:5055/login` (fixture
  app) → `browser_fill` with `{{CRED:…}}` → `browser_capture_identity test` →
  confirm `[identities.test]` appeared in the file → `burp_http_send` with
  `as_identity=test` → confirm `Cookie:` header injected (check via
  `burp_proxy_request`). Then `browser_navigate http://example.org/` →
  confirm `OUT_OF_SCOPE`.

---

## Self-review

- Spec §2 schema → Task 12. §3 scope → Tasks 2, 3, 10, 11. §4 cred/redact →
  Tasks 1, 5, 10, 11. §5 identity → Tasks 4, 7, 8, 10, 11. §6 OOB → Tasks 6,
  9, 11, 14. §7 pipeline → Tasks 10, 11. §8 docs → Task 13. §9 tests → every
  task + Task 15. No spec section unmapped.
- No "TBD"/"similar to" placeholders. Task 13 step 1 enumerates section
  contents rather than full prose because it is documentation, not code; the
  implementer writes the prose — that is the task.
- Signatures consistent: `Engagement.load/in_scope/credential/identity/
  write_identity/scope_hosts/oob_provider`; `CredStore.expand/filter/
  refresh_identities`; `OOBReceiver.get_payload/poll`; `handle(...,
  engagement=, oob=)`; `BrowserSession(..., engagement=)`.
