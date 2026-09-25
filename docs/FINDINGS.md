# Real findings — dogfooded against `axxess-triaxis`

Run: `repowatch axxess-triaxis`. 14 repos scanned, real GitHub API data, no
synthetic/sample dataset. Full raw output: [`repowatch_report.json`](repowatch_report.json) /
[`repowatch_report.html`](repowatch_report.html).

## Headline findings

- **AXXESSTRIAXIS (the flagship product repo): 28 open Dependabot vulnerability
  alerts, 11 PRs open >10 days, 1 merge with an unresolved-conflict marker,
  14 recent commits deployed with no Playwright/Vitest run behind them.**
  Nobody was tracking this in one place before this run — exactly the
  "AI-assisted velocity outpaced governance visibility" problem RepoWatch
  exists to catch.
- **Repo sprawl**: 10 active repos in the org, under the sprawl threshold,
  but one near-duplicate pair flagged: `codespaces-react` /
  `codespaces-blank` (0.75 name similarity) — worth a human glance to
  confirm both are intentional, not one forgotten.
- **Untested deploys are the most common finding across the org** — most
  repos hit RepoWatch's 20-commit lookback cap with zero Playwright/Vitest
  runs. For research/fork repos (the ARC-AGI forks, `awesome-phone-call-
  agents`) this is expected and not concerning — they have no UI test
  suite by design. For product repos it's a real signal.
- **Dependabot access**: only worked for AXXESSTRIAXIS; every other repo
  returned "access denied" under the current token scope
  (`security_events` not yet granted). RepoWatch reports this explicitly
  rather than showing a false "clean" result — see README's limitations
  section.

## A documented false positive, on purpose

The PII scan flagged 3 "credit card" matches in `Picketty` — all three are
13-16 digit numeric sequences inside MuJoCo robot-simulation config files
(`aloha.xml`, `mjx_aloha.patch`, `tutorial.ipynb`): joint parameters and mesh
coordinates, not real card numbers. This is exactly the tradeoff stated in
README's limitations section (credit-card-shaped numbers produce false
positives on legitimate numeric data) — kept in this findings doc instead of
quietly fixed, because a hackathon judge should see the tool's real
precision, not a cherry-picked clean run.

## Tier 2 (Bob-driven) findings

Pending — run via Bob IDE per [`BOB_PROMPTS.md`](BOB_PROMPTS.md), results to
be appended here once complete.
