# Bob IDE task session summaries

Per the IBM Bob 2.0 Hackathon submission requirements, exported Bob IDE task
session evidence goes in this folder.

## [`bob-tasks-AXXESS-TRIAXIS-2026-09-27.md`](bob-tasks-AXXESS-TRIAXIS-2026-09-27.md)

The full session transcript for all three Tier 2 checks, run in Bob IDE's
Agent mode against `axxess-triaxis/AXXESSTRIAXIS`: plan-before-ship
detection, spaghetti/inflated-diff judgment, and HITL-outsourcing
detection. Shows every real tool call Bob made to produce the findings in
`docs/findings/` — `git log`/`git diff`/`git show` to read actual commit
and diff content, `grep`/`glob` to check for duplicate function
definitions and existing test patterns, `read_file` against governance
docs (`AI_GOVERNANCE.md`, `CLAUDE.md`, the founder bug closure ledger) to
establish what the repo's stated HITL policy actually is before judging
whether PRs met it, `update_todo_list` to track multi-step progress, and
`write_file` to produce each findings doc — not a single-shot answer from
the PR titles alone.

See [`docs/BOB_PROMPTS.md`](../docs/BOB_PROMPTS.md) for the exact prompts
that produced these sessions, and [`docs/FINDINGS.md`](../docs/FINDINGS.md)
for the resulting findings.
