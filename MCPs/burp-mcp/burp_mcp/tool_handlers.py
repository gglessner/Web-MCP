"""Tool dispatcher: map MCP tool name → BurpClient call → ok/error envelope."""
from __future__ import annotations

import base64
from pathlib import Path

from common.burp_client import (
    BurpBadInput,
    BurpClient,
    BurpClientError,
    BurpProRequired,
    BurpUnavailable,
    BurpUpstreamError,
)
from common.evidence import EvidencePathError, write_evidence
from common.mcp_base import ErrorCode, error_envelope, ok_envelope


def _reconstruct_response(status: int | None, headers: list[dict] | None,
                          body: bytes) -> bytes:
    lines = [f"HTTP/1.1 {status if status is not None else 0}"]
    for h in headers or []:
        lines.append(f"{h.get('name')}: {h.get('value')}")
    head = ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8")
    return head + body


async def handle(tool: str, args: dict, *, bridge_url: str,
                 evidence_root: Path | None = None) -> dict:
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
            if tool == "burp_http_send":
                data = await c.http_send(
                    raw_base64=args["raw_base64"], host=args["host"],
                    port=int(args["port"]),
                    secure=bool(args.get("secure", True)),
                    timeout_ms=int(args.get("timeout_ms", 30000)),
                )
                body_b64 = data.get("body_base64") or ""
                body = base64.b64decode(body_b64) if body_b64 else b""
                preview_bytes = int(args.get("preview_bytes", 4096))
                preview = body[:preview_bytes].decode("utf-8", "replace")
                out: dict = {
                    "status": data.get("status"),
                    "time_ms": data.get("time_ms"),
                    "body_len": data.get("body_len", len(body)),
                    "headers": data.get("headers"),
                    "body_preview": preview,
                }
                if bool(args.get("include_body", False)):
                    out["body_base64"] = body_b64
                save_to = args.get("save_to")
                if save_to:
                    if evidence_root is None:
                        return error_envelope(ErrorCode.INTERNAL,
                                              "evidence_root not configured")
                    req_bytes = base64.b64decode(data.get("request_base64") or "")
                    resp_bytes = _reconstruct_response(
                        data.get("status"), data.get("headers"), body)
                    rp = write_evidence(evidence_root,
                                        f"{save_to}.request.http", req_bytes)
                    sp = write_evidence(evidence_root,
                                        f"{save_to}.response.http", resp_bytes)
                    root_parent = Path(evidence_root).resolve().parent
                    out["saved"] = {
                        "request": str(rp.relative_to(root_parent)),
                        "response": str(sp.relative_to(root_parent)),
                    }
                return ok_envelope(out)
            if tool == "burp_save_request":
                if evidence_root is None:
                    return error_envelope(ErrorCode.INTERNAL,
                                          "evidence_root not configured")
                save_to = args["save_to"]
                data = await c.proxy_request(int(args["id"]))
                req_b64 = (data.get("request") or {}).get("raw_base64") or ""
                rp = write_evidence(evidence_root,
                                    f"{save_to}.request.http",
                                    base64.b64decode(req_b64))
                root_parent = Path(evidence_root).resolve().parent
                saved: dict = {"request": str(rp.relative_to(root_parent)),
                               "response": None}
                resp = data.get("response")
                if resp and resp.get("raw_base64"):
                    sp = write_evidence(evidence_root,
                                        f"{save_to}.response.http",
                                        base64.b64decode(resp["raw_base64"]))
                    saved["response"] = str(sp.relative_to(root_parent))
                return ok_envelope({"saved": saved})
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
    except EvidencePathError as e:
        return error_envelope(ErrorCode.BAD_INPUT, str(e))
    except Exception as e:
        return error_envelope(ErrorCode.INTERNAL, f"{type(e).__name__}: {e}")
