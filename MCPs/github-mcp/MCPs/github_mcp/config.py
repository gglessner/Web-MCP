"""Configuration loader for GitHub MCP.

Loads server definitions from a JSON config file with support for:
- Multiple GitHub servers (github.com + Enterprise)
- Token resolution from environment variables or inline values
- Corporate proxy and custom CA bundle settings
- Fallback to GITHUB_TOKEN env var for single-server setup
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ProxyConfig:
    https: Optional[str] = None
    http: Optional[str] = None
    no_proxy: Optional[str] = None

    def to_dict(self) -> dict[str, str]:
        d: dict[str, str] = {}
        if self.https:
            d["https"] = self.https
        if self.http:
            d["http"] = self.http
        return d


@dataclass
class ServerConfig:
    name: str
    base_url: str
    token: str
    description: str = ""
    # Derived from base_url for URL matching (e.g. "github.com", "github.corp.com")
    hostname: str = ""


@dataclass
class AppConfig:
    servers: dict[str, ServerConfig] = field(default_factory=dict)
    default_server: str = ""
    proxy: Optional[ProxyConfig] = None
    ssl_verify: bool = True
    ca_bundle: Optional[str] = None


def _resolve_token(server_def: dict, server_name: str) -> str:
    """Resolve a PAT from either token_env (env var name) or inline token."""
    if "token_env" in server_def:
        env_name = server_def["token_env"]
        token = os.environ.get(env_name, "")
        if not token:
            print(
                f"Warning: env var '{env_name}' for server '{server_name}' is not set",
                file=sys.stderr,
            )
        return token
    return server_def.get("token", "")


def _hostname_from_base_url(base_url: str) -> str:
    """Extract hostname from a GitHub API base URL.

    https://api.github.com -> github.com
    https://github.corp.com/api/v3 -> github.corp.com
    """
    from urllib.parse import urlparse

    parsed = urlparse(base_url)
    host = parsed.hostname or ""
    if host == "api.github.com":
        return "github.com"
    return host


def load_config() -> AppConfig:
    """Load configuration from JSON file or environment variable fallback.

    Config file search order:
    1. Path in GITHUB_MCP_CONFIG env var
    2. config.json in the working directory
    3. config.json next to this module

    If no config file is found, falls back to GITHUB_TOKEN env var
    for a single github.com server.
    """
    config_path = os.environ.get("GITHUB_MCP_CONFIG")
    candidates = []
    if config_path:
        candidates.append(Path(config_path))
    candidates.append(Path.cwd() / "config.json")
    candidates.append(Path(__file__).parent.parent / "config.json")

    raw: dict = {}
    for p in candidates:
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                raw = json.load(f)
            break

    # Fallback: single github.com server from GITHUB_TOKEN env var
    if not raw:
        token = os.environ.get("GITHUB_TOKEN", "")
        base_url = os.environ.get("GITHUB_BASE_URL", "https://api.github.com")
        if not token:
            print(
                "Warning: no config.json found and GITHUB_TOKEN is not set. "
                "The MCP server will start but all API calls will fail.",
                file=sys.stderr,
            )
        return AppConfig(
            servers={
                "github.com": ServerConfig(
                    name="github.com",
                    base_url=base_url,
                    token=token,
                    description="GitHub.com",
                    hostname=_hostname_from_base_url(base_url),
                )
            },
            default_server="github.com",
        )

    # Parse proxy settings
    proxy = None
    if "proxy" in raw:
        p = raw["proxy"]
        proxy = ProxyConfig(
            https=p.get("https") or os.environ.get("HTTPS_PROXY"),
            http=p.get("http") or os.environ.get("HTTP_PROXY"),
            no_proxy=p.get("no_proxy") or os.environ.get("NO_PROXY"),
        )
    else:
        https_proxy = os.environ.get("HTTPS_PROXY")
        http_proxy = os.environ.get("HTTP_PROXY")
        if https_proxy or http_proxy:
            proxy = ProxyConfig(https=https_proxy, http=http_proxy)

    ssl_verify = raw.get("ssl_verify", True)
    ca_bundle = raw.get("ca_bundle") or os.environ.get("REQUESTS_CA_BUNDLE")

    # Parse servers
    servers: dict[str, ServerConfig] = {}
    for name, sdef in raw.get("servers", {}).items():
        token = _resolve_token(sdef, name)
        base_url = sdef.get("base_url", "https://api.github.com")
        servers[name] = ServerConfig(
            name=name,
            base_url=base_url,
            token=token,
            description=sdef.get("description", ""),
            hostname=_hostname_from_base_url(base_url),
        )

    default_server = raw.get("default_server", "")
    if not default_server and servers:
        default_server = next(iter(servers))

    return AppConfig(
        servers=servers,
        default_server=default_server,
        proxy=proxy,
        ssl_verify=ssl_verify,
        ca_bundle=ca_bundle,
    )
