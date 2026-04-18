"""Credential placeholder expansion (tool inputs) and literal redaction (tool outputs)."""
from __future__ import annotations

import base64
import re
from typing import Any

from common.engagement import Engagement
from common.mcp_armor import ContentFilter, FilterConfig, FilterPattern


_PLACEHOLDER = re.compile(r"\{\{CRED:([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)\}\}")


class UnknownPlaceholder(ValueError):
    pass


class CredStore:
    def __init__(self, engagement: Engagement | None):
        self._eng = engagement
        self._filter: ContentFilter | None = None
        if engagement is not None:
            self._rebuild_filter()

    # ── expansion (tool inputs) ──────────────────────────────────────
    def expand(self, obj: Any) -> Any:
        if self._eng is None:
            return obj
        return self._walk(obj)

    def _walk(self, obj: Any) -> Any:
        if isinstance(obj, str):
            return self._expand_str(obj)
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                if k == "raw_base64" and isinstance(v, str):
                    try:
                        decoded = base64.b64decode(v).decode("latin-1")
                        out[k] = base64.b64encode(
                            self._expand_str(decoded).encode("latin-1")
                        ).decode("ascii")
                        continue
                    except Exception:
                        pass
                out[k] = self._walk(v)
            return out
        if isinstance(obj, list):
            return [self._walk(x) for x in obj]
        return obj

    def _expand_str(self, s: str) -> str:
        def sub(m: re.Match) -> str:
            name, field = m.group(1), m.group(2)
            val = self._eng.credential(name, field)
            if val is None:
                raise UnknownPlaceholder(f"{{{{CRED:{name}.{field}}}}}")
            return str(val)
        return _PLACEHOLDER.sub(sub, s)

    # ── redaction (tool outputs) ─────────────────────────────────────
    def _rebuild_filter(self) -> None:
        patterns: list[FilterPattern] = []
        for cname, fields in self._eng.credentials().items():
            for fname, val in fields.items():
                if not val:
                    continue
                patterns.append(FilterPattern(
                    name=f"cred.{cname}.{fname}",
                    pattern=re.escape(str(val)),
                    replacement=f"[REDACTED:CRED:{cname}.{fname}]",
                    enabled=True,
                ))
        for iname, ident in self._eng.identities().items():
            for c in ident.get("cookies", []):
                v = c.get("value")
                if v:
                    patterns.append(FilterPattern(
                        name=f"ident.{iname}.cookie",
                        pattern=re.escape(str(v)),
                        replacement=f"[REDACTED:IDENT:{iname}.cookie]",
                        enabled=True,
                    ))
            for v in (ident.get("headers") or {}).values():
                if v:
                    patterns.append(FilterPattern(
                        name=f"ident.{iname}.header",
                        pattern=re.escape(str(v)),
                        replacement=f"[REDACTED:IDENT:{iname}.header]",
                        enabled=True,
                    ))
        self._filter = ContentFilter(
            FilterConfig(patterns=patterns, sensitive_keys=[], dry_run=False)
        )

    def refresh_identities(self) -> None:
        if self._eng is not None:
            self._rebuild_filter()

    def filter(self, obj: Any) -> Any:
        if self._filter is None:
            return obj
        filtered, _ = self._filter.filter(obj)
        return filtered
