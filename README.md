# RepoWatch

**IBM Bob 2.0 Hackathon entry.** An onboarding/governance copilot that audits
an org's repos for the failure modes AI-assisted teams actually hit, not the
ones a generic linter checks for.

## The problem

AI coding agents make it cheap to ship a lot, fast. They don't make it cheap
to notice when "a lot, fast" has quietly become: unreviewed security
vulnerabilities, code deployed with no test suite run against it, PRs that
sat unmerged (or got force-merged through conflicts) for weeks, secrets or
PII slipped into a public repo, a sprawl of near-duplicate projects nobody's
tracking anymore, and -- hardest to catch with a regex -- AI-authored
decisions that got rubber-stamped without a human actually making the call.

RepoWatch audits for both halves of that problem:

- **Tier 1 (this repo's Python code, deterministic):** Dependabot
  vulnerabilities, stale PRs (>10 days open), merges with unresolved-
  conflict markers, commits deployed with no Playwright/Vitest run behind
  them, unmasked PII candidates, and repo-sprawl/near-duplicate-name
  detection.
- **Tier 2 (Bob IDE, Agent mode, judgment-based):** plan-before-ship
  detection, spaghetti/inflated-diff judgment, and HITL-outsourcing
  detection -- see [`docs/BOB_PROMPTS.md`](docs/BOB_PROMPTS.md) for the
  exact prompts and [`bob_sessions/`](bob_sessions/) for the exported task
  evidence.

## Usage

```bash
pip install -e .
repowatch <github-org-or-user>
```

Produces `repowatch_report.json` and `repowatch_report.html` -- a real,
readable dashboard, not just a dump.

Scope to specific repos instead of the whole org:

```bash
repowatch axxess-triaxis --repos GALL-e-LEO CopperNick-Vision
```

## Real findings

Dogfooded against the `axxess-triaxis` GitHub org (13 real repos, not a
sample dataset) -- see [`docs/FINDINGS.md`](docs/FINDINGS.md) for the actual
report, including what it got right and what it flagged as a false positive.

## Known limitations (honest, not hidden)

- Dependabot alerts require the `security_events` OAuth scope; without it,
  RepoWatch reports "access denied" explicitly rather than silently showing
  a clean result -- a real absence of vulnerabilities and a lack of
  permission to check are never conflated.
- The conflict-merge check is a lower bound: it only catches merges whose
  commit message still carries git's default "Conflicts:" marker. A squash
  merge or an edited commit message won't be caught.
- PII matches are regex candidates for human review, not verdicts -- credit-
  card-shaped numbers and 10-digit phone-shaped numbers produce false
  positives on plenty of legitimate strings (order IDs, hashes, test
  fixtures). The tool masks every match and flags obviously-benign paths
  (tests, fixtures, docs) rather than pretending precision it doesn't have.
- Tier 2 checks require a human (or Bob) to actually read PR content and
  reason about it -- they are not automatable with a regex, which is the
  entire point of building them as Bob-driven checks instead of Tier 1 ones.

## Architecture

```
src/repowatch/
  cli.py              entry point
  github_client.py     thin `gh` CLI wrapper (reuses your existing gh auth)
  report.py             aggregates all checks -> JSON + HTML
  checks/
    dependabot.py        open vulnerability alerts
    stale_prs.py           stale PRs + conflict-merge heuristic
    untested_deploys.py     commits with no Playwright/Vitest CI run
    pii_scan.py               regex PII scan, masked output only
    repo_sprawl.py             near-duplicate names + repo count
```

Built for the [IBM Bob 2.0 Hackathon](https://lablab.ai/ai-hackathons/ibm-bob-2-hackathon)
by Triaxis Ventures.
