"""Thin wrapper around the `gh` CLI.

Uses `gh` (rather than a raw API client) because it's already authenticated
in this environment and every check in this project needs the same
credentials -- no separate token plumbing to get wrong.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass


class GhError(RuntimeError):
    pass


def gh_json(args: list[str], timeout: int = 30) -> object:
    """Run `gh <args>` and parse stdout as JSON."""
    # encoding/errors explicit: on Windows, subprocess's text=True decodes
    # with the system codepage (cp1252) by default, not UTF-8 -- and GitHub
    # API responses routinely carry real UTF-8 (emoji in descriptions,
    # non-ASCII commit authors, file content pulled during the PII scan).
    # That mismatch crashed a real full-org run with UnicodeDecodeError.
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if result.returncode != 0:
        raise GhError(f"gh {' '.join(args)} failed: {result.stderr.strip()}")
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)


def list_org_repos(org: str) -> list[str]:
    """Real repo names for an org, non-archived, non-fork by default caller's choice."""
    data = gh_json(
        ["repo", "list", org, "--limit", "200", "--json", "name,isArchived"]
    )
    return [r["name"] for r in data if not r.get("isArchived")]


@dataclass(frozen=True)
class RepoRef:
    org: str
    name: str

    @property
    def full_name(self) -> str:
        return f"{self.org}/{self.name}"
