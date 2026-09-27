# Submission deliverables — IBM Bob 2.0 Hackathon

Drafts for the two required written statements (500 words or less each,
per the submission form). Copy directly into the lablab.ai submission form.

---

## Problem & Solution Statement

**The problem.** AI coding agents make shipping cheap. They don't make it
cheap to notice when velocity has quietly outrun governance: open security
vulnerabilities nobody's tracking, code deployed with no test suite behind
it, PRs left open for weeks or merged through unresolved conflicts, secrets
or PII slipped into a public repo, a sprawl of near-duplicate projects, and
— hardest to catch with a linter — AI-authored decisions rubber-stamped
without a human actually making the call. Engineering teams building fast
with AI assistance have no single place that tells them the truth about
this across their whole GitHub org.

**The solution.** RepoWatch is a two-tier governance auditor. Tier 1 runs
six deterministic checks in parallel across every repo in an org
(Dependabot vulnerabilities, stale PRs, unresolved-conflict merges, deploys
with no Playwright/Vitest run behind them, unmasked PII candidates, repo
sprawl) and produces a real JSON/HTML report in minutes via a thin `gh` CLI
wrapper. Tier 2 hands three judgment-based questions to IBM Bob 2.0's Agent
mode — plan-before-ship detection, spaghetti/inflated-diff analysis, and
HITL-outsourcing detection — because these need actual reasoning over PR
and commit content, not a regex.

**Target users and interaction.** Engineering leads, founders, and platform
teams at AI-assisted engineering orgs — anyone who needs an honest read on
governance debt before it becomes an incident. Interaction is a single CLI
command (`repowatch <org>`) for Tier 1, producing a browsable report; Tier 2
runs as three plain-language prompts pasted into Bob IDE's Agent mode,
producing markdown findings docs committed straight into the repo.

**What makes it creative and unique.** Most audit tools either check code
style (deterministic, but blind to judgment questions) or ask an LLM to
"review this PR" (judgment-based, but unfalsifiable). RepoWatch splits the
problem honestly: deterministic checks where a regex is sufficient,
Bob-driven reasoning where it isn't — and, critically, it audits its own
output for overclaiming. When Bob's HITL check found that every
"human-reviewed decision" verdict in our own dogfooding run ultimately
rested on the AI's own written account of what a human decided, we kept
that finding as the headline rather than softening it. A governance tool
that doesn't apply its own standard to itself isn't trustworthy — this one
does.

**Effectiveness.** We dogfooded RepoWatch against our own real 14-repo
GitHub org, not a synthetic dataset. Results were immediately actionable:
13 of 14 repos had vulnerability scanning disabled entirely (a real gap no
one had surfaced), the flagship repo had 28 open Dependabot alerts and 14
recent deploys with no test suite behind them, and Bob's spaghetti audit
correctly reported "no classical spaghetti found" rather than manufacturing
findings — then caught three real, narrower issues instead: tests that
assert on source text rather than behavior, 390 undisclosed lockfile lines
from an unrelated dependency, and a major-version bump merged with no
recorded human review. Every claim in this submission traces to a committed
findings document, not an invented number.

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
