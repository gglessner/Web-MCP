"""Configuration loader for MCP Armor.

Loads filtering patterns from YAML configuration files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class FilterPattern:
    """A single filter pattern with regex and replacement."""

    name: str
    pattern: str
    replacement: str = "[REDACTED]"
    enabled: bool = True


# Default regex matched against dict keys. If a key matches and its value
# is a string, the entire value is replaced with [REDACTED] without running
# any text patterns. Suffix forms (.*_secret etc.) catch service-prefixed
# names like ``aws_secret`` or ``db_password``.
DEFAULT_SENSITIVE_KEYS = [
    r"(?i)^(password|passwd|pwd|secret|token|auth|api[_-]?key|access[_-]?key|"
    r"private[_-]?key|client[_-]?secret|.*_secret|.*_token|.*_password|.*_key)$"
]


@dataclass
class FilterConfig:
    """Configuration for the content filter."""

    patterns: list[FilterPattern] = field(default_factory=list)
    sensitive_keys: list[str] = field(default_factory=lambda: list(DEFAULT_SENSITIVE_KEYS))
    log_requests: bool = True
    log_responses: bool = True
    log_file: Optional[str] = "mcp_filter.log"
    dry_run: bool = False  # If True, don't actually redact, just log


def load_config(config_path: Optional[str] = None) -> FilterConfig:
    """Load configuration from YAML file.
    
    Config file search order:
    1. Path provided in config_path parameter
    2. Path in MCP_CONTENT_FILTER_CONFIG env var
    3. patterns.yaml in the working directory
    4. Default patterns.yaml next to this module
    
    Args:
        config_path: Optional explicit path to config file.
        
    Returns:
        FilterConfig instance with loaded patterns.
    """
    candidates = []
    if config_path:
        candidates.append(Path(config_path))
    
    env_path = os.environ.get("MCP_CONTENT_FILTER_CONFIG")
    if env_path:
        candidates.append(Path(env_path))
    
    candidates.append(Path.cwd() / "patterns.yaml")
    candidates.append(Path(__file__).parent / "patterns.yaml")
    
    raw = {}
    for p in candidates:
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
            break
    
    # Parse patterns
    patterns = []
    for p in raw.get("patterns", []):
        patterns.append(FilterPattern(
            name=p.get("name", "unnamed"),
            pattern=p.get("pattern", ""),
            replacement=p.get("replacement", "[REDACTED]"),
            enabled=p.get("enabled", True),
        ))
    
    sensitive_keys = raw.get("sensitive_keys")
    if sensitive_keys is None:
        sensitive_keys = list(DEFAULT_SENSITIVE_KEYS)

    return FilterConfig(
        patterns=patterns,
        sensitive_keys=sensitive_keys,
        log_requests=raw.get("log_requests", True),
        log_responses=raw.get("log_responses", True),
        log_file=raw.get("log_file", "mcp_filter.log"),
        dry_run=raw.get("dry_run", False),
    )


def load_default_config() -> FilterConfig:
    """Load the built-in default configuration.

    Patterns use a named group ``(?P<secret>...)`` to mark the span that
    gets redacted. Patterns without it (standalone tokens) redact the full
    match. Whitespace between separators and values is restricted to
    ``[ \\t]*`` so patterns never jump newlines.
    """
    default_patterns = [
        # Password patterns
        FilterPattern(
            name="password",
            pattern=r"(?i)(?:password|passwd|pwd)[ \t]*[:=][ \t]*(?P<secret>\S+)",
            replacement="[REDACTED_PASSWORD]",
        ),
        FilterPattern(
            name="password_in_quotes",
            pattern=r"""(?i)["'](?:password|passwd|pwd|secret)["'][ \t]*:[ \t]*["'](?P<secret>[^"']+)["']""",
            replacement="[REDACTED]",
        ),
        FilterPattern(
            name="api_key",
            pattern=r"(?i)(?:api_key|apikey|api-key)[ \t]*[:=][ \t]*(?P<secret>\S+)",
            replacement="[REDACTED_API_KEY]",
        ),
        FilterPattern(
            name="token",
            pattern=r"(?i)(?:token|auth_token|access_token)[ \t]*[:=][ \t]*(?P<secret>\S+)",
            replacement="[REDACTED_TOKEN]",
        ),
        # GitHub tokens — standalone, whole match is the secret
        FilterPattern(
            name="github_token",
            pattern=r"gh[pousr]_[A-Za-z0-9_]{36,}",
            replacement="[REDACTED_GITHUB_TOKEN]",
        ),
        # AWS keys
        FilterPattern(
            name="aws_access_key",
            pattern=r"AKIA[0-9A-Z]{16}",
            replacement="[REDACTED_AWS_KEY]",
        ),
        FilterPattern(
            name="aws_secret_key",
            pattern=r"(?i)aws_secret_access_key[ \t]*[:=][ \t]*(?P<secret>\S+)",
            replacement="[REDACTED]",
        ),
        # Certificate passwords
        FilterPattern(
            name="cert_password",
            pattern=r"(?i)(?:cert_password|key_password|private_key_passphrase|pfx_password)[ \t]*[:=][ \t]*(?P<secret>\S+)",
            replacement="[REDACTED_CERT_PASSWORD]",
        ),
        # Generic secrets
        FilterPattern(
            name="secret",
            pattern=r"(?i)(?:secret|client_secret|app_secret)[ \t]*[:=][ \t]*(?P<secret>\S+)",
            replacement="[REDACTED_SECRET]",
        ),
        # Bearer tokens — preserve "Bearer " prefix
        FilterPattern(
            name="bearer_token",
            pattern=r"Bearer\s+(?P<secret>[A-Za-z0-9_\-\.]+)",
            replacement="[REDACTED]",
        ),
        # Basic auth — preserve "Basic " prefix
        FilterPattern(
            name="basic_auth",
            pattern=r"Basic\s+(?P<secret>[A-Za-z0-9+/=]+)",
            replacement="[REDACTED]",
        ),
    ]

    return FilterConfig(
        patterns=default_patterns,
        log_requests=True,
        log_responses=True,
        log_file="mcp_filter.log",
        dry_run=False,
    )