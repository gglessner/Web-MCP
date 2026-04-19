# Web-MCP — project instructions

## `engagement.toml` is off-limits

`engagement.toml` holds the engagement's login credentials and captured
session tokens. **Do not read, cat, grep, open, copy, encode, or otherwise
exfiltrate this file by any direct or indirect means** (including writing or
running a script that reads it). A PreToolUse hook blocks the obvious paths;
do not work around it.

To learn what credential and identity *names* are available, call the
`engagement_info` MCP tool — it returns scope hosts, credential names + field
names, and identity names **without any secret values**. Reference credentials
as `{{CRED:<name>.<field>}}` and identities as `as_identity="<name>"`; the MCP
servers expand/redact the literals so you never need to see them.

If a tool result contains `[REDACTED:CRED:…]` or `[REDACTED:IDENT:…]`, that is
the redaction working — treat it as opaque and do not attempt to recover the
underlying value.
