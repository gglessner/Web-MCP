"""Traversal-guarded evidence-file writer shared by browser-mcp and burp-mcp."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


class EvidencePathError(ValueError):
    """save_to is absolute or escapes the configured evidence dir."""


def resolve_evidence_path(evidence_root: Path, rel: str) -> Path:
    if os.path.isabs(rel):
        raise EvidencePathError(f"save_to must be relative, got absolute: {rel!r}")
    root = Path(evidence_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    p = (root / rel).resolve()
    if not p.is_relative_to(root):
        raise EvidencePathError(
            f"save_to escapes evidence dir {root}: {rel!r}"
        )
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def write_evidence(evidence_root: Path, rel: str, data: bytes) -> Path:
    p = resolve_evidence_path(evidence_root, rel)
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".evidence-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp, p)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return p
