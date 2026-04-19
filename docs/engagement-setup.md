# Engagement setup (`engagement.toml`)

`engagement.toml` is the per-engagement configuration that the MCP servers
read at startup. It does four things:

1. **Scope guard** — `[scope].hosts` is a hard allowlist. `browser_navigate`,
   `burp_http_send`, `burp_repeater_send`, `burp_intruder_launch`, and
   `burp_scanner_scan` refuse any host not matched. Exact host, `*.suffix`,
   or CIDR.
2. **Credential placeholders** — `[credentials.<name>]` values are never
   shown to the model. The model sends `{{CRED:<name>.<field>}}` and the
   server expands it; any tool output that echoes the literal is replaced
   with `[REDACTED:CRED:<name>.<field>]`.
3. **Identity store** — `[identities.<name>]` holds session cookies/headers
   for each test account. Seeded by hand or captured by
   `browser_capture_identity`. Used by `burp_http_send`/`burp_repeater_send`
   `as_identity=<name>` and `browser_apply_identity`.
4. **OOB receiver** — `[oob].provider` selects the blind-callback backend
   (interactsh by default).

If the file is absent, none of this is active — current behaviour is
preserved. If it's present with `hosts = []`, scope is **fail-closed**.

## What the model can and can't see

The model **never reads `engagement.toml`**. A PreToolUse hook blocks `Read`,
`Grep`, and any `Bash` command referencing the path, and project instructions
(`CLAUDE.md`) tell it not to work around the block. Instead it calls
`engagement_info`, which returns:

```json
{"name": "...", "scope_hosts": [...],
 "credentials": {"user1": ["password", "username"], "admin": [...]},
 "identities": {"user1": {"cookies": 2, "headers": ["Authorization"], "captured_at": "..."}},
 "oob_provider": "interactsh"}
```

— names and field names only, never values. That's enough to write
`{{CRED:user1.password}}` and `as_identity="user1"`.

## 1. Create the file

```bash
cp engagement.example.toml engagement.toml
$EDITOR engagement.toml
```

Fill `[scope].hosts` from your scope record and `[credentials.*]` from the
client-supplied test accounts.

## 2. First session — log in and capture identities

In Claude Code (the literal placeholders below are what the model types — the
server substitutes the real values; the model never sees them):

```
browser_launch headless=false
browser_navigate https://app.example.com/login
browser_fill #email {{CRED:user1.username}}
browser_fill #password {{CRED:user1.password}}
browser_click button[type=submit]
browser_wait_for .dashboard
browser_capture_identity user1
```

`browser_capture_identity` reads in-scope cookies and the most recent
`Authorization` header from the network log and writes them to
`[identities.user1]` in `engagement.toml`. Repeat for each test account
(`browser_capture_identity admin`). You can also paste cookies in by hand
under `[identities.*]` if you'd rather log in manually in Burp's browser.

## 3. Multi-account testing

```
burp_http_send raw_base64=<GET /api/orders/42 ...> host=app.example.com port=443 as_identity=user1
# → 200, body shows order 42

burp_http_send raw_base64=<same request> host=app.example.com port=443 as_identity=admin
# → 200 ⇒ compare; 403 ⇒ control works
```

`as_identity` replaces the request's `Cookie:` header (and any headers listed
under `[identities.<name>].headers`) before sending. Session values that
appear in tool output are shown as `[REDACTED:IDENT:<name>.cookie]` /
`[REDACTED:IDENT:<name>.header]` so you can tell *which* identity's token
was present without seeing it.

For browser-side authenticated crawling under a stored identity:

```
browser_apply_identity admin
browser_navigate https://app.example.com/admin
```

## 4. Blind detection (OOB)

```
oob_get_payload                  # → {"domain": "abc123.oast.fun", "url": "http://abc123.oast.fun/"}
# embed the domain in your SSRF/XXE/cmd-injection/SQLi payload, send it
oob_poll since_id=0              # → [{"id":1,"protocol":"dns","remote_addr":"203.0.113.5", ...}]
```

A `dns` or `http` interaction from the target's egress IP confirms the blind
vulnerability. Requires `interactsh-client` on `PATH` (preinstalled on Kali).

## 5. Troubleshooting

| Error | Meaning / fix |
|---|---|
| `OUT_OF_SCOPE: 'host' not in engagement.toml [scope].hosts` | Add the host (or its wildcard/CIDR) to `[scope].hosts`, or it really is out of scope. |
| `BAD_INPUT: unknown credential placeholder {{CRED:x.y}}` | `[credentials.x]` table or field `y` doesn't exist. |
| `BAD_INPUT: unknown identity 'x'` | No `[identities.x]` — run `browser_capture_identity x` first or seed it by hand. |
| `INTERNAL: OOB receiver not configured` | No `engagement.toml` loaded (oob is only set up when one exists). |
| `RuntimeError: interactsh-client not on PATH` | `sudo apt install interactsh-client` or `go install github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest`. |
| Identity stops working mid-test (401s) | Session expired. Re-run the login + `browser_capture_identity <name>` flow; the file and redaction filter update in place. |

## Hardening (optional, hard boundary)

The hook + instruction layers stop a *cooperative* model. They do **not** stop
a prompt-injected or adversarial model that writes a script to read the file
via an unblocked path. If your threat model includes that, the only robust
defence is filesystem permissions — make the file unreadable by the process
that runs the model's Bash/Read tools:

```bash
# Run the MCP servers (which legitimately read engagement.toml) as a
# dedicated user; run Claude Code's shell as your normal user.
sudo useradd -r webmcp
sudo chown webmcp:webmcp engagement.toml
sudo chmod 600 engagement.toml
# Then launch the MCP servers via sudo -u webmcp in .mcp.json's "command".
```

Under that setup, even `python3 -c "open('engagement.toml').read()"` from the
model's Bash tool gets `PermissionError`. The MCP servers (running as
`webmcp`) still read it fine.
