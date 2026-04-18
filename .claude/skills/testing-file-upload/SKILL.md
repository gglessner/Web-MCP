---
name: testing-file-upload
description: Test for OWASP A01/A04 File Upload vulnerabilities — extension bypass, MIME spoofing, polyglot, path traversal via filename.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-content-discovery`, `mcp-burp`.

Use this skill when the target accepts file uploads such as profile pictures, documents, or import files. File upload functionality is a common attack surface that can lead to remote code execution, stored XSS, or unauthorized file placement when server-side validation is weak or missing.

## Signal to look for

- Multipart upload endpoints (`multipart/form-data` POST requests).
- Filename reflected in the server response body or embedded in the URL after a successful upload.
- Server-side rendering of uploaded content, such as image previews generated on the server, inline file downloads, or document conversion features that process the uploaded file's contents.

## Test steps

1. Upload a baseline legitimate file (e.g., a valid JPEG image) and confirm the resulting URL or storage path returned by the server.
2. Extension bypass: upload files named `shell.php.jpg`, `shell.phtml`, `shell.pHp`, and an `.htaccess` file with an `AddType` directive to remap an extension to a PHP handler.
3. MIME spoofing: rename `shell.php` to `shell.jpg`, send the request with `Content-Type: image/jpeg`, and observe whether the server accepts and stores the file under the disguised name.
4. Path traversal via filename: set the `filename` parameter to `../../webroot/shell.php` and observe whether the server writes the file outside the intended upload directory.
5. Polyglot: craft an image file with embedded PHP or JavaScript payload in EXIF metadata or appended after valid image bytes.
6. If an upload succeeds: use `browser_navigate` to navigate to the uploaded file's URL and confirm whether the server executes or interprets the payload.
7. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell:**

```bash
curl -F 'file=@shell.php;filename=shell.php.jpg' -F 'file_type=image/jpeg' https://target.example.com/upload
# Success: 200; URL of uploaded file returned
```

**MCP:**

Send a crafted multipart request via Burp Repeater:

```
burp_repeater_send(raw_base64=<b64 multipart>, host="target.example.com", port=443, secure=true, tab_name="upload-probe")
```

Expected envelope on success:

```json
{"ok": true, "status": 200, "body": "...uploaded file URL..."}
```

Navigate to the uploaded file to confirm execution:

```
browser_navigate(url="https://target.example.com/uploads/shell.php.jpg")
```

Expected envelope:

```json
{"ok": true, "url": "https://target.example.com/uploads/shell.php.jpg", "title": "..."}
```

## Interpret results

- Uploaded PHP, JSP, or ASPX file executing as server-side code = Remote Code Execution (RCE); treat as a critical finding.
- Stored XSS delivered via an SVG or HTML file upload that executes JavaScript in a victim's browser is a separate positive finding path; report independently.
- False positive: an `.htaccess` file upload being accepted does not confirm exploitability. The server must actually process the directive — this requires a server running Apache with `AllowOverride` enabled. If the server uses Nginx, IIS, or another web server that does not process `.htaccess`, the upload is inert. Always test actual interpretation; do not rely on upload success alone.

## Finding writeup

- **Title:** `Unrestricted File Upload in <endpoint>`
- **Severity:**
  - RCE via web shell = Critical
  - File overwrite via path traversal = High
  - Stored XSS via SVG or HTML upload = High
- **Evidence** per `methodology-evidence-capture`: the upload request, the server response containing the stored filename or URL, navigation to the uploaded file's URL, and proof of execution or interpretation (e.g., PHP output rendered, JavaScript alert fired).
- **Fix:** Whitelist permitted extensions server-side rather than blacklisting; regenerate filenames server-side to eliminate attacker-controlled paths; store uploaded files outside the web root so they cannot be directly served as code; serve uploaded files through a dedicated handler that enforces strict `Content-Type` headers and never executes file contents.

## References

- OWASP WSTG BUSL-09 (Testing Upload of Unexpected File Types): `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/10-Business_Logic_Testing/09-Test_Upload_of_Unexpected_File_Types`
- PortSwigger File upload: `https://portswigger.net/web-security/file-upload`
- CWE-434: `https://cwe.mitre.org/data/definitions/434.html`

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
