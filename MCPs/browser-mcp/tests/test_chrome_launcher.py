import shutil

import pytest

from browser_mcp.chrome_launcher import (
    ChromeNotFoundError,
    build_chrome_argv,
    read_devtools_active_port,
    resolve_chrome_binary,
)


def test_build_chrome_argv_minimal():
    argv = build_chrome_argv(
        binary="chromium",
        cdp_port=9222,
        proxy=None,
        headless=False,
        user_data_dir="/tmp/p",
    )
    assert argv[0] == "chromium"
    assert "--remote-debugging-port=9222" in argv
    assert "--user-data-dir=/tmp/p" in argv
    assert "--ignore-certificate-errors" in argv
    assert "--no-first-run" in argv
    assert not any(a.startswith("--proxy-server=") for a in argv)
    assert "--headless=new" not in argv


def test_build_chrome_argv_with_proxy_and_headless():
    argv = build_chrome_argv(
        binary="chromium",
        cdp_port=9222,
        proxy="127.0.0.1:8080",
        headless=True,
        user_data_dir="/tmp/p",
    )
    assert "--proxy-server=127.0.0.1:8080" in argv
    assert "--headless=new" in argv


def test_resolve_chrome_binary_finds_existing(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda x: f"/usr/bin/{x}" if x == "chromium" else None)
    assert resolve_chrome_binary(["nope", "chromium"]) == "/usr/bin/chromium"


def test_resolve_chrome_binary_raises_when_none_found(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda x: None)
    with pytest.raises(ChromeNotFoundError):
        resolve_chrome_binary(["nope1", "nope2"])


def test_read_devtools_active_port(tmp_path):
    (tmp_path / "DevToolsActivePort").write_text("41234\n/devtools/browser/abc\n")
    assert read_devtools_active_port(str(tmp_path), timeout_s=1.0) == 41234


def test_read_devtools_active_port_timeout(tmp_path):
    with pytest.raises(TimeoutError):
        read_devtools_active_port(str(tmp_path), timeout_s=0.2)
