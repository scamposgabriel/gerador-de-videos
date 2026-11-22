"""Atalho para usar a Creative Intelligence sem instalar: `py creative-intelligence/ci.py <comando>` (ver README)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from creative_intelligence.cli import main  # noqa: E402

sys.exit(main())
