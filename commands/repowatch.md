---
description: Audit a GitHub org or specific repos for governance issues (vulnerabilities, stale PRs, untested deploys, PII, repo sprawl)
argumentHint: [org] [--repos NAME...]
---

The user wants to run a RepoWatch governance audit against a GitHub org or
a specific list of repos within one.

Run this with the Bash tool, using whatever org/repo arguments the user
gave after `/repowatch` (default to no `--repos` filter, which scans every
active, non-fork repo in the org):

```
repowatch <org> [--repos NAME NAME ...]
```

This takes real time (each repo runs 6 real GitHub API-backed checks) —
tell the user it's running before the command returns, don't let it look
stalled.

Once it finishes, it writes `repowatch_report.json` and
`repowatch_report.html` in the current directory. Read the JSON report and
summarize the real findings directly in the conversation — don't just say
"done, see the file." For each repo, call out anything flagged:

- Dependabot: open alert count, or explicitly note `access_denied` (token
  lacks the `security_events` scope) vs `dependabot_disabled` (never turned
  on for that repo) vs a real clean 0-alert result — these are three
  different things and the report distinguishes them on purpose; don't
  collapse them into one "clean" bucket.
- Stale PRs (>10 days open), and unresolved-conflict merges
- Untested deploys: commits with no Playwright/Vitest run behind them
- PII: mention `likely_benign` matches only in passing; call out non-benign
  ones plainly, but note they're regex candidates for human review, not
  confirmed leaks
- Repo sprawl: near-duplicate names, or the org exceeding the count
  threshold

If nothing across the org is concerning, say that plainly too — don't
manufacture findings to seem more useful than the real result.
