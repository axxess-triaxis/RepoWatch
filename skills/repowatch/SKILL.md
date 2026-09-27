---
name: repowatch
description: Audit a GitHub org, or specific repos in it, for governance issues that AI-assisted teams hit - open Dependabot alerts, stale PRs, unresolved-conflict merges, deploys with no test run, exposed PII, and repo sprawl.
when_to_use: Use when the user asks to audit, health-check, or review the governance or security posture of a GitHub org or its repositories.
argument-hint: <org> [--repos NAME ...]
---

Run a RepoWatch audit for: `$ARGUMENTS`

The first word is the GitHub org or user. Anything after `--repos` limits the audit to those repo names. With no `--repos`, RepoWatch scans every active, non-fork repo in the org. If no org was given, ask the user for one before running anything.

## Before running

RepoWatch calls the GitHub API through the user's own `gh` CLI login, and runs on Python 3.11 or newer. If `gh auth status` fails, tell the user to run `gh auth login` themselves, and stop.

## Run it

Tell the user the audit is running. Each repo runs 6 GitHub API-backed checks, so a large org takes a few minutes.

Write the reports to the plugin's data directory, never into the user's working tree:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/repowatch.py" <org> [--repos NAME ...] --out "${CLAUDE_PLUGIN_DATA}/repowatch_report"
```

On Windows, if `python3` isn't found, use `python` instead.

It writes `repowatch_report.json` and `repowatch_report.html` there. Tell the user where the HTML report is.

## Summarize the real findings

Read the JSON report and summarize the findings in the conversation. Don't just say "done, see the file." For each repo, call out anything flagged:

- **Dependabot:** give the open alert count and severities. Keep three results separate, because the report distinguishes them on purpose:
  - `access_denied`: the token can't read alerts. The user needs the `security_events` scope, via `gh auth refresh -s security_events`.
  - `dependabot_disabled`: alerts were never turned on for that repo.
  - A real, clean result of 0 alerts.
- **Stale PRs** open more than 10 days, and merges with unresolved-conflict markers.
- **Untested deploys:** commits with no test run behind them, or with a failed one. RepoWatch looks at the last 20 commits only.
- **PII:** mention `likely_benign` matches only in passing. Call out other matches plainly, but say they are regex candidates for human review, not confirmed leaks. Only ever repeat the masked excerpt, never an unmasked value.
- **Repo sprawl:** near-duplicate repo names, or the org going over the repo-count threshold.

If nothing across the org is concerning, say so plainly. Don't manufacture findings.
