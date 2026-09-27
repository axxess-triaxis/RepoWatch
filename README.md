# RepoWatch

![RepoWatch: repo governance, audit, vigilance](assets/repowatch-banner.png)

RepoWatch audits a GitHub org for the failure modes AI-assisted teams actually hit, not the ones a generic linter checks for. AI coding agents make it cheap to ship a lot, fast. They don't make it cheap to notice when that has quietly turned into:

- unreviewed security vulnerabilities
- code deployed with no test run behind it
- PRs that sat for weeks, or were merged through conflicts
- PII slipped into a repository
- a sprawl of near-duplicate projects nobody tracks any more

RepoWatch checks every active, non-fork repo in an org, or only the repos you name, and produces a JSON report and a readable HTML dashboard. As a Claude plugin, Claude runs the audit and summarizes the real findings in the conversation.

## What it checks

| Check | What it reports |
|---|---|
| Dependabot | Open vulnerability alerts with severity. It keeps "no permission to read alerts" and "Dependabot turned off" separate from a real clean result of 0 alerts. |
| Stale PRs | PRs open more than 10 days. |
| Conflict merges | Merge commits that still carry git's default `Conflicts:` marker. |
| Untested deploys | Recent commits (the last 20) with no check run named like a Playwright or Vitest job, or where every such run failed. |
| PII | Regex candidates for emails, phone numbers, US SSNs, card-shaped numbers and Aadhaar-shaped numbers, in up to 80 text files per repo. Every match is masked in the output. |
| Repo sprawl | Near-duplicate repo names, and orgs with more than 15 active repos. |

## Requirements

- The [GitHub CLI](https://cli.github.com/) (`gh`), logged in with `gh auth login`. To read Dependabot alerts, the login also needs the `security_events` scope: `gh auth refresh -s security_events`.
- Python 3.11 or newer. RepoWatch uses the standard library only, so there is nothing to `pip install`.

## Install as a Claude Code plugin

Add this repository as a plugin marketplace, then install the plugin:

```bash
claude plugin marketplace add axxess-triaxis/RepoWatch
claude plugin install repowatch@repowatch
```

Then, in a Claude Code session:

```
/repowatch:repowatch your-org
/repowatch:repowatch your-org --repos repo-one repo-two
```

You can also ask in plain words, such as "audit the governance of my GitHub org". Claude runs the audit and walks you through what it found. Reports are written to the plugin's own data directory, not to your working tree.

The plugin needs a local shell, `gh` and Python, so it works in Claude Code. It doesn't do anything useful in claude.ai chat, which has no local shell.

## Use as a command-line tool

```bash
pip install -e .
repowatch your-org
repowatch your-org --repos repo-one repo-two --out reports/audit
```

This writes `repowatch_report.json` and `repowatch_report.html` (or `<out>.json` and `<out>.html`).

## Data and network disclosure

- **What it calls:** only the GitHub REST API (`api.github.com`), through your own `gh` CLI login. It uses the token `gh` already holds on your machine and never reads, prints or stores that token itself.
- **What it reads:** repository metadata, the org's repo list, open PRs, recent commits and their check runs, Dependabot alerts, and the file tree and contents of up to 80 text files per repo for the PII scan. Everything is read-only; RepoWatch never writes to GitHub.
- **What it writes:** two local report files, JSON and HTML. PII matches appear only as masked excerpts, such as `22********08`.
- **What it doesn't do:** it sends no telemetry and no analytics, and nothing is sent to any server other than GitHub's API. It keeps no data beyond the report files you choose to keep.

## Known limitations

- **Dependabot needs the `security_events` scope.** Without it, RepoWatch reports `access_denied`, so a lack of permission is never shown as a clean result.
- **The conflict-merge check is a lower bound.** Squash merges, or edited merge messages, aren't caught.
- **PII matches are candidates for human review, not verdicts.** Card-shaped and phone-shaped numbers match plenty of legitimate strings, such as IDs, hashes and fixtures. Matches in paths containing `test`, `spec`, `fixture`, `example` or `sample`, or in `.md` files, are flagged as `likely_benign`.
- **Only Playwright and Vitest runs count as tests.** A commit counts as tested only if one of its check runs has `playwright` or `vitest` in its name. Repos that test with pytest, Jest, Go test or anything else show every commit as untested, so treat this check as meaningful only for repos that use those two tools.
- **Scans are sampled.** Untested-deploy detection looks at the last 20 commits, and the PII scan reads up to 80 files per repo.

## Architecture

```
.claude-plugin/          plugin and marketplace manifests
skills/repowatch/        the Claude skill: run the audit, summarize findings
scripts/repowatch.py     stdlib launcher used by the skill (no install step)
src/repowatch/
  cli.py                 command-line entry point
  github_client.py       thin `gh` CLI wrapper (reuses your gh login)
  report.py              runs every check -> JSON + HTML
  checks/                dependabot, stale_prs, untested_deploys, pii_scan, repo_sprawl
tests/                   unit tests for the checks
```

RepoWatch started as an entry to the IBM Bob 2.0 Hackathon. That submission is preserved unchanged at the [`hackathon-submission`](https://github.com/axxess-triaxis/RepoWatch/tree/hackathon-submission) tag.

## License

MIT, see [LICENSE](LICENSE). Built by Triaxis Ventures.
