"""Multi-server GitHub client manager.

Handles lazy initialization, caching, proxy/TLS configuration,
and URL-to-server resolution for multiple GitHub instances.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from github import Auth, Github, GithubException

from .config import AppConfig, ServerConfig


@dataclass
class RepoRef:
    """Resolved reference to a repository on a specific server."""

    client: Github
    owner: str
    repo: str
    server_name: str


class GitHubClients:
    """Manages PyGithub client instances for multiple GitHub servers."""

    def __init__(self, config: AppConfig):
        self._config = config
        self._clients: dict[str, Github] = {}

    @property
    def config(self) -> AppConfig:
        return self._config

    def get_client(self, server_name: Optional[str] = None) -> Github:
        """Get or create a PyGithub client for the named server."""
        name = server_name or self._config.default_server
        if not name or name not in self._config.servers:
            available = ", ".join(self._config.servers.keys()) or "(none)"
            raise ValueError(
                f"Unknown server '{name}'. Available servers: {available}"
            )

        if name not in self._clients:
            self._clients[name] = self._create_client(self._config.servers[name])
        return self._clients[name]

    def resolve_repo_url(self, repo_url: str) -> RepoRef:
        """Parse a GitHub repo URL and resolve it to a client + owner/repo.

        Accepts URLs like:
            https://github.com/owner/repo
            https://github.com/owner/repo/tree/main/src
            https://github.corp.com/org/project
        """
        parsed = urlparse(repo_url)
        url_host = parsed.hostname or ""

        # Normalize: api.github.com -> github.com
        if url_host == "api.github.com":
            url_host = "github.com"

        # Find matching server by hostname
        matched_name: Optional[str] = None
        for name, server in self._config.servers.items():
            if server.hostname == url_host:
                matched_name = name
                break

        if not matched_name:
            available = {s.hostname: n for n, s in self._config.servers.items()}
            raise ValueError(
                f"No configured server matches hostname '{url_host}'. "
                f"Configured hostnames: {available}"
            )

        # Extract owner/repo from path: /owner/repo[/...]
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(path_parts) < 2:
            raise ValueError(
                f"Cannot extract owner/repo from URL '{repo_url}'. "
                f"Expected format: https://<host>/owner/repo"
            )

        owner = path_parts[0]
        repo = path_parts[1]
        # Strip .git suffix if present
        if repo.endswith(".git"):
            repo = repo[:-4]

        client = self.get_client(matched_name)
        return RepoRef(
            client=client, owner=owner, repo=repo, server_name=matched_name
        )

    def list_servers(self) -> list[dict]:
        """Return metadata for all configured servers."""
        result = []
        for name, server in self._config.servers.items():
            result.append(
                {
                    "name": name,
                    "hostname": server.hostname,
                    "base_url": server.base_url,
                    "description": server.description,
                    "is_default": name == self._config.default_server,
                    "authenticated": bool(server.token),
                }
            )
        return result

    def _create_client(self, server: ServerConfig) -> Github:
        """Create and configure a PyGithub client with proxy/TLS settings."""
        auth = Auth.Token(server.token) if server.token else None

        kwargs: dict = {"auth": auth, "per_page": 100}
        if server.base_url != "https://api.github.com":
            kwargs["base_url"] = server.base_url

        g = Github(**kwargs)

        # Apply proxy and SSL settings to the internal requests session
        self._configure_session(g)
        return g

    def _configure_session(self, client: Github) -> None:
        """Apply proxy, CA bundle, and SSL verify to PyGithub's internal session."""
        try:
            session = client._Github__requester._Requester__session
        except AttributeError:
            return

        cfg = self._config

        if cfg.proxy and cfg.proxy.to_dict():
            session.proxies.update(cfg.proxy.to_dict())

        if cfg.ca_bundle:
            session.verify = cfg.ca_bundle
        elif not cfg.ssl_verify:
            session.verify = False

        if cfg.proxy and cfg.proxy.no_proxy:
            import os
            os.environ.setdefault("NO_PROXY", cfg.proxy.no_proxy)
