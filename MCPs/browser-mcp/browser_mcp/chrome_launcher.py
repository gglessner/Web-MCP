"""Resolve and launch Chrome for CDP-driven automation."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class ChromeNotFoundError(RuntimeError):
    """No Chrome-compatible binary found on PATH."""


def resolve_chrome_binary(candidates: list[str]) -> str:
    """Return the first candidate resolvable via `shutil.which`."""
    for name in candidates:
        if Path(name).is_absolute() and Path(name).exists():
            return name
        found = shutil.which(name)
        if found:
            return found
    raise ChromeNotFoundError(
        f"none of {candidates} found on PATH or as absolute paths"
    )


def build_chrome_argv(
    *,
    binary: str,
    cdp_port: int,
    proxy: str | None,
    headless: bool,
    user_data_dir: str,
) -> list[str]:
    argv = [
        binary,
        f"--remote-debugging-port={cdp_port}",
        f"--user-data-dir={user_data_dir}",
        "--ignore-certificate-errors",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=InterestFeedContentSuggestions,Translate",
        "--disable-modal-dialogs",
        "about:blank",
    ]
    if proxy:
        argv.insert(1, f"--proxy-server={proxy}")
    if headless:
        argv.insert(1, "--headless=new")
    return argv


def launch_chrome(argv: list[str]) -> subprocess.Popen:
    """Spawn Chrome as a detached subprocess. Caller owns termination."""
    return subprocess.Popen(
        argv,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
