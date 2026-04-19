"""browser-mcp stdio server: registers tools and dispatches to BrowserSession."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from urllib.parse import urlparse

from common.config import load_config
from common.credstore import CredStore, UnknownPlaceholder
from common.engagement import Engagement
from common.logging import setup_logger
from common.mcp_base import ErrorCode, error_envelope, ok_envelope

from .tools import BrowserSession


WORKSPACE = Path(__file__).resolve().parents[3]  # Web-MCP repo root


def _tool_schemas() -> list[Tool]:
    return [
        Tool(
            name="browser_launch",
            description="Launch Chrome attached to CDP. Use before other browser_* tools.",
            inputSchema={
                "type": "object",
                "properties": {
                    "headless": {"type": "boolean"},
                    "proxy": {"type": ["string", "null"], "description": "host:port or null for config default"},
                },
            },
        ),
        Tool(name="browser_close", description="Close the browser session.", inputSchema={"type": "object"}),
        Tool(
            name="browser_navigate",
            description="Navigate the current tab to a URL and wait for load event.",
            inputSchema={"type": "object", "required": ["url"], "properties": {"url": {"type": "string"}}},
        ),
        Tool(
            name="engagement_info",
            description=("Structure-only view of engagement.toml: scope hosts, credential "
                         "NAMES and FIELD NAMES (no values), identity names with cookie "
                         "count + header names, oob provider. Use this instead of reading "
                         "engagement.toml — that file contains secrets the model must not see."),
            inputSchema={"type": "object"},
        ),
        Tool(
            name="browser_capture_identity",
            description=("Capture in-scope cookies + Authorization header from the current "
                         "session and write them as [identities.<name>] in engagement.toml."),
            inputSchema={"type": "object", "required": ["name"],
                         "properties": {"name": {"type": "string"}}},
        ),
        Tool(
            name="browser_apply_identity",
            description="Load a stored identity's cookies into the browser session.",
            inputSchema={"type": "object", "required": ["name"],
                         "properties": {"name": {"type": "string"}}},
        ),
        Tool(name="browser_snapshot", description="DOM + accessibility tree snapshot.", inputSchema={"type": "object"}),
        Tool(
            name="browser_query",
            description="Return outerHTML of the first element matching a CSS selector.",
            inputSchema={"type": "object", "required": ["selector"], "properties": {"selector": {"type": "string"}}},
        ),
        Tool(
            name="browser_click",
            description="Click the first element matching a CSS selector (uses box-model centroid).",
            inputSchema={"type": "object", "required": ["selector"], "properties": {"selector": {"type": "string"}}},
        ),
        Tool(
            name="browser_fill",
            description="Focus an input and insert text.",
            inputSchema={
                "type": "object",
                "required": ["selector", "text"],
                "properties": {"selector": {"type": "string"}, "text": {"type": "string"}},
            },
        ),
        Tool(
            name="browser_eval",
            description="Evaluate a JavaScript expression in the page context.",
            inputSchema={"type": "object", "required": ["expression"], "properties": {"expression": {"type": "string"}}},
        ),
        Tool(
            name="browser_wait_for",
            description="Poll until a CSS selector is attached (or visible) in the DOM, or time out.",
            inputSchema={"type": "object", "required": ["selector"], "properties": {
                "selector": {"type": "string"},
                "timeout_s": {"type": "number"},
                "state": {"type": "string", "enum": ["attached", "visible"]},
            }},
        ),
        Tool(
            name="browser_get_response_body",
            description=("Return the response body for a CDP Network requestId from "
                         "browser_network_log. Only works while the page that made the "
                         "request is still loaded."),
            inputSchema={"type": "object", "required": ["request_id"],
                         "properties": {"request_id": {"type": "string"}}},
        ),
        Tool(
            name="browser_screenshot",
            description="Capture a PNG screenshot. Returns base64 inline, or writes to the evidence dir and returns the path when save_to is set.",
            inputSchema={"type": "object", "properties": {
                "full_page": {"type": "boolean"},
                "save_to": {"type": "string",
                            "description": "relative path under evidence/, e.g. 'F-001/shot.png'"},
            }},
        ),
        Tool(
            name="browser_cookies",
            description="List cookies (optionally scoped to URLs).",
            inputSchema={"type": "object", "properties": {"urls": {"type": "array", "items": {"type": "string"}}}},
        ),
        Tool(
            name="browser_set_cookie",
            description="Set a cookie.",
            inputSchema={
                "type": "object",
                "required": ["name", "value", "domain"],
                "properties": {
                    "name": {"type": "string"}, "value": {"type": "string"}, "domain": {"type": "string"},
                    "path": {"type": "string"}, "secure": {"type": "boolean"}, "http_only": {"type": "boolean"},
                    "same_site": {"type": "string", "enum": ["Strict", "Lax", "None"]},
                },
            },
        ),
        Tool(
            name="browser_network_log",
            description="Return Network.* CDP events captured since a sequence number.",
            inputSchema={"type": "object", "properties": {"since_seq": {"type": "integer"}}},
        ),
    ]


_SCOPE_EXEMPT = {"browser_launch", "browser_close", "browser_capture_identity",
                 "browser_apply_identity", "engagement_info"}


async def _async_main() -> None:
    cfg = load_config(WORKSPACE / "config.toml")
    logger = setup_logger("browser-mcp", log_dir=WORKSPACE / cfg.logging.dir, level=cfg.logging.level)
    logger.info("startup", extra={"cfg": str(cfg.source)})

    engagement = Engagement.load(WORKSPACE / "engagement.toml")
    credstore = CredStore(engagement)
    if engagement is not None:
        logger.info("engagement loaded", extra={"scope_hosts": engagement.scope_hosts()})

    session = BrowserSession(
        chrome_candidates=cfg.browser.chrome_candidates,
        cdp_port=cfg.browser.cdp_port,
        default_proxy=cfg.browser.default_proxy,
        user_data_dir_root=cfg.browser.user_data_dir_root,
        navigation_timeout_s=cfg.browser.navigation_timeout_s,
        evidence_root=WORKSPACE / cfg.evidence.dir,
        engagement=engagement,
    )

    server = Server("browser-mcp")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return _tool_schemas()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            arguments = credstore.expand(arguments or {})
        except UnknownPlaceholder as e:
            return [TextContent(type="text", text=json.dumps(
                error_envelope(ErrorCode.BAD_INPUT, f"unknown credential placeholder {e}")))]

        if engagement is not None and name not in _SCOPE_EXEMPT:
            host = (urlparse(arguments.get("url", "")).hostname
                    if name == "browser_navigate" else session.current_host)
            if host is not None and not engagement.in_scope(host):
                return [TextContent(type="text", text=json.dumps(
                    error_envelope(ErrorCode.OUT_OF_SCOPE,
                                   f"{host!r} not in engagement.toml [scope].hosts")))]

        try:
            if name == "browser_launch":
                result = await session.launch(
                    headless=bool(arguments.get("headless", cfg.browser.headless)),
                    proxy=arguments.get("proxy"),
                )
            elif name == "browser_close":
                result = await session.close()
            elif name == "browser_navigate":
                result = await session.navigate(arguments["url"])
            elif name == "browser_wait_for":
                result = await session.wait_for(
                    arguments["selector"],
                    timeout_s=float(arguments.get("timeout_s", 10.0)),
                    state=arguments.get("state", "attached"),
                )
            elif name == "browser_get_response_body":
                result = await session.get_response_body(arguments["request_id"])
            elif name == "browser_snapshot":
                result = await session.snapshot()
            elif name == "browser_query":
                result = await session.query(arguments["selector"])
            elif name == "browser_click":
                result = await session.click(arguments["selector"])
            elif name == "browser_fill":
                result = await session.fill(arguments["selector"], arguments["text"])
            elif name == "browser_eval":
                result = await session.eval_js(arguments["expression"])
            elif name == "browser_screenshot":
                result = await session.screenshot(
                    full_page=bool(arguments.get("full_page", False)),
                    save_to=arguments.get("save_to"),
                )
            elif name == "browser_cookies":
                result = await session.cookies(urls=arguments.get("urls"))
            elif name == "browser_set_cookie":
                result = await session.set_cookie(
                    name=arguments["name"], value=arguments["value"], domain=arguments["domain"],
                    path=arguments.get("path", "/"),
                    secure=bool(arguments.get("secure", False)),
                    http_only=bool(arguments.get("http_only", False)),
                    same_site=arguments.get("same_site"),
                )
            elif name == "browser_network_log":
                result = session.network_log(since_seq=int(arguments.get("since_seq", 0)))
            elif name == "engagement_info":
                result = (ok_envelope(engagement.info()) if engagement is not None
                          else error_envelope(ErrorCode.BAD_INPUT, "no engagement.toml loaded"))
            elif name == "browser_capture_identity":
                result = await session.capture_identity(arguments["name"])
                credstore.refresh_identities()
            elif name == "browser_apply_identity":
                result = await session.apply_identity(arguments["name"])
            else:
                result = error_envelope(ErrorCode.BAD_INPUT, f"unknown tool: {name}")
        except Exception as e:
            logger.exception("tool crashed", extra={"tool": name})
            result = error_envelope(ErrorCode.INTERNAL, f"{type(e).__name__}: {e}")
        result = credstore.filter(result)
        return [TextContent(type="text", text=json.dumps(result))]

    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
