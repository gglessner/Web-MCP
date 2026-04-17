"""Tests package conftest: ensure tests.fixtures is importable."""
import sys
from pathlib import Path

_root = str(Path(__file__).parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

# Pre-register tests.fixtures so MCPs sub-packages can't shadow it
import tests.fixtures  # noqa: E402, F401
import tests.fixtures.target_app  # noqa: E402, F401
