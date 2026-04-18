import os
from pathlib import Path

import pytest

from common.evidence import EvidencePathError, resolve_evidence_path, write_evidence


def test_resolve_happy_path(tmp_path: Path):
    root = tmp_path / "evidence"
    p = resolve_evidence_path(root, "F-001/shot.png")
    assert p == (root / "F-001" / "shot.png").resolve()
    assert p.parent.exists()


def test_resolve_rejects_absolute(tmp_path: Path):
    root = tmp_path / "evidence"
    with pytest.raises(EvidencePathError):
        resolve_evidence_path(root, "/etc/passwd")


def test_resolve_rejects_dotdot_escape(tmp_path: Path):
    root = tmp_path / "evidence"
    with pytest.raises(EvidencePathError):
        resolve_evidence_path(root, "../outside.txt")


def test_resolve_rejects_symlink_escape(tmp_path: Path):
    root = tmp_path / "evidence"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "link").symlink_to(outside)
    with pytest.raises(EvidencePathError):
        resolve_evidence_path(root, "link/x.txt")


def test_write_evidence_writes_bytes(tmp_path: Path):
    root = tmp_path / "evidence"
    p = write_evidence(root, "F-001/req.http", b"GET / HTTP/1.1\r\n\r\n")
    assert p.read_bytes() == b"GET / HTTP/1.1\r\n\r\n"
    assert p.is_relative_to(root.resolve())


def test_write_evidence_atomic_no_partial_on_resolve_error(tmp_path: Path):
    root = tmp_path / "evidence"
    with pytest.raises(EvidencePathError):
        write_evidence(root, "../x", b"data")
    assert not (tmp_path / "x").exists()


def test_resolve_rejects_dead_symlink_escape(tmp_path: Path):
    root = tmp_path / "evidence"
    root.mkdir()
    # symlink target does NOT exist
    (root / "deadlink").symlink_to(tmp_path / "nonexistent")
    with pytest.raises(EvidencePathError):
        resolve_evidence_path(root, "deadlink/x.txt")


def test_write_evidence_cleans_tmp_on_write_failure(tmp_path: Path, monkeypatch):
    root = tmp_path / "evidence"
    def boom(src, dst):
        raise OSError("disk full")
    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError, match="disk full"):
        write_evidence(root, "F-001/x.bin", b"data")
    # No leaked .evidence-*.tmp under F-001/
    leaked = list((root / "F-001").glob(".evidence-*.tmp"))
    assert leaked == [], f"tmp file leaked: {leaked}"
