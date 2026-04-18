---
name: testing-privilege-escalation
description: Test for OWASP A01 Privilege Escalation — horizontal (peer user) and vertical (role uplift) via parameter tampering and role-assignment endpoints.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-api-enum`, `recon-sitemap-crawl`, `mcp-burp`.

Use this skill against a multi-tenant application that exposes role or ownership assignment flows — for example, a SaaS product where users can update their profiles, invite others to workspaces, or transfer resource ownership. The goal is to determine whether the server enforces role boundaries server-side or naively trusts client-supplied role fields.

## Signal to look for

- Profile-update endpoints (`PATCH /api/users/me`, `PUT /api/profile`) that include a `role` or `isAdmin` field in the request or response body.
- Tenant-switching APIs that accept a tenant or organization identifier as a parameter.
- Invite and permission-grant endpoints that allow the caller to specify a target role for the invitee.
- Ownership-transfer endpoints that accept a `userId`, `ownerId`, or `transferTo` field the client can manipulate.

## Test steps

1. Authenticate as a low-privileged user and capture a profile-update request using the Burp proxy (`mcp-burp`).
2. Add `role=admin` or `isAdmin=true` to the request body and replay the mutated request via `burp_repeater_send`.
3. Check the resulting permissions by issuing a request to a known admin-only endpoint; a successful response confirms vertical privilege escalation.
4. Horizontal escalation: tamper the `userId` (or equivalent ownership identifier) to a peer user's ID and replay to confirm unauthorized cross-user write access.
5. Capture all evidence per `methodology-evidence-capture` — screenshot or save the mutated request, the server response, and the follow-up admin-endpoint proof.

## Tool commands

**Shell — send a mutated profile-update:**

```bash
curl -X PATCH \
  -H "Cookie: session=<LOWPRIV>" \
  -H "Content-Type: application/json" \
  --data '{"role":"admin"}' \
  https://target.example.com/api/users/me
# Success: 200 + account now has admin role
```

**MCP — replay mutated request in Burp Repeater:**

```
burp_repeater_send(raw_base64=<b64 of mutated profile update>, host="target.example.com", port=443, secure=true, tab_name="privesc-probe")
```

Expected envelope on success:

```json
{"ok": true, "status": 200, "body": "..."}
```

**MCP — verify admin capability after the PATCH:**

```
burp_repeater_send(raw_base64=<b64 of admin-only endpoint request>, host="target.example.com", port=443, secure=true, tab_name="privesc-admin-verify")
```

Expected envelope on success:

```json
{"ok": true, "status": 200, "body": "..."}
```

## Interpret results

A confirmed finding requires two conditions: the role-mutation PATCH returns a success response **and** a subsequent request to an admin-only endpoint succeeds with the same session.

**False positive:** the server echoes the `role` field back in the PATCH response (200 OK, body contains `"role":"admin"`) but silently ignores it — mass-assignment filtering may be stripping the value before it reaches the database. Always re-verify admin capability with a live admin-only endpoint after the PATCH rather than relying on the PATCH response body alone.

## Finding writeup

- **Title:** `Privilege Escalation via <endpoint> <parameter>` (e.g., `Privilege Escalation via PATCH /api/users/me role`).
- **Severity:**
  - Role uplift to admin or equivalent super-user = **Critical**.
  - Horizontal peer-to-peer unauthorized access = **High**.
- **Evidence** per `methodology-evidence-capture`: include the mutation request and response, then the admin-endpoint request and response that proves the gained capability.
- **Fix:** The server must never accept a role value from the client. Role assignment must be performed server-side by privileged code only. Add audit logging for all role-change events, and enforce authorization checks on every admin-only endpoint independently of how the role was set.

## References

- OWASP WSTG ATHZ-03: <https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/05-Authorization_Testing/03-Testing_for_Privilege_Escalation>
- PortSwigger Access Control: <https://portswigger.net/web-security/access-control>
- CWE-269: <https://cwe.mitre.org/data/definitions/269.html>

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
