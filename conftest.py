"""Root conftest: ensure repo root is on sys.path for 'tests.*' package imports."""
import sys
from pathlib import Path

_root = str(Path(__file__).parent)
if _root not in sys.path:
    sys.path.insert(0, _root)
