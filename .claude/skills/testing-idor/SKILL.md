---
name: testing-idor
description: Test for OWASP A01 IDOR / BOLA — direct object references accessible without authorization check.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-api-enum`, `recon-sitemap-crawl`, `mcp-burp`.

Use this skill when endpoints take an object identifier (`/users/123`, `?id=abc`, `/orders/UUID`) and return resource data. The goal is to determine whether the server enforces authorization between the requesting session and the owner of the referenced object.

## Signal to look for

- Numeric IDs that are incrementable (e.g., `/orders/1001`, `/orders/1002`).
- UUIDs that are swappable between accounts.
- ID appearing in a URL path segment or body parameter.
- Absence of a secondary authorization check between the session user and the object owner.

## Test steps

1. Capture a resource request while logged in as User A via `burp_proxy_history`.
2. Use `burp_match_replace_set` to swap User A's session cookie for User B's when replaying.
3. Re-issue via `burp_repeater_send`; observe whether User B's resource returns or is forbidden.
4. ID-enumeration: increment or decrement numeric IDs; observe whether other users' data is returned.
5. Writable IDOR: test PUT/POST requests with swapped IDs to check for unauthorized modification.
6. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell:**

```bash
curl -H "Cookie: session=<USER_B_SESSION>" https://target.example.com/api/users/<USER_A_ID>
# Success: User A's data returned with User B's session
```

**MCP:**

```
# Set a match-replace rule to swap session cookies for replay
burp_match_replace_set(rules=[{"match": "session=<USER_A>", "replace": "session=<USER_B>",
                                "type": "request_header", "enabled": true}])
# Success: {"ok": true, "data": {"count": 1}}

# Replay User A's request with the active match-replace rule applied
burp_repeater_send(raw_base64=<b64 of User A's request>, host="target.example.com",
                   port=443, secure=true, tab_name="idor-probe")
# Success: {"ok": true, "data": {"tab_id": "..."}}
# Inspect the response body for User A's data returned under User B's session.
```

## Interpret results

User B receiving User A's data confirms an IDOR vulnerability. A partial leak — where only some fields from User A's resource are returned — is still a valid finding and should be reported. False positive: if the server returns HTTP 200 with an empty payload, the endpoint may be field-level access-controlled; verify by checking the actual contents of the response body before concluding no data is exposed.

## Finding writeup

- **Title:** `Insecure Direct Object Reference at <endpoint>`.
- **Severity:** Unauthenticated access = Critical; cross-user read = High; cross-user write = High-Critical.
- **Evidence** per `methodology-evidence-capture`: both requests (victim session and attacker session), both responses, and the `burp_repeater_send` reproduction steps.
- **Fix:** Authorize every object access on the server side; use session-scoped object lookups so the server resolves the resource from the authenticated principal rather than accepting a caller-supplied identifier directly.

## References

- OWASP WSTG ATHZ-04: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/05-Authorization_Testing/04-Testing_for_Insecure_Direct_Object_References
- PortSwigger Access Control: https://portswigger.net/web-security/access-control
- CWE-639: https://cwe.mitre.org/data/definitions/639.html

## Authorization note

Only use against systems you are authorized to test. This skill assumes the user has obtained written authorization. If authorization is uncertain, stop and confirm scope before proceeding.
