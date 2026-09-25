"""Untested-code-on-deploy detection.

Real signal: for recent commits on the default branch, checks whether any
CI check-run for that commit references Playwright or Vitest by name (case-
insensitive substring match on the check-run's `name`). A commit with zero
matching check-runs is flagged -- either no CI ran at all, or it ran without
the test suites this org actually relies on for UI/unit coverage (per this
session's own established verification discipline: `pnpm run test`,
Playwright for UI/routing/auth changes).

This is name-based, not outcome-based on purpose: a *failing* Playwright/
Vitest run still proves the suite was invoked, which is a materially
different problem (a real failure someone should already see in CI) from
the suite never running at all, which is silent. Failing runs are reported
separately, not folded into "untested".
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..github_client import gh_json

TEST_MARKERS = ("playwright", "vitest")


@dataclass
class DeployTestFinding:
    repo: str
    sha: str
    message_summary: str
    url: str
    reason: str  # "no_test_run" or "test_run_failed"


@dataclass
class DeployTestResult:
    repo: str
    findings: list[DeployTestFinding] = field(default_factory=list)
    error: str | None = None


def check(org: str, repo: str, lookback: int = 20) -> DeployTestResult:
    result = DeployTestResult(repo=repo)
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
        sha = c["sha"]
        try:
            check_runs = gh_json(
                ["api", f"repos/{org}/{repo}/commits/{sha}/check-runs"]
            )
        except Exception:  # noqa: BLE001 -- one bad commit shouldn't kill the whole scan
            continue

        runs = (check_runs or {}).get("check_runs", [])
        matching = [r for r in runs if any(m in r.get("name", "").lower() for m in TEST_MARKERS)]

        message = c.get("commit", {}).get("message", "").splitlines()[0]
        url = c.get("html_url", "")

        if not matching:
            result.findings.append(
                DeployTestFinding(repo=repo, sha=sha[:8], message_summary=message, url=url, reason="no_test_run")
            )
        elif all(r.get("conclusion") not in ("success",) for r in matching):
            result.findings.append(
                DeployTestFinding(repo=repo, sha=sha[:8], message_summary=message, url=url, reason="test_run_failed")
            )
    return result
