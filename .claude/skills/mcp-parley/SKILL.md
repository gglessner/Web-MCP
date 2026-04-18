---
name: mcp-parley
description: Drive Parley-MCP for non-HTTP MiTM proxying (raw TCP/TLS, FIX, ISO 8583, LDAP) and protocol-level traffic capture, modification via Python modules, and SQLite analysis.
---

# Using parley-mcp for non-HTTP protocol penetration testing

## When to use

When the target speaks a non-HTTP protocol — FIX, ISO 8583, LDAP, SMTP,
Solace/AMQP, raw TCP/TLS, or any custom binary protocol — and you need
to intercept, inspect, and mutate traffic at the byte level. Also use
when an HTTP target needs Python-level mutation logic that goes beyond
Burp's match-replace rules (e.g. stateful de-chunking, multi-field
re-signing, custom codec transforms).

For pure HTTP targets, reach for `mcp-burp` first; Parley can handle
HTTP via `web_proxy_setup` but Burp is better suited for that workflow.

Prerequisite: `parley-mcp` registered in Claude Code (see
`MCPs/parley-mcp/README.md` and `MCPs/parley-mcp/MCP_SETUP.md`).
No `GITHUB_TOKEN` is required.

## Signal to look for

- `curl` or browser is not applicable — target does not speak HTTP.
- Target uses a known protocol: FIX (financial order routing),
  ISO 8583 (card payment messages), LDAP (directory), SMTP (mail),
  Solace PubSub+, or an in-house binary format.
- Traffic needs runtime mutation: replay with modified fields, fuzzing
  message type codes, toggling flags across multiple TCP segments.
- HTTP traffic needs Python-level header rewriting, cookie surgery, or
  security-header stripping that is too complex for Burp's rules.

## Test steps

1. For HTTP targets: call `web_proxy_setup(target_domain="target.example.com")` —
   deploys a TLS-decrypting proxy with full rewriting modules in one call.
   Point browser to the returned `http://<listen>` URL.
2. For raw protocols: call `proxy_start(target_host="<host>", target_port=<port>)`
   with `use_tls_server=true` / `use_tls_client=true` as needed.
   Note the returned `instance_id`.
3. Call `proxy_status(instance_id=<id>)` to confirm the proxy is running.
4. Route client traffic through the proxy (`localhost:<listen_port>`).
5. Call `traffic_summary(instance_id=<id>)` — confirm messages are
   being captured.
6. Call `traffic_query(instance_id=<id>, decode_as="hexdump")` to inspect
   raw traffic; use `decode_as="utf8"` for text-based protocols.
7. Call `traffic_search(instance_id=<id>, pattern="<keyword>")` to locate
   specific messages (e.g. a field value, an error code, an auth token).
8. Write a mutation module: call `module_create(name="FuzzMsgType",
   direction="client", code="def module_function(...): ...")`.
   The function signature must be
   `module_function(message_num, source_ip, source_port, dest_ip, dest_port, message_data) -> bytearray`.
9. Re-route traffic; call `traffic_query` again with `show_modified=true`
   to compare original vs modified bytes.
10. Iterate: use `module_update(module_id=<id>, code=<new_code>)` to
    refine the mutation without restarting the proxy.
11. Call `traffic_clear(instance_id=<id>)` between test iterations for a
    clean capture.
12. Call `proxy_stop(instance_id=<id>)` when the session is complete.

## Tool commands

```
# --- Lifecycle ---

# Quick HTTP proxy (one-call setup)
web_proxy_setup(target_domain="target.example.com", listen_port=8080)
# Success: plain text summary with instance_id, proxy URL, module IDs

# Raw TCP proxy (e.g. FIX on port 4000)
proxy_start(target_host="fix-gateway.example.com", target_port=4000,
            listen_host="localhost", listen_port=9000, name="fix-test")
# Success: plain text summary including Instance ID

proxy_list()
# Success: plain text table of all instances with status/stats

proxy_status(instance_id="<id>")
# Success: detailed status block (RUNNING/STOPPED, connection count, byte counts)

proxy_stop(instance_id="<id>")
# Success: plain text summary of closed connections and captured totals

# --- Module management ---

module_create(name="FlipMsgFlag", direction="client",
              code="""
def module_function(message_num, source_ip, source_port,
                    dest_ip, dest_port, message_data):
    data = bytearray(message_data)
    # example: flip byte 4 (message type field)
    if len(data) > 4:
        data[4] ^= 0x01
    return data
""",
              description="Flip bit 0 of byte 4 in every client message",
              instance_id="<id>")
# Success: Module ID, name, direction, status

module_list(instance_id="<id>")
# Success: plain text list of modules with ON/OFF status and priority

module_update(module_id="<mod_id>", code="def module_function(...): return message_data")
# Success: updated module summary

module_set_enabled(module_id="<mod_id>", enabled=false)
# Success: "Module '<name>' (<id>): DISABLED"

module_delete(module_id="<mod_id>")
# Success: "Module deleted: '<name>' (<id>)"

# --- Traffic analysis ---

traffic_summary(instance_id="<id>")
# Success: connection count, message counts, byte volumes, timing

traffic_query(instance_id="<id>", decode_as="hexdump", limit=10, show_modified=true)
# Success: per-message block with hex dump and [MODIFIED] flag where applicable

traffic_search(instance_id="<id>", pattern="AUTH", direction="client_to_server")
# Success: matching messages with context

traffic_connections(instance_id="<id>")
# Success: per-connection endpoint and timing table

traffic_clear(instance_id="<id>")
# Success: "Traffic cleared... Messages deleted: N, Connections deleted: M"
```

## Interpret results

All Parley tools return plain text strings directly from the upstream
implementation — there is no `{"ok": ...}` envelope. Consume the text
as returned; error conditions surface as lines beginning with `ERROR:`.

Common error patterns:

- `ERROR: No running instance with ID '<id>'` — wrong id or proxy was
  never started. Confirm with `proxy_list()`.
- `ERROR: Failed to start proxy - [Errno 98] Address already in use` —
  listen port is taken. Choose a different `listen_port` or stop the
  conflicting process.
- `ERROR: Invalid module code - <message>` — Python syntax or missing
  `module_function` definition. Check the code before assuming the proxy
  is broken.
- `ERROR: No instance with ID '<id>'` — instance was cleaned up or
  wrong id.

False positive to watch for: a module compile error surfaces as an `ERROR:`
response to `module_create` or `module_update`, not as a traffic-flow
problem. If traffic is passing but not being modified as expected, call
`module_list` to confirm the module is `[ON]` and check for a prior
`module_update` that returned an error.

## Finding writeup

- **Title pattern:** `<Protocol> <Issue> in <component>` — e.g.
  "FIX Protocol: Missing Message Integrity Check Allows Order Spoofing".
- **Severity guidance:** Reference the `reporting-severity-rubric` skill.
  Unauthenticated message injection over a financial protocol is typically
  Critical; information disclosure via cleartext capture is Medium to High.
- **Description template:** *"Traffic between `<client>` and `<server>`
  over `<protocol>` was intercepted and modified using a Parley-MCP proxy.
  The `<field>` value was altered from `<original>` to `<mutated>` and the
  server accepted the message without error, demonstrating `<impact>`."*
- **Reproduction steps:** include the `proxy_start` call, the
  `module_create` code block (full `module_function` source), the
  `traffic_query` output showing the `[MODIFIED]` message, and the
  server's observed reaction.
- **Suggested fix:** implement message authentication (HMAC or TLS mutual
  auth), validate message fields server-side, and reject unexpected values.

## References

- Parley-MCP README: `MCPs/parley-mcp/README.md`
- Parley-MCP setup patterns: `MCPs/parley-mcp/MCP_SETUP.md`
- OWASP WSTG — Error Handling:
  https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/08-Testing_for_Error_Handling/
- FIX protocol specification: https://www.fixtrading.org/standards/
- ISO 8583 overview: https://www.iso.org/standard/31628.html

## Scope

This skill operates within the engagement scope established by
`methodology-scoping` and `methodology-rules-of-engagement`. Targets are
constrained mechanically via `burp_scope_check`; hosts outside Burp scope are
not tested.
