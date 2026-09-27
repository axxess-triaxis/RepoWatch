# Slide content — RepoWatch

Drop these into whatever deck tool you're using. 7 slides, built for a
≤3-minute video to walk through quickly.

---

## Slide 1 — Title

**RepoWatch**
*An AI-native engineering governance auditor*

IBM Bob 2.0 Hackathon — Triaxis Ventures

---

## Slide 2 — The problem

AI coding agents make shipping cheap.
They don't make it cheap to notice when velocity has outrun governance.

- Vulnerabilities nobody's tracking
- Code deployed with no tests behind it
- PRs stale or merged through unresolved conflicts
- Secrets/PII slipped into a public repo
- AI-authored decisions rubber-stamped with no human call

---

## Slide 3 — The approach: two tiers

**Tier 1 — deterministic** (this repo's Python, runs in minutes)
Dependabot vulnerabilities · stale PRs · unresolved-conflict merges ·
untested deploys · PII scan · repo sprawl

**Tier 2 — judgment-based** (IBM Bob 2.0, Agent mode)
Plan-before-ship detection · spaghetti/inflated-diff analysis ·
HITL-outsourcing detection

*Some questions need a regex. Some need actual reasoning over real content.*

---

## Slide 4 — Real results, not a demo dataset

Dogfooded against our own 14-repo GitHub org.

- **13 of 14 repos have zero vulnerability scanning enabled** — not clean,
  just never turned on
- **28 open Dependabot alerts** on the flagship repo, previously untracked
  in one place
- **11 PRs open >10 days**, 1 merge with an unresolved-conflict marker,
  14 recent deploys with no test suite run behind them

---

## Slide 5 — Where Bob did the real work

Bob's Agent mode chained real investigation across 3 tasks — not
single-shot answers:

- Read actual commit/diff content (`git log`, `git diff`, `git show`)
- Checked for duplicate logic (`grep`, `glob`) before calling anything
  spaghetti
- Read governance docs to learn the *stated* HITL policy before judging
  PRs against it
- **Found no classical spaghetti** — reported that honestly instead of
  manufacturing findings to look more dramatic
- Caught real, specific issues instead: tests that assert on source text
  rather than behavior, 390 undisclosed lockfile lines, a major dependency
  bump merged with no recorded review

---

## Slide 6 — The sharpest finding

Every "human-reviewed decision" verdict in our own audit rests on
**the AI's own written account** of what a human decided — not an
independently verifiable record.

A governance tool built to catch AI decisions shipped without human
oversight has to hold *itself* to that same standard.

RepoWatch does — instead of claiming more certainty than the evidence
supports.

---

## Slide 7 — Try it

```
pip install -e .
repowatch <your-github-org>
```

Live demo: **axxess-triaxis.github.io/RepoWatch**
Source: **github.com/axxess-triaxis/RepoWatch**
MIT licensed.
