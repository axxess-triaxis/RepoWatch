"""Unit tests for RepoWatch's Tier 1 checks -- all network calls mocked, so
these run offline and can't accidentally hit real repos or burn API quota.
"""

from __future__ import annotations

from unittest.mock import patch

from repowatch.checks import dependabot, pii_scan, repo_sprawl, stale_prs, untested_deploys


def test_dependabot_reports_open_alerts_only():
    fake_alerts = [
        {
            "state": "open",
            "security_advisory": {"summary": "Prototype pollution"},
            "security_vulnerability": {"severity": "high", "package": {"name": "lodash"}},
            "html_url": "https://example.com/alert/1",
        },
        {"state": "dismissed", "security_advisory": {}, "security_vulnerability": {}},
    ]
    with patch("repowatch.checks.dependabot.gh_json", return_value=fake_alerts):
        result = dependabot.check("org", "repo")
    assert len(result.findings) == 1
    assert result.findings[0].severity == "high"
    assert result.findings[0].package == "lodash"
    assert not result.access_denied


def test_dependabot_flags_access_denied_distinct_from_clean():
    with patch(
        "repowatch.checks.dependabot.gh_json",
        side_effect=dependabot.GhError("gh api ... failed: HTTP 403: Forbidden"),
    ):
        result = dependabot.check("org", "repo")
    assert result.access_denied is True
    assert result.findings == []


def test_stale_prs_threshold():
    old_pr = {"number": 1, "title": "old", "createdAt": "2020-01-01T00:00:00Z", "url": "u1"}
    new_pr = {"number": 2, "title": "new", "createdAt": "2099-01-01T00:00:00Z", "url": "u2"}
    with patch("repowatch.checks.stale_prs.gh_json", return_value=[old_pr, new_pr]):
        result = stale_prs.check_stale("org", "repo", threshold_days=10)
    assert len(result.stale_prs) == 1
    assert result.stale_prs[0].number == 1


def test_conflict_merge_detection_requires_multi_parent_and_marker():
    commits = [
        {"sha": "a" * 40, "parents": [{"sha": "p1"}, {"sha": "p2"}], "commit": {"message": "Merge\n\nConflicts:\n\tfoo.py"}, "html_url": "u"},
        {"sha": "b" * 40, "parents": [{"sha": "p1"}, {"sha": "p2"}], "commit": {"message": "Clean merge, no conflicts"}, "html_url": "u"},
        {"sha": "c" * 40, "parents": [{"sha": "p1"}], "commit": {"message": "Conflicts: mentioned but single-parent"}, "html_url": "u"},
    ]
    with patch("repowatch.checks.stale_prs.gh_json", return_value=commits):
        result = stale_prs.check_conflict_merges("org", "repo")
    assert len(result.findings) == 1
    assert result.findings[0].sha == "a" * 8


def test_untested_deploys_flags_missing_and_failed_runs():
    commits = [
        {"sha": "1" * 40, "commit": {"message": "no ci at all"}, "html_url": "u"},
        {"sha": "2" * 40, "commit": {"message": "has playwright, failed"}, "html_url": "u"},
        {"sha": "3" * 40, "commit": {"message": "has vitest, passed"}, "html_url": "u"},
    ]
    check_runs_by_sha = {
        "1" * 40: {"check_runs": []},
        "2" * 40: {"check_runs": [{"name": "Playwright E2E", "conclusion": "failure"}]},
        "3" * 40: {"check_runs": [{"name": "Vitest unit", "conclusion": "success"}]},
    }

    def fake_gh_json(args):
        if args[1] == "repos/org/repo/commits":
            return commits
        sha = args[1].split("/")[4]
        return check_runs_by_sha[sha]

    with patch("repowatch.checks.untested_deploys.gh_json", side_effect=fake_gh_json):
        result = untested_deploys.check("org", "repo")

    reasons = {f.sha: f.reason for f in result.findings}
    assert reasons["11111111"] == "no_test_run"
    assert reasons["22222222"] == "test_run_failed"
    assert "33333333" not in reasons


def test_pii_scan_masks_matches_and_flags_benign_paths():
    tree = {"tree": [{"path": "src/config.py", "type": "blob", "size": 100, "sha": "s1"}]}
    import base64

    blob = {"encoding": "base64", "content": base64.b64encode(b"contact: real.person@example.com").decode()}

    def fake_gh_json(args):
        if "git/trees" in args[1]:
            return tree
        if "git/blobs" in args[1]:
            return blob
        return {"default_branch": "main"}

    with patch("repowatch.checks.pii_scan.gh_json", side_effect=fake_gh_json):
        result = pii_scan.check("org", "repo")

    assert result.files_scanned == 1
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.kind == "email"
    assert "@" not in finding.masked_excerpt  # never leak the real match
    assert not finding.likely_benign


def test_pii_scan_skips_oversized_and_binary_files():
    tree = {
        "tree": [
            {"path": "big.txt", "type": "blob", "size": 999_999_999, "sha": "s1"},
            {"path": "image.png", "type": "blob", "size": 100, "sha": "s2"},
        ]
    }
    with patch("repowatch.checks.pii_scan.gh_json", return_value=tree) as mocked:
        # default_branch lookup call happens first; give it a harmless dict
        mocked.side_effect = [{"default_branch": "main"}, tree]
        result = pii_scan.check("org", "repo")
    assert result.files_scanned == 0


def test_repo_sprawl_flags_near_duplicate_names():
    repos = [
        {"name": "CopperNick", "isArchived": False, "isFork": False},
        {"name": "CopperNick2", "isArchived": False, "isFork": False},
        {"name": "TotallyUnrelated", "isArchived": False, "isFork": False},
    ]
    with patch("repowatch.checks.repo_sprawl.gh_json", return_value=repos):
        result = repo_sprawl.check("org", similarity_threshold=0.75)
    assert result.total_active_repos == 3
    pairs = {(d.repo_a, d.repo_b) for d in result.near_duplicates}
    assert ("CopperNick", "CopperNick2") in pairs


def test_repo_sprawl_over_threshold():
    repos = [{"name": f"repo{i}", "isArchived": False, "isFork": False} for i in range(20)]
    with patch("repowatch.checks.repo_sprawl.gh_json", return_value=repos):
        result = repo_sprawl.check("org", count_threshold=15)
    assert result.over_threshold is True
