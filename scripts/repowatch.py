#!/usr/bin/env python3
"""RepoWatch launcher for the Claude plugin.

Puts the bundled package source (../src) on sys.path and runs the CLI, so the
plugin works from a fresh install with no `pip install` step. Standard library
only; RepoWatch itself has no third-party dependencies.
"""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info < (3, 11):
    sys.exit(f"RepoWatch needs Python 3.11 or newer (found {sys.version.split()[0]}).")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from repowatch.cli import main  # noqa: E402

raise SystemExit(main())
