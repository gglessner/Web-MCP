# burp-mcp

MCP server wrapping Burp Suite via the `burp-mcp-bridge` Kotlin extension.

## Setup
1. Build the Kotlin extension (see `burp-ext/BUILD.md`).
2. Load the jar in Burp (Extensions → Add → Java).
3. Verify: `curl -s http://127.0.0.1:8775/meta`.
4. Register this MCP in Claude Code (see top-level `claude_config.example.json`).

## Tools
- Read: `burp_meta`, `burp_proxy_history`, `burp_proxy_request`, `burp_sitemap`, `burp_match_replace_get`, `burp_scope_check`.
- Write (active testing): `burp_repeater_send`, `burp_scope_modify`, `burp_match_replace_set`.
- Pro-only: `burp_scanner_scan`, `burp_scanner_issues`, `burp_intruder_launch`. On Community these return `PRO_REQUIRED`.
