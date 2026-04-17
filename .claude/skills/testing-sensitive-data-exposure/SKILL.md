---
name: testing-sensitive-data-exposure
description: Test for OWASP A02 Sensitive Data Exposure in responses — PII, tokens, credentials, stack traces, debug output.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-sitemap-crawl`, `recon-content-discovery`, `mcp-burp`.

After recon phases have populated the proxy with traffic, review captured proxy history for inadvertent disclosure of secrets, PII, or server-internal details that appear in responses the application returns to clients.

## Signal to look for

- Stack traces visible in production responses
- `Authorization:` header values echoed back in response bodies
- Private keys or tokens embedded in HTML comments or JS bundles
- Verbose `X-Debug:`, `X-Powered-By:` headers carrying sensitive internal values

## Test steps

1. Regex scan across captured history: `burp_proxy_history(contains="Authorization: ")`.
2. Run separate scans for common secret patterns: `BEGIN RSA`, `sk_live_`, `AWS_SECRET_ACCESS_KEY`, `password=`.
3. Trigger error paths (invalid IDs, malformed JSON) and capture any stack traces returned.
4. Check for PII in responses (SSN, credit-card patterns) and flag each instance.
5. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell:**

```bash
# Scan downloaded response bodies for secrets
trufflehog filesystem --include-paths .claude --no-update

# Manual grep for common secret patterns
grep -rE "(BEGIN RSA|sk_live_|AWS_SECRET_ACCESS_KEY|password=)" ./responses/
```

**MCP:**

Scan for private key material:

```json
{"ok": true, "result": "<history items>"}
```

```
burp_proxy_history(host="target.example.com", contains="BEGIN RSA")
```

Scan for plaintext passwords:

```
burp_proxy_history(host="target.example.com", contains="password=")
```

```json
{"ok": true, "result": "<history items>"}
```

Scan for stack traces:

```
burp_proxy_history(host="target.example.com", contains="Exception")
```

```json
{"ok": true, "result": "<history items>"}
```

## Interpret results

Any real credential, PII, or server-internal detail present in a response body or header constitutes a finding and must be reported. False positives to watch for: placeholder secrets such as `YOUR_API_KEY_HERE` or `sk_test_*` values — these should be flagged as informational only rather than confirmed vulnerabilities.

## Finding writeup

- **Title:** `Sensitive Data Exposure in <response>`
- **Severity:**
  - Credentials leaked = Critical
  - PII exposed = High
  - Stack trace with path disclosure = Low-Medium
- **Evidence** per `methodology-evidence-capture`: include a redacted excerpt of the response showing the disclosure (redact real data values before filing the report).
- **Fix:** Redact sensitive values at the API or templating layer; catch and swallow exception details in production error handlers; purge secrets from JS bundles at build time; set `X-Debug: false` in production configuration.

## References

- OWASP WSTG INFO-05: <https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/05-Review_Webpage_Content_for_Information_Leakage>
- PortSwigger Information disclosure: <https://portswigger.net/web-security/information-disclosure>
- CWE-200: <https://cwe.mitre.org/data/definitions/200.html>

## Authorization note

Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.
