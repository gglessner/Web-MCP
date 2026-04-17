---
name: testing-ldap-injection
description: Test for OWASP A03 LDAP Injection in auth forms and directory-query endpoints.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-api-enum`, `mcp-burp`.

Target uses LDAP for authentication or directory search (enterprise apps, Active Directory integrations). Applies when login forms bind user-supplied credentials directly to an LDAP directory or when search endpoints construct LDAP filters from user input.

## Signal to look for

- Auth endpoints that accept username and password and bind to an LDAP backend
- Directory-search endpoints that accept a query string and return user or group records
- Error messages containing `ldap`, `invalid DN`, or OID patterns (e.g., `1.2.840.113556`)

## Test steps

1. **Authentication bypass probe:** submit username `*)(uid=*))(|(uid=*` with any password and observe whether login succeeds.
2. **Blind enumeration via wildcards:** try usernames such as `admin*`, `a*`, `*admin*` to enumerate valid accounts based on response differences.
3. **Response-differential analysis:** compare HTTP status codes, response bodies, and timing between valid credentials, invalid credentials, and injected payloads to confirm the injection surface.
4. **Capture evidence** per `methodology-evidence-capture` — record payloads, raw requests/responses, and reproduction steps for all findings.

## Tool commands

**Shell:**

```bash
curl -X POST --data 'user=*)(uid=*))(|(uid=*&pass=x' https://target.example.com/login
# Success: 200 + auth token
```

**MCP:**

```
burp_repeater_send(raw_base64=<b64>, host="target.example.com", port=443, secure=true, tab_name="ldap-probe")
```

Compare the response to a baseline failure via:

```
burp_proxy_request(id=<N>)
```

Retrieve the baseline request ID from proxy history before sending the injected payload so the differential is clear.

## Interpret results

A successful login when using the wildcard payload (`*)(uid=*))(|(uid=*`) confirms an authentication bypass via LDAP injection.

**False positive check:** some servers sanitise or strip `()` from the username field before constructing the LDAP filter. Inspect the raw request body using `burp_proxy_request` to confirm the payload reached the server as-is before classifying as confirmed.

## Finding writeup

- **Title:** `LDAP Injection in <parameter>`
- **Severity:**
  - Authentication bypass = Critical
  - Blind enumeration only = Medium
- **Evidence** (per `methodology-evidence-capture`): injected payload, server response showing bypass or differential, `burp_repeater_send` reproduction command.
- **Fix:**
  - Escape LDAP special characters (`*`, `(`, `)`, `\`, `NUL`) in all user-supplied input.
  - Use parameterised LDAP queries where the framework supports them.
  - Use a library that enforces DN grammar and rejects malformed filter strings.

## References

- OWASP WSTG INPV-06: <https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/06-Testing_for_LDAP_Injection>
- PortSwigger LDAP injection: <https://portswigger.net/kb/issues/00100500_ldap-injection>
- CWE-90: <https://cwe.mitre.org/data/definitions/90.html>

## Authorization note

Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.
