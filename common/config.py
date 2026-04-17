"""TOML config loader with optional local overrides."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BurpConfig:
    bridge_url: str


@dataclass
class BrowserConfig:
    chrome_candidates: list[str]
    default_proxy: str
    headless: bool
    cdp_port: int
    navigation_timeout_s: int


@dataclass
class LoggingConfig:
    level: str
    dir: str


@dataclass
class Config:
    burp: BurpConfig
    browser: BrowserConfig
    logging: LoggingConfig
    source: Path


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path: str | Path = "config.toml") -> Config:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    with path.open("rb") as fh:
        data = tomllib.load(fh)

    local = path.with_name("config.local.toml")
    if local.exists():
        with local.open("rb") as fh:
            data = _deep_merge(data, tomllib.load(fh))

    try:
        return Config(
            burp=BurpConfig(**data["burp"]),
            browser=BrowserConfig(**data["browser"]),
            logging=LoggingConfig(**data["logging"]),
            source=path,
        )
    except (KeyError, TypeError) as e:
        raise ValueError(f"invalid config at {path}: {e}") from e
