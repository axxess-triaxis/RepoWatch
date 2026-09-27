# Submission deliverables — IBM Bob 2.0 Hackathon

Drafts for the two required written statements (500 words or less each,
per the submission form). Copy directly into the lablab.ai submission form.

---

## Problem & Solution Statement

AI coding agents make shipping cheap. They don't make it cheap to notice
when velocity has quietly outrun governance: open security vulnerabilities
nobody's tracking, code deployed with no test suite behind it, PRs left
open for weeks or merged through unresolved conflicts, secrets or PII
slipped into a public repo, a sprawl of near-duplicate projects, and —
hardest to catch with a linter — AI-authored decisions rubber-stamped
without a human actually making the call.

RepoWatch audits for both halves of that problem across an entire GitHub
org, not one repo at a time. Six deterministic checks (Dependabot
vulnerabilities, stale PRs, unresolved-conflict merges, deploys with no
Playwright/Vitest run behind them, unmasked PII candidates, repo sprawl)
run in parallel via a thin `gh` CLI wrapper and produce a real JSON/HTML
report in minutes. Three judgment-based checks — plan-before-ship
detection, spaghetti/inflated-diff analysis, and HITL-outsourcing detection
— run through IBM Bob 2.0's Agent mode, because they need actual reasoning
over PR content, not a regex.

We dogfooded RepoWatch against our own real 14-repo GitHub org, not a
sample dataset. The results were genuinely useful, not staged: our flagship
product repo has 28 open Dependabot alerts and 13 of our 14 repos have
vulnerability scanning disabled entirely — a real coverage gap nobody had
surfaced before this ran. Bob's plan-before-ship audit found 80% of our
recent human-authored PRs had real pre-implementation planning evidence,
and specifically caught the one that didn't — a reactive hotfix shipped
with no issue or design doc. Bob's spaghetti audit found no duplicated
logic in our recent PRs, but did catch a bugfix PR whose 510-line diff hid
390 undisclosed lockfile lines and 48 lines of tests that assert on source
text rather than behavior. Bob's HITL audit confirmed 5 of 5 human-authored
PRs had real human judgment calls behind them — and caught one Dependabot
major-version bump that slipped through without review.

The most important finding came from asking Bob to audit its own audit: it
discovered that every "human-reviewed decision" verdict in our repo
ultimately rests on the AI's own written account of what a human decided
(commit bodies attributing calls to the founder), not an independently
verifiable record. A tool built to catch AI decisions shipped without human
oversight has to hold that same standard against itself — and RepoWatch
does, rather than claiming more certainty than the evidence supports.

This is a governance tool that tells you the truth about your own repos,
including the parts that are uncomfortable, using Bob for exactly the work
a regex can't do: reading real content and reasoning about what it means.

---

## IBM Bob 2.0 Usage Statement

Bob IDE (Agent mode) ran three of RepoWatch's nine checks — the ones that
need judgment over PR/commit content, not pattern-matching:

1. **Plan-before-ship detection**: read the last 15 merged PRs on our
   production repo, cross-referenced commit bodies against a pre-existing
   incident ledger, and classified each as planned or unplanned with cited
   evidence — correctly excluding 10 Dependabot auto-bumps from the human
   planning-rate denominator rather than diluting the result.
2. **Spaghetti/inflated-diff judgment**: compared diff size against each
   PR's stated claim across 10 recent PRs, inspected actual function
   content and lockfile deltas (not just line counts), and correctly
   reported "no classical spaghetti found" rather than manufacturing
   findings — then flagged 3 real, narrower issues: source-text tests
   masquerading as unit tests, an out-of-scope doc correction bundled into
   a bugfix, and undisclosed lockfile churn from an unrelated transitive
   dependency shift.
3. **HITL-outsourcing detection**: read PR descriptions and linked ledger
   entries for the same 15 PRs, distinguished real named tradeoffs and
   rejected alternatives from rubber-stamp language, and identified the one
   real gap — a major-version dependency bump merged with no recorded human
   review of its breaking API surface.

Across all three tasks, Bob used Agent mode to chain multiple real
investigation steps autonomously — reading source files, grepping for
duplicate function definitions, inspecting lockfile hunks line by line,
cross-referencing governance docs (`AI_GOVERNANCE.md`,
`ENGINEERING_WORKFLOW.md`, `CLAUDE.md`) for stated HITL policy before
judging whether PRs met it — rather than answering from the PR titles
alone. Task session summaries for all three runs are in `bob_sessions/`.

The value Bob added was specifically qualitative reasoning our deterministic
Tier 1 checks structurally cannot do: judging whether a diff's *shape*
matches its *claim*, whether cited evidence for a decision is real or
performative, and — in its strongest moment — recognizing the limits of its
own evidence rather than overclaiming certainty.
