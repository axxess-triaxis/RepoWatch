"""Unmasked PII scan.

Regex-based, over tracked text files only (binary/large files skipped by
extension + a size cap, not fetched at all -- keeps this cheap and avoids
pulling real binary blobs through the API). Patterns are intentionally
conservative (favor false positives over silently missing something): a
flagged match is a *candidate* for a human to confirm, not an automatic
verdict, and match content itself is never printed in full -- only a masked
excerpt, so running this check doesn't itself become a way to leak PII into
a report or a terminal log.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..github_client import gh_json

MAX_FILES = 80  # each file is a separate `gh api` subprocess call -- keep this
# bounded so an org-wide audit finishes in minutes, not the better part of an
# hour. Real coverage tradeoff, stated plainly in README's limitations section
# rather than left implicit.
MAX_FILE_BYTES = 200_000
SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf", ".zip", ".woff",
    ".woff2", ".ttf", ".eot", ".mp4", ".mp3", ".lock",
}
SKIP_PATH_SUBSTRINGS = ("node_modules/", "dist/", "build/", ".git/", "vendor/")

PATTERNS: dict[str, re.Pattern] = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "phone_us": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "ssn_us": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "aadhaar_in": re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
}
# Files that legitimately contain "emails" without being a leak: test fixtures,
# example/sample data explicitly marked as such.
BENIGN_PATH_HINTS = ("test", "spec", "fixture", "example", "sample", ".md")


def _mask(match_text: str) -> str:
    if len(match_text) <= 4:
        return "*" * len(match_text)
    return match_text[:2] + "*" * (len(match_text) - 4) + match_text[-2:]


@dataclass
class PiiFinding:
    repo: str
    path: str
    kind: str
    masked_excerpt: str
    likely_benign: bool


@dataclass
class PiiResult:
    repo: str
    findings: list[PiiFinding] = field(default_factory=list)
    files_scanned: int = 0
    error: str | None = None


def check(org: str, repo: str, branch: str | None = None) -> PiiResult:
    result = PiiResult(repo=repo)
    try:
        if branch is None:
            # The trees API needs a real ref (a branch name, tag, or SHA) --
            # the literal string "HEAD" 404s. Resolve the repo's actual
            # default branch first rather than assuming "main".
            repo_info = gh_json(["api", f"repos/{org}/{repo}"])
            branch = (repo_info or {}).get("default_branch", "main")
        tree = gh_json(
            ["api", f"repos/{org}/{repo}/git/trees/{branch}", "-X", "GET", "-f", "recursive=true"]
        )
    except Exception as e:  # noqa: BLE001
        result.error = str(e)
        return result

    entries = (tree or {}).get("tree", [])
    candidates = [
        e for e in entries
        if e.get("type") == "blob"
        and e.get("size", 0) <= MAX_FILE_BYTES
        and not any(e["path"].lower().endswith(ext) for ext in SKIP_EXTENSIONS)
        and not any(s in e["path"] for s in SKIP_PATH_SUBSTRINGS)
    ][:MAX_FILES]

    for entry in candidates:
        path = entry["path"]
        try:
            blob = gh_json(["api", f"repos/{org}/{repo}/git/blobs/{entry['sha']}"])
        except Exception:  # noqa: BLE001 -- one unreadable blob shouldn't kill the scan
            continue
        if not blob or blob.get("encoding") != "base64":
            continue

        import base64

        try:
            content = base64.b64decode(blob["content"]).decode("utf-8", errors="ignore")
        except Exception:  # noqa: BLE001
            continue

        result.files_scanned += 1
        likely_benign = any(hint in path.lower() for hint in BENIGN_PATH_HINTS)

        for kind, pattern in PATTERNS.items():
            m = pattern.search(content)
            if m:
                result.findings.append(
                    PiiFinding(
                        repo=repo,
                        path=path,
                        kind=kind,
                        masked_excerpt=_mask(m.group(0)),
                        likely_benign=likely_benign,
                    )
                )

    return result
