"""Dependabot vulnerability audit.

Real signal, not a proxy: reads the repo's actual open Dependabot alerts via
the GitHub API. Requires the authenticated token to have read access to
vulnerability alerts (the `repo` scope covers this for repos the token owner
administers; a 403 here means the token lacks that specific permission, not
that the repo has no alerts -- surfaced as a distinct finding rather than
silently reported as "clean").
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..github_client import GhError, gh_json


@dataclass
class DependabotFinding:
    repo: str
    severity: str
    package: str
    summary: str
    url: str


@dataclass
class DependabotResult:
    repo: str
    findings: list[DependabotFinding] = field(default_factory=list)
    access_denied: bool = False
    dependabot_disabled: bool = False
    error: str | None = None


def check(org: str, repo: str) -> DependabotResult:
    result = DependabotResult(repo=repo)
    try:
        # No -q filter here: `gh api --paginate` merges each page's JSON
        # array into one combined array automatically, which a jq stream
        # filter (`.[] | select(...)`) would break -- filter in Python
        # instead, on the clean merged array.
        alerts = gh_json(
            ["api", f"repos/{org}/{repo}/dependabot/alerts", "--paginate"]
        )
    except GhError as e:
        message = str(e)
        # Both cases return HTTP 403, but they're materially different
        # findings: "disabled for this repository" means the feature was
        # never turned on (no alerts exist to read, at all) -- a real
        # governance gap worth its own flag, not a permission problem.
        # A generic 403 without that phrase means the token genuinely
        # lacks access, and reporting the repo as "clean" would be wrong.
        if "disabled for this repository" in message:
            result.dependabot_disabled = True
        elif "403" in message or "Forbidden" in message:
            result.access_denied = True
        else:
            result.error = message
        return result

    if not alerts:
        return result

    raw = [a for a in alerts if a.get("state") == "open"]
    for entry in raw:
        try:
            advisory = entry["security_advisory"]
            vuln = entry["security_vulnerability"]
            result.findings.append(
                DependabotFinding(
                    repo=repo,
                    severity=vuln.get("severity", "unknown"),
                    package=vuln.get("package", {}).get("name", "unknown"),
                    summary=advisory.get("summary", ""),
                    url=entry.get("html_url", ""),
                )
            )
        except (KeyError, TypeError):
            continue
    return result
