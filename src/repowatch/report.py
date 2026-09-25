"""Aggregates all Tier-1 checks across an org's repos into one report."""

from __future__ import annotations

import dataclasses
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from .checks import dependabot, pii_scan, repo_sprawl, stale_prs, untested_deploys
from .github_client import list_org_repos


def _to_dict(obj):
    if dataclasses.is_dataclass(obj):
        return {k: _to_dict(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, list):
        return [_to_dict(v) for v in obj]
    return obj


def _audit_one_repo(org: str, repo: str) -> dict:
    return {
        "repo": repo,
        "dependabot": _to_dict(dependabot.check(org, repo)),
        "stale_prs": _to_dict(stale_prs.check_stale(org, repo)),
        "conflict_merges": _to_dict(stale_prs.check_conflict_merges(org, repo)),
        "untested_deploys": _to_dict(untested_deploys.check(org, repo)),
        "pii": _to_dict(pii_scan.check(org, repo)),
    }


def run_audit(org: str, repos: list[str] | None = None, concurrency: int = 6) -> dict:
    target_repos = repos or list_org_repos(org)

    # Each repo's checks are independent, I/O-bound `gh` subprocess calls --
    # sequential scanning of a 10+ repo org would take the better part of an
    # hour. Parallelize across repos the same way as this account's other
    # multi-target scan (AgentObserver's seed_sweep.py).
    results_by_repo: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(_audit_one_repo, org, repo): repo for repo in target_repos}
        for future in as_completed(futures):
            repo = futures[future]
            results_by_repo[repo] = future.result()
    per_repo = [results_by_repo[repo] for repo in target_repos]

    sprawl = _to_dict(repo_sprawl.check(org))

    return {
        "org": org,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repos_scanned": len(target_repos),
        "sprawl": sprawl,
        "repos": per_repo,
    }


def write_json(report: dict, out_path: Path) -> None:
    out_path.write_text(json.dumps(report, indent=2))


def write_html(report: dict, out_path: Path) -> None:
    rows = []
    for r in report["repos"]:
        findings = []
        dep = r["dependabot"]
        if dep.get("access_denied"):
            findings.append('<li class="warn">Dependabot: no read access (token scope)</li>')
        elif dep.get("findings"):
            findings.append(f'<li class="bad">Dependabot: {len(dep["findings"])} open alert(s)</li>')

        stale = r["stale_prs"].get("stale_prs", [])
        if stale:
            findings.append(f'<li class="bad">{len(stale)} PR(s) open &gt;10 days</li>')

        conflicts = r["conflict_merges"].get("findings", [])
        if conflicts:
            findings.append(f'<li class="bad">{len(conflicts)} merge(s) with unresolved-conflict markers</li>')

        untested = r["untested_deploys"].get("findings", [])
        no_test = [f for f in untested if f["reason"] == "no_test_run"]
        failed_test = [f for f in untested if f["reason"] == "test_run_failed"]
        if no_test:
            findings.append(f'<li class="bad">{len(no_test)} recent commit(s) with no Playwright/Vitest run</li>')
        if failed_test:
            findings.append(f'<li class="warn">{len(failed_test)} commit(s) with a failing Playwright/Vitest run</li>')

        pii = r["pii"]
        non_benign_pii = [f for f in pii.get("findings", []) if not f["likely_benign"]]
        if non_benign_pii:
            findings.append(f'<li class="bad">{len(non_benign_pii)} possible unmasked PII match(es)</li>')

        status = "clean" if not findings else "flagged"
        rows.append(
            f'<tr class="{status}"><td>{r["repo"]}</td><td><ul>{"".join(findings) or "<li>clean</li>"}</ul></td></tr>'
        )

    dupes = report["sprawl"].get("near_duplicates", [])
    sprawl_html = ""
    if report["sprawl"].get("over_threshold") or dupes:
        sprawl_html = f'<p class="bad">Repo sprawl: {report["sprawl"]["total_active_repos"]} active repos'
        if dupes:
            dupe_list = ", ".join(f'{d["repo_a"]} ~ {d["repo_b"]} ({d["similarity"]})' for d in dupes)
            sprawl_html += f"; near-duplicate names: {dupe_list}"
        sprawl_html += "</p>"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>RepoWatch -- {report['org']}</title>
<style>
body {{ font-family: -apple-system, Segoe UI, sans-serif; margin: 2rem; background: #0f1117; color: #e6e6e6; }}
h1 {{ font-weight: 600; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
td {{ padding: 0.75rem; border-bottom: 1px solid #2a2d3a; vertical-align: top; }}
tr.clean td:first-child {{ color: #6ee7b7; }}
tr.flagged td:first-child {{ color: #fca5a5; font-weight: 600; }}
.bad {{ color: #fca5a5; }}
.warn {{ color: #fcd34d; }}
ul {{ margin: 0; padding-left: 1.2rem; }}
.meta {{ color: #9ca3af; font-size: 0.9rem; }}
</style></head>
<body>
<h1>RepoWatch report -- {report['org']}</h1>
<p class="meta">Generated {report['generated_at']} &middot; {report['repos_scanned']} repos scanned</p>
{sprawl_html}
<table>
<tr><th align="left">Repo</th><th align="left">Findings</th></tr>
{''.join(rows)}
</table>
</body></html>"""
    out_path.write_text(html)
