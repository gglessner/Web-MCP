"""Per-engagement scope, credentials, and identity store backed by engagement.toml."""
from __future__ import annotations

import ipaddress
import os
import tempfile
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import tomli_w


class Engagement:
    def __init__(self, path: Path, data: dict[str, Any]):
        self._path = Path(path)
        self._data = data
        self._scope = [str(h) for h in data.get("scope", {}).get("hosts", [])]

    @classmethod
    def load(cls, path: str | Path = "engagement.toml") -> "Engagement | None":
        p = Path(path)
        if not p.exists():
            return None
        with p.open("rb") as fh:
            return cls(p, tomllib.load(fh))

    # ── scope ────────────────────────────────────────────────────────
    @staticmethod
    def _hostname(host_or_url: str) -> str:
        if "://" in host_or_url:
            return urlparse(host_or_url).hostname or ""
        return host_or_url.split(":", 1)[0]

    def in_scope(self, host_or_url: str) -> bool:
        host = self._hostname(host_or_url)
        if not host:
            return False
        for entry in self._scope:
            if entry.startswith("*."):
                if host.endswith(entry[1:]) and host != entry[2:]:
                    return True
            elif "/" in entry:
                try:
                    if ipaddress.ip_address(host) in ipaddress.ip_network(entry, strict=False):
                        return True
                except ValueError:
                    pass
            elif host == entry:
                return True
        return False

    def scope_hosts(self) -> list[str]:
        return list(self._scope)

    # ── credentials / identities ─────────────────────────────────────
    def credentials(self) -> dict[str, dict[str, str]]:
        return {k: dict(v) for k, v in self._data.get("credentials", {}).items()}

    def credential(self, name: str, field: str) -> str | None:
        return self._data.get("credentials", {}).get(name, {}).get(field)

    def identities(self) -> dict[str, dict[str, Any]]:
        return {k: dict(v) for k, v in self._data.get("identities", {}).items()}

    def identity(self, name: str) -> dict[str, Any] | None:
        ident = self._data.get("identities", {}).get(name)
        return dict(ident) if ident is not None else None

    def oob_provider(self) -> str:
        return self._data.get("oob", {}).get("provider", "interactsh")

    def info(self) -> dict[str, Any]:
        """Structure-only summary safe to return to the LLM — no secret values."""
        creds = {name: sorted(fields) for name, fields in self.credentials().items()}
        idents: dict[str, Any] = {}
        for name, ident in self.identities().items():
            idents[name] = {
                "cookies": len(ident.get("cookies", [])),
                "headers": sorted((ident.get("headers") or {}).keys()),
                "captured_at": ident.get("captured_at"),
            }
        return {
            "name": self._data.get("engagement", {}).get("name"),
            "scope_hosts": self.scope_hosts(),
            "credentials": creds,
            "identities": idents,
            "oob_provider": self.oob_provider(),
        }

    # ── identity write (atomic) ──────────────────────────────────────
    def write_identity(self, name: str, *, cookies: list[dict], headers: dict[str, str]) -> None:
        idents = self._data.setdefault("identities", {})
        idents[name] = {
            "cookies": cookies,
            "headers": headers,
            "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        fd, tmp = tempfile.mkstemp(dir=self._path.parent, prefix=".engagement-", suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as fh:
                tomli_w.dump(self._data, fh)
            os.replace(tmp, self._path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
