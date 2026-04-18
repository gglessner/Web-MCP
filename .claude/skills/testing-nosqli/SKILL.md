---
name: testing-nosqli
description: Test for OWASP A03 NoSQL Injection against MongoDB, CouchDB, and similar stores via operator-syntax and JS-injection payloads.
---

# NoSQL Injection Testing

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-api-enum`, `mcp-burp`.

Use this skill when the target has a NoSQL backend — framework fingerprint indicates MongoDB, CouchDB, or Firestore — and user-supplied input reaches a query. Common indicators include a Node.js/Express stack, MongoDB connection strings in error messages, or Mongoose-related stack traces. The technique is most impactful at authentication endpoints where a crafted operator payload can bypass credential checks entirely.

## Signal to look for

- JSON-bodied endpoints: `Content-Type: application/json` in POST requests to `/login`, `/auth`, `/api/users`, or similar.
- Authentication forms that accept a full JSON object rather than form-encoded fields — these pass user input directly into a query object.
- Absence of SQL-specific error patterns (no `syntax error near`, no `ORA-`, no `MSSQL`) combined with tech-fingerprint evidence of NoSQL: `X-Powered-By: Express`, MongoDB driver version strings, or `mongoose` in JavaScript bundles.
- Error messages referencing `$where`, `$query`, or BSON parsing failures when malformed input is submitted.

## Test steps

1. Identify JSON endpoints via `burp_proxy_history(host="target.example.com", contains="application/json")` — focus on authentication and search endpoints.
2. Retrieve the full request for a candidate endpoint with `burp_proxy_request(id=<N>)` and note the JSON body structure.
3. Operator-syntax probe: replace `{"user":"x","pass":"y"}` with `{"user":{"$ne":null},"pass":{"$ne":null}}` and send via `burp_repeater_send`.
4. JS-injection probe (applicable where `$where` or server-side JS eval is used): set `"user": "'; return true; //"` and observe whether the query short-circuits.
5. Confirm auth bypass or unexpected data return: a successful-login response (200 with session token, redirect to dashboard) despite no valid credentials is conclusive.
6. Capture evidence per `methodology-evidence-capture`: save the full request/response pair for each successful payload before further enumeration.

## Tool commands

Shell — operator-injection probe via curl:

```bash
curl -s -X POST \
  -H 'Content-Type: application/json' \
  --data '{"user":{"$gt":""},"pass":{"$gt":""}}' \
  https://target.example.com/api/login
# Success: 200 with auth token despite unknown credentials
```

MCP — Burp Repeater probe and history search:

```
burp_repeater_send(raw_base64=<b64>, host="target.example.com", port=443, secure=true, tab_name="nosqli-probe")
# Success: {"ok": true, "data": {"tab_id": "..."}}

burp_proxy_history(host="target.example.com", contains="$ne")
# Success: {"ok": true, "data": {"items": [...], "total": <N>, "cursor": <N>}}
```

MCP tool signatures follow the `mcp-burp` skill.

## Interpret results

**Auth bypass confirmed:** A successful-login response — HTTP 200 with a session cookie, JWT, or redirect to an authenticated page — in response to an operator payload proves injection. The server passed the operator object directly into a MongoDB `findOne` or equivalent, causing the query to match every document.

**Authenticated enumeration:** If an operator payload in a search field returns records belonging to other users, the finding is confirmed at a lower severity but still significant.

**False positives:** Endpoints that return HTTP 400 (`Bad Request`) or a schema-validation error when an object is supplied where a string is expected are not vulnerable — the input sanitization is upstream of the query. Verify that the operator payload actually reaches the NoSQL query unsanitized by checking server-side JSON parsing behavior; some frameworks strip unexpected keys before handing off to the data layer.

**Severity context:** Authentication bypass via `$ne`/`$gt` at an unauthenticated endpoint is Critical. Authenticated data enumeration via operator injection is Medium to High depending on the sensitivity of exposed records.

## Finding writeup

- **Title pattern:** `NoSQL Injection in <endpoint>`.
- **Severity:** Authentication bypass = Critical; authenticated enumeration = Medium-High.
- **Description template:** *"The `<parameter>` value is embedded into a NoSQL query without filtering MongoDB-style operator keys (`$ne`, `$gt`, etc.), allowing an attacker to alter query semantics."*
- **Evidence** per `methodology-evidence-capture`: full request/response pair showing the operator payload and the bypassed-authentication response; a reproducible `burp_repeater_send` call that an independent reviewer can replay.
- **Suggested fix:** Whitelist and type-check inputs before use in a query — reject any value that is not a plain string or number where a scalar is expected; reject object keys starting with `$` at the API boundary; use query builders or ODM methods that escape operator keys rather than accepting raw user-supplied objects.

## References

- OWASP WSTG INPV-05 §NoSQL: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05-Testing_for_SQL_Injection
- PortSwigger NoSQL Injection: https://portswigger.net/web-security/nosql-injection
- CWE-943: https://cwe.mitre.org/data/definitions/943.html

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
