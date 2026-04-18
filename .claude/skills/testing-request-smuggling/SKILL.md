---
name: testing-request-smuggling
description: Test for HTTP Request Smuggling (desync) — CL.TE, TE.CL, TE.TE variants against front-end/back-end chains.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-tech-fingerprinting`, `mcp-burp`.

Target has a front-end proxy (nginx, HAProxy, CloudFront, Akamai) in front of a back-end server; the two may interpret `Content-Length` vs `Transfer-Encoding` differently.

## Signal to look for

- Both `Content-Length` and `Transfer-Encoding: chunked` accepted by the server.
- Front-end and back-end are different products (e.g. CloudFront in front of a Rails app).

## Test steps

1. Detection: send a CL.TE probe with two differently-sized headers; observe response delay or early close.
2. Confirmation: smuggle a second request and retrieve another user's response. Respect RoE — request smuggling can affect other users' traffic; see `methodology-rules-of-engagement`.
3. Use Burp's "HTTP Request Smuggler" extension for reliable probing.
4. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell:** Burp extension primary. Manual example payload:

```
POST / HTTP/1.1
Host: target.example.com
Content-Length: 13
Transfer-Encoding: chunked

0

GET /404 HTTP/1.1
X-Foo: bar
```

(`# Success: subsequent request from another client returns 404 for a different path`).

**MCP:** `burp_repeater_send(raw_base64=<b64 of crafted request>, host="target.example.com", port=443, secure=true, tab_name="smuggling-probe")`. Requires the HTTP Request Smuggler extension loaded in Burp Pro for reliable confirmation. Include `{"ok": true, ...}` envelope.

## Interpret results

Confirmed when a smuggled request affects an unrelated response (the canonical proof). Easy to false-positive — Burp extension's automated confirmation logic is the reliable signal.

## Finding writeup

- Title: `HTTP Request Smuggling (<variant>) between front-end and back-end`.
- Severity: confirmed smuggling = Critical; suspected without second-request proof = High.
- Evidence per `methodology-evidence-capture`: crafted payload, before/after HTTP transcript, Burp extension output.
- Fix: require consistent parsing; front-end should normalise (strip `Transfer-Encoding` when `Content-Length` is present, or vice versa); use HTTP/2 end-to-end.

## References

- OWASP WSTG INPV-15: `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/15-Testing_for_HTTP_Splitting_Smuggling`
- PortSwigger HTTP request smuggling: `https://portswigger.net/web-security/request-smuggling`
- CWE-444: `https://cwe.mitre.org/data/definitions/444.html`

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
