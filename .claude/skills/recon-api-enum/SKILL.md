---
name: recon-api-enum
description: Discover and enumerate web APIs — OpenAPI/Swagger specs, GraphQL introspection, REST versioning — by probing well-known paths and inspecting proxy history.
---

# API Enumeration

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `mcp-burp`.

Use this skill when the target has a visible API surface — mobile backend,
single-page application backend, or B2B integration endpoints — and before
selecting API-specific attack classes such as BOLA/IDOR, mass assignment, or
injection. Running this skill first establishes what endpoints exist and what
authentication model protects them.

## Signal to look for

- Network tab shows JSON responses with API-shaped URLs (`/api`, `/v1`, `/graphql`).
- Responses carry `Content-Type: application/json` or `application/graphql+json`.
- CORS preflight (`OPTIONS`) responses appear in proxy history.
- A mobile application is in scope and communicates with a backend service.

## Test steps

1. Probe well-known OpenAPI/Swagger paths:

   ```
   curl -s https://target.example.com/swagger/v1/swagger.json | jq . | head -60
   curl -s https://target.example.com/openapi.json | jq .paths | head -40
   curl -s https://target.example.com/v2/api-docs | jq . | head -60
   curl -s https://target.example.com/swagger-ui.html | head -20
   curl -s https://target.example.com/api-docs | jq . | head -60
   ```

   A 200 response with a JSON body that contains `"openapi"`, `"swagger"`, or
   `"paths"` keys confirms spec exposure.

2. If a GraphQL endpoint is present (`/graphql`, `/api/graphql`), probe
   introspection:

   ```
   curl -s -X POST https://target.example.com/graphql \
     -H 'Content-Type: application/json' \
     --data '{"query":"{ __schema { types { name kind description } } }"}'
   ```

   A response containing `"__Schema"` or `"QueryType"` in the `types` array
   confirms introspection is enabled.

3. Review Burp for already-captured API traffic:

   ```
   burp_proxy_history(host="target.example.com", contains="/api", limit=100)
   ```

   Scan the returned items for unique URL prefixes, HTTP methods, and
   authentication headers to build an endpoint inventory.

4. If a spec was found in step 1: download it (`curl -o spec.json <url>`),
   summarize the available endpoints (`jq '.paths | keys' spec.json`), and
   note the declared security schemes (`jq '.components.securitySchemes' spec.json`).

5. If GraphQL introspection succeeded in step 2: save the schema response,
   extract query and mutation names, and note any directives that hint at
   access control (e.g., `@auth`, `@hasRole`).

6. Replay an interesting introspection query or spec-described endpoint via
   Burp Repeater to confirm live behavior and capture evidence:

   ```
   burp_repeater_send(raw_base64="<base64-of-full-POST-request>",
                      host="target.example.com", port=443, secure=true,
                      tab_name="api-enum-1")
   ```

## Tool commands

Shell:

```
# Probe OpenAPI/Swagger paths
curl -s https://target.example.com/swagger/v1/swagger.json | jq . | head -60
curl -s https://target.example.com/openapi.json | jq .paths | head
curl -s https://target.example.com/v2/api-docs | jq . | head -60
curl -s https://target.example.com/api-docs | jq . | head -60

# Probe GraphQL introspection
curl -s -X POST https://target.example.com/graphql \
  -H 'Content-Type: application/json' \
  --data '{"query":"{ __schema { types { name } } }"}'
```

MCP:

```
# Browse captured API traffic
burp_proxy_history(host="target.example.com", contains="/api", limit=100)
# Success: {"ok": true, "data": {"items": [...], "total": <N>, "cursor": 100}}

# Replay a request in Repeater
burp_repeater_send(raw_base64="<base64-of-full-POST-request>",
                   host="target.example.com", port=443, secure=true,
                   tab_name="api-enum-1")
# Success: {"ok": true, "data": {"tab_id": "..."}}
```

## Interpret results

**Disabled-but-leaky introspection.** Some frameworks reject the introspection
query with a 400 or a custom error, yet the error body includes type names or
field paths from the internal schema. Treat any JSON error whose shape mirrors
`{"errors": [{"message": "...", "extensions": {"code": "..."}}]}` as a partial
schema leak and enumerate the exposed names.

**Versioned REST APIs.** When `v1` and `v2` both exist, test them independently.
Older versions frequently lack rate limiting or authorization checks that were
hardened in newer releases. Finding an endpoint documented only in `v1` that
accepts the same JWT as `v2` is a high-value finding.

**Authentication models.** Identify which model the API uses before selecting
attack classes:

- `Authorization: Bearer <jwt>` — examine token claims; test for algorithm
  confusion and signature bypass.
- Session cookie — same-site cookie scope may mean CSRF is still viable.
- `X-API-Key` header — check whether the key is scoped per user or per
  application; test horizontal privilege escalation by swapping keys.

## Finding writeup

Write findings using evidence captured by this skill:

- **"Information Disclosure (API Specification)"** (Medium) — when an OpenAPI
  or Swagger spec is publicly accessible without authentication. Evidence: spec
  URL, first 60 lines of the JSON response.
- **"GraphQL Introspection Enabled"** (Medium) — when full introspection
  succeeds in a production environment, exposing the complete type system.
  Evidence: introspection URL, schema excerpt showing sensitive type names.
- **Unauthenticated sensitive endpoint** — severity High or Critical per
  `reporting-*` severity guidance, depending on data exposure.

Per `methodology-evidence-capture`: record the spec URL, the raw JSON response,
and the `burp_repeater_send` tab that reproduces the query.

## References

- OWASP API Security Top 10: https://owasp.org/www-project-api-security/
- OpenAPI/Swagger specification: https://spec.openapis.org/
- GraphQL Introspection: https://graphql.org/learn/introspection/

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
