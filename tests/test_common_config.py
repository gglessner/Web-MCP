from pathlib import Path

import pytest

from common.config import Config, load_config


def test_load_config_reads_toml(tmp_path: Path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        """
        [burp]
        bridge_url = "http://127.0.0.1:9999"

        [browser]
        chrome_candidates = ["chromium"]
        default_proxy = "127.0.0.1:8080"
        headless = true
        cdp_port = 9222
        navigation_timeout_s = 10
        user_data_dir_root = "/tmp"

        [logging]
        level = "DEBUG"
        dir = "logs"

        [evidence]
        dir = "evidence"
        """
    )
    cfg = load_config(cfg_file)
    assert isinstance(cfg, Config)
    assert cfg.burp.bridge_url == "http://127.0.0.1:9999"
    assert cfg.browser.headless is True
    assert cfg.browser.navigation_timeout_s == 10
    assert cfg.browser.user_data_dir_root == "/tmp"
    assert cfg.logging.level == "DEBUG"


def test_load_config_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nope.toml")


def test_load_config_local_override(tmp_path: Path):
    base = tmp_path / "config.toml"
    base.write_text(
        """
        [burp]
        bridge_url = "http://127.0.0.1:8775"
        [browser]
        chrome_candidates = ["chromium"]
        default_proxy = "127.0.0.1:8080"
        headless = false
        cdp_port = 9222
        navigation_timeout_s = 30
        user_data_dir_root = "/tmp"
        [logging]
        level = "INFO"
        dir = "logs"
        [evidence]
        dir = "evidence"
        """
    )
    local = tmp_path / "config.local.toml"
    local.write_text(
        """
        [browser]
        headless = true
        """
    )
    cfg = load_config(base)
    assert cfg.browser.headless is True
    assert cfg.burp.bridge_url == "http://127.0.0.1:8775"  # unchanged


def test_deep_merge_recurses_past_one_level():
    from common.config import _deep_merge
    base = {"a": {"b": {"c": 1, "d": 2}, "e": 3}, "f": 4}
    override = {"a": {"b": {"c": 99}}}
    result = _deep_merge(base, override)
    assert result == {"a": {"b": {"c": 99, "d": 2}, "e": 3}, "f": 4}


def test_deep_merge_list_replaces_not_appends():
    from common.config import _deep_merge
    base = {"xs": [1, 2, 3]}
    override = {"xs": [4]}
    result = _deep_merge(base, override)
    assert result == {"xs": [4]}


def test_load_config_raises_valueerror_on_malformed_section(tmp_path: Path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        """
        [burp]
        bridge_url = "http://127.0.0.1:8775"
        [browser]
        chrome_candidates = ["chromium"]
        default_proxy = "127.0.0.1:8080"
        headless = false
        cdp_port = 9222
        navigation_timeout_s = 30
        user_data_dir_root = "/tmp"
        [logging]
        wrong_key = "INFO"
        dir = "logs"
        [evidence]
        dir = "evidence"
        """
    )
    with pytest.raises(ValueError, match="invalid config"):
        load_config(cfg_file)


def test_load_config_reads_evidence_section(tmp_path: Path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        """
        [burp]
        bridge_url = "http://127.0.0.1:8775"
        [browser]
        chrome_candidates = ["chromium"]
        default_proxy = "127.0.0.1:8080"
        headless = false
        cdp_port = 9222
        navigation_timeout_s = 30
        user_data_dir_root = "/tmp"
        [logging]
        level = "INFO"
        dir = "logs"
        [evidence]
        dir = "evidence"
        """
    )
    cfg = load_config(cfg_file)
    assert cfg.evidence.dir == "evidence"


def test_load_config_missing_evidence_raises(tmp_path: Path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        """
        [burp]
        bridge_url = "http://127.0.0.1:8775"
        [browser]
        chrome_candidates = ["chromium"]
        default_proxy = "127.0.0.1:8080"
        headless = false
        cdp_port = 9222
        navigation_timeout_s = 30
        user_data_dir_root = "/tmp"
        [logging]
        level = "INFO"
        dir = "logs"
        """
    )
    with pytest.raises(ValueError, match="invalid config"):
        load_config(cfg_file)


def test_config_dataclasses_are_frozen(tmp_path: Path):
    import dataclasses
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        '[burp]\nbridge_url="x"\n[browser]\nchrome_candidates=["c"]\n'
        'default_proxy="p"\nheadless=false\ncdp_port=1\nnavigation_timeout_s=1\n'
        'user_data_dir_root="/tmp"\n'
        '[logging]\nlevel="INFO"\ndir="logs"\n[evidence]\ndir="evidence"\n'
    )
    cfg = load_config(cfg_file)
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.burp.bridge_url = "y"
