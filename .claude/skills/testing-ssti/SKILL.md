---
name: testing-ssti
description: Test for OWASP A03 Server-Side Template Injection against Jinja2, Twig, Freemarker, Smarty, ERB, and similar engines.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-tech-fingerprinting`, `mcp-burp`.

Use this skill when the target uses a server-side template engine and user input is rendered as part of a template. Common scenarios include name or greeting fields, email confirmation bodies, report generation, and any endpoint where reflected content is processed before being sent to the client.

## Signal to look for

- Input is reflected in a rendered template (e.g., a greeting page that displays a name you submitted)
- Name or email fields that echo back in a mail body or confirmation page
- Error pages rendered from templates that include user-supplied values
- Framework fingerprint (from `recon-tech-fingerprinting`) indicates a template engine such as Jinja2, Twig, Freemarker, Smarty, or ERB

## Test steps

1. **Baseline probe** — choose the syntax that matches the fingerprint from `recon-tech-fingerprinting`:
   - Jinja2 / Twig: `{{7*7}}`
   - Freemarker / JSP EL: `${7*7}`
   - ERB (Ruby): `<%= 7*7 %>`

   Submit the probe as the value of the target parameter (URL, form field, header). If no engine fingerprint is available, try all three in sequence.

2. **Evaluate the response** — if `49` appears in the response body where your input would normally be reflected, the server is evaluating the expression inside the template engine.

3. **Engine identification** — use the following payload/response pairs to narrow down the engine:

   | Payload | Expected response | Engine |
   |---|---|---|
   | `{{7*'7'}}` | `7777777` | Jinja2 |
   | `{{7*'7'}}` | `49` | Twig |
   | `${7*7}` evaluated + `<#assign x=7*7>${x}` | `49` | Freemarker |
   | `<%= 7*7 %>` | `49` | ERB |

4. **RCE probe** — only with explicit written sponsor approval (see `methodology-rules-of-engagement`):
   - Jinja2: `{{ ''.__class__.__mro__[1].__subclasses__() }}`
   - This reveals loaded Python classes and confirms code-execution context. Do not proceed further without authorization.

5. **Capture evidence** per `methodology-evidence-capture`: screenshot or export the request/response pair for each confirming payload.

## Tool commands

**Shell — automated engine detection and RCE status:**

```bash
tplmap -u "https://target.example.com/greet?name=FUZZ"
# Success: tplmap reports engine + RCE status
```

**MCP — manual probe via Burp Repeater:**

```
burp_repeater_send(
  raw_base64=<base64-encoded request with {{7*7}} in the target parameter>,
  host="target.example.com",
  port=443,
  secure=true,
  tab_name="ssti-probe"
)
```

Inspect the response body for `49`. If present, proceed to engine identification payloads in subsequent Repeater tabs.

## Interpret results

- **Arithmetic evaluation confirmed** — a response containing `49` where `{{7*7}}` (or equivalent) was submitted is a positive indicator of SSTI.
- **Engine identification** — the specific payload/response pair from the table above narrows the engine and informs escalation payload selection.
- **False positive: client-side template injection** — frameworks such as AngularJS also use `{{}}` syntax, but evaluation happens in the browser, not on the server. Verify server-side rendering by inspecting the raw HTTP response via `burp_proxy_request`. If `49` appears in the server response body (before the browser renders it), the injection is server-side and the finding is valid.

## Finding writeup

- **Title:** Server-Side Template Injection in `<field>`
- **Severity:**
  - RCE confirmed: Critical
  - Code evaluation confirmed without RCE: High
- **Evidence** per `methodology-evidence-capture`:
  - Request containing the arithmetic probe (e.g., `{{7*7}}`) and the corresponding response showing `49`
  - Engine-identification payload and its response (e.g., `{{7*'7'}}` returning `7777777` for Jinja2)
- **Recommended fix:**
  - Never pass user-controlled input directly into a template rendering function
  - Use context-aware interpolation (pass data as template variables, not as template source)
  - Where a template engine must process dynamic content, enforce a sandboxed template environment with an allowlist of safe operations

## References

- OWASP WSTG INPV-18: <https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/18-Testing_for_Server-side_Template_Injection>
- PortSwigger SSTI: <https://portswigger.net/web-security/server-side-template-injection>
- CWE-94: <https://cwe.mitre.org/data/definitions/94.html>

## Authorization note

Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.
