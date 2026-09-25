# Tier 2 — Bob IDE prompts (run these yourself)

RepoWatch's Tier 1 checks (Dependabot, stale PRs, conflict merges, untested
deploys, PII, repo sprawl) are deterministic and already run via
`repowatch <org>`. The three checks below need judgment, not a regex — this
is where Bob's Agent mode, subagents, and document understanding actually
earn their place in the submission, and where the required task-session
screenshots come from.

Run each of these in Bob IDE, in **Agent mode**, against a real cloned repo
(the RepoWatch repo itself, or any repo you're auditing). After each task
completes, export the task session summary per the hackathon guide
(`Tasks` panel → select the task → export) into `bob_sessions/`.

## 1. Plan-before-ship detection

> Look at the last 15 merged PRs in this repository. For each one, determine
> whether there is evidence a plan existed *before* the implementation
> started — a linked issue with a design/plan written out, a PLAN.md-style
> file added in an early commit of the branch, or a PR description that
> references prior planning discussion. Classify each PR as
> "planned-then-shipped" or "shipped-with-no-visible-plan". Write the result
> to `docs/findings/plan_before_ship.md` as a table: PR number, title,
> classification, and the one-line evidence (or "none found") you based the
> classification on. Do not guess — if you can't find evidence either way,
> say so explicitly rather than assuming.

## 2. Spaghetti / inflated-codebase judgment

> Compare the diff size and file-touch pattern of the last 10 merged PRs
> against the actual functional change each one claims to make (read the PR
> title/description as the claim). Flag any PR where the diff looks
> disproportionate to the claim — many more files or lines touched than the
> stated change would need, duplicated logic instead of reused functions,
> or new files that substantially re-implement something already in the
> repo. For each flagged PR, name specifically what looks inflated and why
> — not just "this seems big." Write the result to
> `docs/findings/spaghetti_audit.md`.

## 3. HITL-outsourcing detection

> Read the descriptions and any linked discussion for the last 15 merged
> PRs. For each one, look for language that indicates a human actually
> reviewed and made the call on a non-trivial technical, security, product,
> or UX decision (not just "LGTM" — actual reasoning, a stated tradeoff, a
> named alternative that was rejected and why) versus a PR that reads as
> AI-authored and merged without any visible human judgment call. Classify
> each as "human-reviewed decision" or "no visible HITL". Write the result
> to `docs/findings/hitl_audit.md` with your reasoning per PR.

---

After running all three, copy the three output files' *findings*, plus a
one-paragraph summary of what you observed, into `docs/FINDINGS.md`
alongside the Tier 1 results — that combined file is what the submission's
"Problem & Solution Statement" and demo video should reference.
