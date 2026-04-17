# browser-mcp

CDP-driven browser MCP. Launches Chrome, attaches via `--remote-debugging-port`, exposes navigation, DOM query, click, fill, JS eval, screenshot, cookies, and network log as MCP tools.

## Tools
- `browser_launch(headless?, proxy?)` — Start Chrome (idempotent).
- `browser_close()` — Terminate Chrome.
- `browser_navigate(url)` — Load URL and wait for `Page.loadEventFired`.
- `browser_snapshot()` — DOM + accessibility tree.
- `browser_query(selector)` — First match → outerHTML.
- `browser_click(selector)` / `browser_fill(selector, text)` — Interaction.
- `browser_eval(expression)` — JS eval.
- `browser_screenshot(full_page?)` — PNG base64.
- `browser_cookies(urls?)` / `browser_set_cookie(name, value, domain, ...)` — Cookies.
- `browser_network_log(since_seq?)` — Captured CDP `Network.*` events.

## Smoke test
Register with Claude Code via the example config in the workspace root. Ask Claude: *"Run browser_launch headless=true, then browser_navigate to https://example.com and screenshot. Close after."*
