"""Shared MCP helpers: error envelope + stdio server boilerplate."""
from __future__ import annotations

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    BURP_UNAVAILABLE = "BURP_UNAVAILABLE"
    TARGET_NOT_ATTACHED = "TARGET_NOT_ATTACHED"
    PRO_REQUIRED = "PRO_REQUIRED"
    TIMEOUT = "TIMEOUT"
    BAD_INPUT = "BAD_INPUT"
    UPSTREAM_HTTP = "UPSTREAM_HTTP"
    INTERNAL = "INTERNAL"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


def ok_envelope(data: Any) -> dict:
    return {"ok": True, "data": data}


def error_envelope(code: ErrorCode, message: str, detail: dict | None = None) -> dict:
    return {
        "ok": False,
        "error": {
            "code": code.value,
            "message": message,
            "detail": detail or {},
        },
    }
