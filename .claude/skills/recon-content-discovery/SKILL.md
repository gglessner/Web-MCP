---
name: recon-content-discovery
description: Discover hidden endpoints, backup files, and config artifacts on a web target via wordlist enumeration (ffuf/dirsearch/gobuster) plus common low-hanging paths.
---

# Content Discovery

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-burp`, `mcp-browser`.

Use this skill after scope is settled and the public surface is known. Content
discovery finds what isn't linked: admin panels, development leftovers, backup
archives, and configuration files that the application never advertises but
still serves.

## Signal to look for

- Target has a large unknown attack surface with few publicly linked paths.
- Framework hints (error pages, headers, cookie names) suggest unprotected
  dev or admin endpoints that may be guessable by name.
- Version-control metadata or backup files may be exposed (`.git`, `.svn`,
  `.bak`, `.zip`) based on how the application is deployed.

## Test steps

1. Check low-hanging paths first:
   ```bash
   curl -sI https://target.example.com/robots.txt
   curl -sI https://target.example.com/sitemap.xml
   curl -sI https://target.example.com/.git/HEAD
   curl -sI https://target.example.com/.env
   curl -sI https://target.example.com/.DS_Store
   curl -sI https://target.example.com/backup.zip
   ```
2. Run ffuf with a common wordlist; respect RoE rate limits via `-rate`:
   ```bash
   ffuf -u https://target.example.com/FUZZ \
        -w /usr/share/wordlists/dirb/common.txt \
        -mc 200,301,403 -rate 10
   ```
3. Optional — run dirsearch for extension-aware probing:
   ```bash
   dirsearch -u https://target.example.com \
             -e php,bak,old,zip,tar,gz,sql
   ```
4. Load confirmed hits into Burp scope:
   ```
   burp_scope_modify(add=["https://target.example.com/hidden-path"], remove=[])
   ```
5. Spot-check hits that require JS to render:
   ```
   browser_navigate(url="https://target.example.com/hidden-path")
   browser_snapshot()
   ```

## Tool commands

Shell — canonical ffuf run:

```bash
ffuf -u https://target.example.com/FUZZ \
     -w /usr/share/wordlists/dirb/common.txt \
     -mc 200,301,403 -rate 10 \
     -o ffuf.json -of json
# Success: JSON results written to ffuf.json; matches printed to stdout
```

Shell — low-hanging path loop:

```bash
for p in robots.txt sitemap.xml .git/HEAD .env .DS_Store backup.zip; do
  curl -sI "https://target.example.com/$p" | head -1
done
# Success: one HTTP status line per path; 200 or 403 = path exists
```

MCP follow-up (after confirming hits):

```
# Add discovered paths to Burp scope
burp_scope_modify(add=["https://target.example.com/hidden-path"], remove=[])
# Success: {"ok": true, "data": {"added": 1, "removed": 0}}

# Navigate to a JS-rendered hit for inspection
browser_navigate(url="https://target.example.com/hidden-path")
# Success: {"ok": true, "data": {"url": "https://target.example.com/hidden-path"}}

# Capture rendered DOM and accessibility tree
browser_snapshot()
# Success: {"ok": true, "data": {"dom": {...}, "accessibility": {...}}}
```

## Interpret results

**Status-code triage:**

- `200` — path is reachable; inspect the response body for sensitive content.
- `301` — redirect; follow the `Location` header and reprobe the destination.
- `403` — resource exists but access is controlled; do not attempt to bypass
  without explicit RoE clearance — see `methodology-rules-of-engagement`.

**Length-based false-positive filtering:** soft-404 pages often return `200`
with a consistent body size. Use `-fs <size>` (filter by byte size) or
`-fw <count>` (filter by word count) in ffuf to suppress them. Confirm edge
cases with `browser_snapshot` to view the rendered page.

**Rate-limiting signals:** a sudden shift to `429` responses or artificially
introduced delays indicates the target or a WAF is throttling. Stop, consult
`methodology-rules-of-engagement`, and adjust `-rate` accordingly before
resuming.

## Finding writeup

Confirmed hits either stand alone as direct findings or feed forward into
further testing. Direct findings:

- **"Exposed `.git` Directory"** — High severity. The full application source
  is recoverable, exposing logic, secrets, and internal paths.
- **"Exposed `.env` File"** — High severity. Likely contains database
  credentials, API keys, and application secrets in plaintext.
- **"Backup File Accessible"** — Medium to High depending on contents.
  A downloadable archive of application code or database dumps.

Evidence per `methodology-evidence-capture`:

- `curl -I` output showing the `200` status for the sensitive path.
- `burp_proxy_request` output for the full response body confirming the
  sensitive content (source code, credentials, archive magic bytes).

## References

- OWASP WSTG-CONF-04 — Review Old, Backup, and Unreferenced Files:
  https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/04-Review_Old_Backup_and_Unreferenced_Files_for_Sensitive_Information
- OWASP WSTG-CONF-05 — Enumerate Infrastructure and Application Admin Interfaces:
  https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/05-Enumerate_Infrastructure_and_Application_Admin_Interfaces
- ffuf repository: https://github.com/ffuf/ffuf
- SecLists project: https://github.com/danielmiessler/SecLists

## Authorization note

Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.
