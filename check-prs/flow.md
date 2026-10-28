# Flow

## Tabs

Order: Easy, Medium, Hard. Sort inside a tab by `priority` (1 direct, 2 priority team, 3 other), then oldest first.
Use `AskUserQuestion` multi-select. Up to 4 PRs per question and 4 questions per call. Page through more rounds if needed.
Option label: one-line ASD-STE100 summary, repo, PR number. Option description: full PR URL, type reason, state.
When a tab ends, run `scripts/cache.py set "<cache_key>" closed_date=<today> my_action=<action>` for each PR I handled. Run it with `dismissed=true` for PRs I dismissed.

**Easy**: I pick PRs to approve. PRs with `approve_blocked` show but cannot be picked.
**Medium**: A) passed all checks: I pick PRs to approve. B) "Needs manual review": show the failed checks. I pick PRs to review.
**Hard**: I pick PRs to review. Print each picked URL. Open it with `open <url>` only when `approvals_enabled` is true.

## Review (Medium-B and Hard picks)

- Stale branch: when `branch_behind` is true, show "branch N commits behind main" on the PR row. Never make it a finding or a comment. Version numbers in a stale branch (for example package versions) can differ from main. Check them against main before you use them in a finding.
- Pass the FE rules file path to `frontend-reviewer`: the path of your reviewer rules file (set it in config.md). Tell it to read the rules, not guess them.
- Before posting an inline comment, open the file at the head SHA and check that the line holds the code you quote. Reviewer line numbers can be off.
- First read the full PR description and the linked Jira ticket. Give both to every reviewer. A reviewer must not report a change as "unrelated" or "unexplained" if the description explains it. For each finding, say what the description says about it: explained and OK, explained but risky, or not explained. Quote the description line.
- Apps (`kind: app`): run your domain reviewer agent for app repos. Tell it to return findings only. It must never post to GitHub. If the FE rules file is missing on this machine, say so in the report. Do not present rule IDs as exact.
- Libraries (`kind: library`): run a generic Sonnet reviewer that reads the PR with `gh`. Write "FE-001…FE-013 not applied" in the report.
- Big PRs: split by file. Run up to 4 agents in parallel. Each has a 10-minute limit. On failure, write "not reviewed". List every file not read.
- Final Sonnet pass: keep only critical and major findings. Each finding has: quoted code, link `https://github.com/<org>/<repo>/blob/<head_sha>/<path>#L<line>`, severity and reason, failure scenario (state, then wrong result), rule reference, "what the diff cannot show".
- Mark these as `checked` or `not checked`: correctness and edge cases; tests and risk coverage; security, accessibility, i18n.
- Show one PR at a time. No critical or major issue: say "No blocking issues" and offer Approve.
- For each finding, show the exact comment the skill would post, as a draft: file, line, and full body text. Do this before I decide. Write every comment body in ASD-STE100 Simplified Technical English: short active sentences, one idea per sentence, approved words, no idioms. A comment states the problem, the failure scenario, and one question or fix.
- Code-owner warning: when `i_am_code_owner` is false, say "your approval does not satisfy code owners". If I was asked directly and own no changed path, offer Comment only.
- I choose for each PR: Comment (post the drafts as shown), Edit (I change a draft or drop a finding, then show the new draft again), Approve, or Skip.
- Post a comment only as the text I saw last. Never change the text after I choose.
- CI red or pending, but the review finds no critical or major issue: Approve is blocked. Offer Comment with the body `Codewise LGTM. Please fix CI check and poke me for a re-review. Thanks!` Say in the row that the CI failure is often an out-of-date branch. Do not draft a CI question.

## Posting

Use only `scripts/post.py <repo> <number> <head_sha> <approve|comment> --body-file F [--comments-file F] --user-confirmed`.
- `<head_sha>` is the SHA saved at triage. The script reads the head again and stops if it changed. Then review again.
- It never posts twice on the same PR, SHA, and action. A new SHA can be reviewed again.
- It records every post in `cache.json` (PR, SHA, action, time).
- Approve body for easy and medium-A: `LGTM — auto-triaged as low-risk`. If the PR has no Jira key (`jira` is empty), the body is `LGTM! Please link the Jira ticket in the description.`
- The same Jira line applies to a PR I approve after a review. Add it to the approval body when `jira` is empty.
- Week 1 (`approvals_enabled: false`): one PR at a time, only what I choose. No `--batch`.
- `approvals_enabled: true`: one batch confirmation for Easy and Medium-A approvals (`--batch`).
- A comments file is a JSON list of `{"path", "line", "body"}`.

## Report

Write the prioritized list to `reports/YYYY-MM-DD.md` (local only). Add `failures` from triage at the end. The script deletes reports and cache entries older than 30 days.
