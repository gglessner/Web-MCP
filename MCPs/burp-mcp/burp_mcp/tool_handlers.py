"""Tool dispatcher: map MCP tool name → BurpClient call → ok/error envelope."""
from __future__ import annotations

from typing import Any

from common.burp_client import (
    BurpBadInput,
    BurpClient,
    BurpClientError,
    BurpProRequired,
    BurpUnavailable,
    BurpUpstreamError,
)
from common.mcp_base import ErrorCode, error_envelope, ok_envelope


async def handle(tool: str, args: dict, *, bridge_url: str) -> dict:
    try:
        async with BurpClient(bridge_url) as c:
            if tool == "burp_meta":
                return ok_envelope(await c.meta())
            if tool == "burp_proxy_history":
                return ok_envelope(await c.proxy_history(
                    host=args.get("host"),
                    method=args.get("method"),
                    status=args.get("status"),
                    contains=args.get("contains"),
                    cursor=int(args.get("cursor", 0)),
                    limit=int(args.get("limit", 50)),
                ))
            if tool == "burp_proxy_request":
                return ok_envelope(await c.proxy_request(int(args["id"])))
            if tool == "burp_repeater_send":
                return ok_envelope(await c.repeater_send(
                    raw_base64=args["raw_base64"], host=args["host"], port=int(args["port"]),
                    secure=bool(args.get("secure", True)), tab_name=args.get("tab_name"),
                ))
            if tool == "burp_scope_check":
                return ok_envelope(await c.scope_check(list(args.get("urls", []))))
            if tool == "burp_scope_modify":
                return ok_envelope(await c.scope_modify(
                    add=list(args.get("add", [])), remove=list(args.get("remove", []))
                ))
            if tool == "burp_sitemap":
                return ok_envelope(await c.sitemap(
                    prefix=args.get("prefix"),
                    cursor=int(args.get("cursor", 0)),
                    limit=int(args.get("limit", 200)),
                ))
            if tool == "burp_scanner_scan":
                return ok_envelope(await c.scanner_scan(
                    url=args["url"], mode=args.get("mode", "active")
                ))
            if tool == "burp_scanner_issues":
                return ok_envelope(await c.scanner_issues())
            if tool == "burp_intruder_launch":
                return ok_envelope(await c.intruder_launch(
                    raw_base64=args["raw_base64"], host=args["host"], port=int(args["port"]),
                    secure=bool(args.get("secure", True)), tab_name=args.get("tab_name"),
                ))
            if tool == "burp_match_replace_get":
                return ok_envelope(await c.match_replace_get())
            if tool == "burp_match_replace_set":
                return ok_envelope(await c.match_replace_set(args["rules"]))
            return error_envelope(ErrorCode.BAD_INPUT, f"unknown tool: {tool}")
    except BurpProRequired as e:
        return error_envelope(ErrorCode.PRO_REQUIRED, str(e))
    except BurpBadInput as e:
        return error_envelope(ErrorCode.BAD_INPUT, str(e))
    except BurpUnavailable as e:
        return error_envelope(ErrorCode.BURP_UNAVAILABLE, str(e))
    except BurpUpstreamError as e:
        return error_envelope(ErrorCode.UPSTREAM_HTTP, str(e))
    except BurpClientError as e:
        return error_envelope(ErrorCode.UPSTREAM_HTTP, str(e))
    except Exception as e:
        return error_envelope(ErrorCode.INTERNAL, f"{type(e).__name__}: {e}")
