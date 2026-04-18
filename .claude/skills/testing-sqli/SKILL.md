---
name: testing-sqli
description: Test for OWASP A03 SQL Injection — error-based, blind, UNION, and time-based — via Burp Repeater and sqlmap.
---

# SQL Injection Testing

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-api-enum`, `recon-content-discovery`, `mcp-burp`.

Use this skill when the target has a SQL backend and user-supplied input reaches a database query. An injectable parameter typically shows an error, blind boolean, or time-based oracle that can be exploited to extract or manipulate data.

## Signal to look for

- Response shape (body length, status code, content structure) changes when a quote character (`'`, `"`) or boolean fragment is appended to a parameter value.
- Visible SQL error banners appear in the response body — MySQL (`You have an error in your SQL syntax`), PostgreSQL (`ERROR: unterminated quoted string`), MSSQL (`Unclosed quotation mark`), or Oracle (`ORA-00907`).
- Slow responses correlated with `SLEEP()` (MySQL/MariaDB) or `WAITFOR DELAY` (MSSQL) injected into a parameter, indicating a time-based blind oracle.

## Test steps

1. Identify a candidate parameter via `burp_proxy_history` — look for GET/POST parameters, JSON body fields, or HTTP headers that are likely query-bound.
2. Probe the parameter with `'`, `"`, `)` in turn; observe whether the response changes in body length, status code, or content (error message, empty result set).
3. Confirm a boolean oracle: compare the response to `' OR 1=1--` against `' OR 1=2--`; a consistent length or content difference confirms injection.
4. If no visible difference, use a time-based fallback: inject `' AND SLEEP(5)--` and observe whether the response takes approximately 5 seconds longer than baseline.
5. Hand off confirmed parameters to `sqlmap` for automated extraction; respect RoE rate limits (see `methodology-rules-of-engagement`) via `--delay` or `--safe-freq`.
6. Capture evidence per `methodology-evidence-capture`: save the full request/response pair for each successful payload before proceeding to extraction.

## Tool commands

Shell — sqlmap extraction:

```bash
sqlmap -u "https://target.example.com/api/users?id=1" --batch --risk=1 --level=2
# Success: sqlmap reports injectable parameter and DBMS fingerprint
```

MCP — Burp Repeater probe and history search:

```
burp_repeater_send(raw_base64="<b64 of request with SQL payload>", host="target.example.com", port=443, secure=true, tab_name="sqli-probe")
# Success: {"ok": true, "data": {"tab_id": "..."}}

burp_proxy_history(host="target.example.com", contains="SLEEP(")
# Success: {"ok": true, "data": {"items": [...], "total": <N>, "cursor": <N>}}
```

MCP tool signatures follow the `mcp-burp` skill.

## Interpret results

**Error-based:** A DBMS banner or stack trace in the response body confirms injection and fingerprints the database engine. Treat this as a high-confidence finding.

**Blind-boolean:** A consistent response-length or content differential between a true payload (`1=1`) and a false payload (`1=2`) confirms injection even without visible errors.

**Time-based:** A consistent delay of approximately N seconds proportional to the `SLEEP(N)` argument confirms a time-based blind oracle. Take the median of at least 5 trials to rule out network jitter.

**False positives:** A WAF may return `403` or `503` on quote characters without an underlying injection — cross-check by testing a benign equivalent-length string. Network jitter can mimic time-based delays; the median-of-5 rule applies here too.

**Severity context:** Authentication state affects impact. Unauthenticated extraction is typically Critical; post-authentication is High. A blind-only channel with limited extraction speed may reduce to Medium.

## Finding writeup

- **Title pattern:** `SQL Injection in <endpoint> parameter <name>`.
- **Severity:** Unauthenticated data extraction = Critical; authenticated = High; blind-only with limited extraction = Medium.
- **Description template:** *"The `<parameter>` value is concatenated into a SQL query at `<endpoint>`, allowing an attacker to alter query semantics and extract/manipulate data."*
- **Evidence** per `methodology-evidence-capture`: full request/response pair showing the error or differential, sqlmap summary output, and a reproducible `burp_repeater_send` call that an independent reviewer can replay.
- **Suggested fix:** Use parameterized queries or prepared statements; apply ORM-level escaping where raw SQL is unavoidable; run the database service under a least-privilege user account with no write access to system tables.

## References

- OWASP WSTG INPV-05: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05-Testing_for_SQL_Injection
- PortSwigger SQLi: https://portswigger.net/web-security/sql-injection
- CWE-89: https://cwe.mitre.org/data/definitions/89.html
- sqlmap wiki: https://github.com/sqlmapproject/sqlmap/wiki

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
