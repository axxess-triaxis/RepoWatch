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
- **Dependabot coverage: only 1 of 14 repos has it enabled at all.** After
  granting the token the `security_events` scope, the real picture is
  clearer and more concerning than an access problem: AXXESSTRIAXIS has
  Dependabot alerts turned on (and 28 open); every other repo returns
  "Dependabot alerts are disabled for this repository" — a per-repo GitHub
  setting nobody ever flipped on. That's not "13 clean repos," it's
  **13 repos with zero automated vulnerability visibility**, indistinguishable
  from a real 403 until RepoWatch's check specifically separates the two
  (see the dependabot.py fix in this repo's own commit history — the same
  HTTP 403 covers both cases, and conflating them would have hidden this
  finding entirely).

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

### Plan-before-ship audit (1 of 3 complete)

Run via IBM Bob 2.0, Agent mode, against `axxess-triaxis/AXXESSTRIAXIS`'s
last 15 merged PRs. Full table: [`findings/plan_before_ship.md`](findings/plan_before_ship.md).

**4 of 5 human-authored PRs (80%) show real pre-implementation planning
evidence** (cross-references to a pre-existing ledger item, a decision
sequence spanning prior PRs) — the other 10 of 15 are Dependabot auto-bumps
with no planning expected. The one gap: **#363**, a reactive hotfix for a
macOS CI failure (darwin/sharp architecture support) shipped with no issue,
design doc, or pre-branch decision record — a real, specific instance of
exactly the failure mode this hackathon's challenge brief describes, caught
by Bob reading actual PR/commit content, not a keyword match.

### Spaghetti / inflated-diff audit (2 of 3 complete)

Run via IBM Bob 2.0, Agent mode, against the same 10 most recent merged PRs.
Full detail: [`findings/spaghetti_audit.md`](findings/spaghetti_audit.md).

**No classical spaghetti found** — worth stating plainly, since a tool that
always finds something to flag isn't trustworthy. 3 of 10 PRs flagged, all
in narrower, real categories: PR #362 bundles 4 distinct inflations (34
lines of incident-report prose inside a 72-line function, 48 lines of tests
that assert on source text rather than behavior, an unrelated doc
correction folded into a bugfix PR, and ~390 undisclosed lockfile lines from
a new native dependency); #363 has an 11-line comment block around a
1-line config fix; #353 ("bump input-otp") actually changed 75 lockfile
lines, 73 of them from an unrelated transitive `terser` resolution shift the
PR title never mentions.

HITL-outsourcing detection: pending, prompt 3 in [`BOB_PROMPTS.md`](BOB_PROMPTS.md).
