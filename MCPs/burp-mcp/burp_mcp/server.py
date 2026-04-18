"""burp-mcp stdio server: registers tools and dispatches via tool_handlers.handle."""
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
from common.mcp_base import ErrorCode, error_envelope
from common.oob import OOBReceiver

from .tool_handlers import handle


WORKSPACE = Path(__file__).resolve().parents[3]


def _tool_schemas() -> list[Tool]:
    return [
        Tool(name="burp_meta", description="Burp edition/version and bridge version.",
             inputSchema={"type": "object"}),
        Tool(
            name="burp_proxy_history",
            description="Paginated proxy history with optional filters (host/method/status/contains).",
            inputSchema={"type": "object", "properties": {
                "host": {"type": "string"}, "method": {"type": "string"},
                "status": {"type": "integer"}, "contains": {"type": "string"},
                "cursor": {"type": "integer"}, "limit": {"type": "integer"},
            }},
        ),
        Tool(
            name="burp_proxy_request",
            description="Full request + response for a given history id.",
            inputSchema={"type": "object", "required": ["id"], "properties": {"id": {"type": "integer"}}},
        ),
        Tool(
            name="burp_repeater_send",
            description="Send a raw request to Repeater in a new tab.",
            inputSchema={"type": "object", "required": ["raw_base64", "host", "port"], "properties": {
                "raw_base64": {"type": "string"}, "host": {"type": "string"}, "port": {"type": "integer"},
                "secure": {"type": "boolean"}, "tab_name": {"type": "string"},
                "as_identity": {"type": "string",
                                "description": "name of an [identities.*] entry in engagement.toml"},
            }},
        ),
        Tool(
            name="burp_scope_check",
            description="Test whether URLs are in scope.",
            inputSchema={"type": "object", "required": ["urls"],
                         "properties": {"urls": {"type": "array", "items": {"type": "string"}}}},
        ),
        Tool(
            name="burp_scope_modify",
            description="Add and/or remove URLs from scope.",
            inputSchema={"type": "object", "properties": {
                "add": {"type": "array", "items": {"type": "string"}},
                "remove": {"type": "array", "items": {"type": "string"}},
            }},
        ),
        Tool(
            name="burp_sitemap",
            description="Site map entries, optionally filtered by URL prefix.",
            inputSchema={"type": "object", "properties": {
                "prefix": {"type": "string"}, "cursor": {"type": "integer"}, "limit": {"type": "integer"},
            }},
        ),
        Tool(
            name="burp_scanner_scan",
            description="Start an audit (Pro only). mode: active|passive.",
            inputSchema={"type": "object", "required": ["url"], "properties": {
                "url": {"type": "string"}, "mode": {"type": "string", "enum": ["active", "passive"]},
            }},
        ),
        Tool(name="burp_scanner_issues", description="List scan issues (Pro only).",
             inputSchema={"type": "object"}),
        Tool(
            name="burp_intruder_launch",
            description="Send a raw request to Intruder (Pro only).",
            inputSchema={"type": "object", "required": ["raw_base64", "host", "port"], "properties": {
                "raw_base64": {"type": "string"}, "host": {"type": "string"}, "port": {"type": "integer"},
                "secure": {"type": "boolean"}, "tab_name": {"type": "string"},
            }},
        ),
        Tool(name="burp_match_replace_get", description="Read match-and-replace rules.",
             inputSchema={"type": "object"}),
        Tool(
            name="burp_match_replace_set",
            description="Replace match-and-replace rules with the supplied array.",
            inputSchema={"type": "object", "required": ["rules"], "properties": {"rules": {}}},
        ),
        Tool(
            name="burp_http_send",
            description=("Send a raw HTTP request through Burp and return the response "
                         "(status, headers, timing, body preview). Optional save_to "
                         "writes <stem>.request.http / <stem>.response.http under the "
                         "configured evidence dir."),
            inputSchema={"type": "object", "required": ["raw_base64", "host", "port"],
                         "properties": {
                "raw_base64": {"type": "string"}, "host": {"type": "string"},
                "port": {"type": "integer"}, "secure": {"type": "boolean"},
                "timeout_ms": {"type": "integer"},
                "preview_bytes": {"type": "integer"},
                "include_body": {"type": "boolean"},
                "save_to": {"type": "string",
                            "description": "relative path stem under evidence/, e.g. 'F-001/idor-probe'"},
                "as_identity": {"type": "string",
                                "description": "name of an [identities.*] entry in engagement.toml"},
            }},
        ),
        Tool(
            name="oob_get_payload",
            description="Get the OOB interaction domain/url to embed in blind SSRF/XXE/SQLi/cmd-injection payloads.",
            inputSchema={"type": "object"},
        ),
        Tool(
            name="oob_poll",
            description="Return OOB interactions (DNS/HTTP callbacks) received since the given id.",
            inputSchema={"type": "object", "properties": {"since_id": {"type": "integer"}}},
        ),
        Tool(
            name="burp_save_request",
            description=("Write a proxy-history entry's raw request/response to "
                         "<stem>.request.http / <stem>.response.http under the evidence dir."),
            inputSchema={"type": "object", "required": ["id", "save_to"], "properties": {
                "id": {"type": "integer"}, "save_to": {"type": "string"},
            }},
        ),
    ]


_HOST_TOOLS = {"burp_http_send", "burp_repeater_send", "burp_intruder_launch"}
_URL_TOOLS = {"burp_scanner_scan"}


async def _async_main() -> None:
    cfg = load_config(WORKSPACE / "config.toml")
    evidence_root = WORKSPACE / cfg.evidence.dir
    logger = setup_logger("burp-mcp", log_dir=WORKSPACE / cfg.logging.dir, level=cfg.logging.level)
    logger.info("startup", extra={"bridge": cfg.burp.bridge_url})

    engagement = Engagement.load(WORKSPACE / "engagement.toml")
    credstore = CredStore(engagement)
    oob = OOBReceiver(provider=engagement.oob_provider()) if engagement is not None else None

    if engagement is not None and engagement.scope_hosts():
        try:
            from common.burp_client import BurpClient
            async with BurpClient(cfg.burp.bridge_url) as c:
                urls: list[str] = []
                for h in engagement.scope_hosts():
                    if "/" in h or h.startswith("*."):
                        continue
                    urls += [f"http://{h}/", f"https://{h}/"]
                if urls:
                    await c.scope_modify(add=urls)
                    logger.info("scope pushed to Burp", extra={"urls": urls})
        except Exception as e:
            logger.warning("scope push to Burp failed", extra={"err": str(e)})

    server = Server("burp-mcp")

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

        if engagement is not None:
            host = None
            if name in _HOST_TOOLS:
                host = arguments.get("host")
            elif name in _URL_TOOLS:
                host = urlparse(arguments.get("url", "")).hostname
            if host is not None and not engagement.in_scope(host):
                return [TextContent(type="text", text=json.dumps(
                    error_envelope(ErrorCode.OUT_OF_SCOPE,
                                   f"{host!r} not in engagement.toml [scope].hosts")))]

        result = await handle(name, arguments,
                              bridge_url=cfg.burp.bridge_url,
                              evidence_root=evidence_root,
                              engagement=engagement, oob=oob)
        result = credstore.filter(result)
        return [TextContent(type="text", text=json.dumps(result))]

    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
