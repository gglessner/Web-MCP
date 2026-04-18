---
name: testing-graphql
description: Test for GraphQL-specific flaws — introspection leakage, batching abuse, alias-based rate-limit bypass, field duplication, deep-query DoS.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-api-enum`, `mcp-burp`.

Use this skill when the target exposes a GraphQL endpoint (`/graphql`, `/api/graphql`).

## Signal to look for

`Content-Type: application/json` POST responses with `{"data": {...}}` shape; `query { __schema ... }` acceptance.

## Test steps

1. Introspection enumeration (cross-reference `recon-api-enum`).
2. Alias-based rate-limit bypass: stack 100 aliased invocations of a protected mutation in one POST.
3. Field duplication (auth bypass in some implementations): `{ me { id } me { email } me { role } }`.
4. Deep-query DoS: nested relations with cyclic types — respect RoE (DoS-adjacent; see `methodology-rules-of-engagement`).
5. Batching attack: submit an array of queries in one request.
6. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell:** curl with stacked aliases:

```
curl -X POST -H 'Content-Type: application/json' \
  --data '{"query":"{ a1: login(pass:\"p1\") a2: login(pass:\"p2\") }"}' \
  https://target.example.com/graphql
```

**MCP:** `burp_repeater_send(raw_base64=<b64 with alias-stacked query>, host="target.example.com", port=443, secure=true, tab_name="graphql-alias")`; response correlates each alias to its own result. Include `{"ok": true, ...}` envelope.

## Interpret results

Multiple alias-stacked attempts successful in one request = rate-limit bypass. Field duplication yielding different auth responses = auth flaw. Deep-query 5xx or timeout = DoS susceptibility.

## Finding writeup

- Title: `GraphQL <flaw> at <endpoint>`.
- Severity: auth-bypass via alias/field duplication = High-Critical; introspection leak = Medium; deep-query DoS = Medium.
- Evidence per `methodology-evidence-capture`: query, response, impact proof.
- Fix: disable introspection in production; query depth/complexity limits; per-field authorization checks; rate-limit at the field-execution layer.

## References

- OWASP API Security Top 10: `https://owasp.org/www-project-api-security/`
- PortSwigger GraphQL: `https://portswigger.net/web-security/graphql`
- CWE-863: `https://cwe.mitre.org/data/definitions/863.html`

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
