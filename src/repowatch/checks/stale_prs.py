"""Stale open PRs (>N days) and merge-without-clean-resolution detection.

Both checks read from the same `gh pr list` call since they need the same
data (open/merged PRs with timestamps and mergeable state).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..github_client import gh_json

DEFAULT_STALE_DAYS = 10


@dataclass
class StalePR:
    repo: str
    number: int
    title: str
    days_open: int
    url: str


@dataclass
class StaleResult:
    repo: str
    stale_prs: list[StalePR] = field(default_factory=list)
    error: str | None = None


def _age_days(iso_timestamp: str) -> int:
    created = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - created).days


def check_stale(org: str, repo: str, threshold_days: int = DEFAULT_STALE_DAYS) -> StaleResult:
    result = StaleResult(repo=repo)
    try:
        prs = gh_json(
            [
                "pr",
                "list",
                "--repo",
                f"{org}/{repo}",
                "--state",
                "open",
                "--limit",
                "200",
                "--json",
                "number,title,createdAt,url",
            ]
        )
    except Exception as e:  # noqa: BLE001 -- surfaced to caller as a finding, not a crash
        result.error = str(e)
        return result

    for pr in prs or []:
        age = _age_days(pr["createdAt"])
        if age > threshold_days:
            result.stale_prs.append(
                StalePR(
                    repo=repo,
                    number=pr["number"],
                    title=pr["title"],
                    days_open=age,
                    url=pr["url"],
                )
            )
    return result


@dataclass
class ConflictMergeFinding:
    repo: str
    sha: str
    message_summary: str
    url: str


@dataclass
class ConflictMergeResult:
    repo: str
    findings: list[ConflictMergeFinding] = field(default_factory=list)
    error: str | None = None


def check_conflict_merges(org: str, repo: str, lookback: int = 100) -> ConflictMergeResult:
    """Heuristic, not a certainty: flags recent merge commits on the default
    branch whose message body contains the literal "Conflicts:" marker git
    writes into a merge commit's default message when a manual merge had to
    resolve conflicting hunks. A real conflict-resolution merge that got its
    commit message edited (or was squash-merged, which discards the marker
    entirely) won't be caught -- this is a lower bound, not an exhaustive
    audit, and is reported as such in the findings.
    """
    result = ConflictMergeResult(repo=repo)
    try:
        commits = gh_json(
            [
                "api",
                f"repos/{org}/{repo}/commits",
                "-X",
                "GET",
                "-f",
                f"per_page={min(lookback, 100)}",
            ]
        )
    except Exception as e:  # noqa: BLE001
        result.error = str(e)
        return result

    for c in commits or []:
        parents = c.get("parents", [])
        message = c.get("commit", {}).get("message", "")
        if len(parents) > 1 and "Conflicts:" in message:
            result.findings.append(
                ConflictMergeFinding(
                    repo=repo,
                    sha=c["sha"][:8],
                    message_summary=message.splitlines()[0],
                    url=c.get("html_url", ""),
                )
            )
    return result
