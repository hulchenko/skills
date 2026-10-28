# Known issues

Format: problem, cause, fix. Read this file at the start of each run.
When a run fails and I fix it: propose a new entry, wait for my OK, then append it.

1. **`gh` fails with "token invalid".** The shell `GITHUB_TOKEN` is invalid. Fix: run `env -u GITHUB_TOKEN gh ...`. The scripts do this already.
2. **Jira key search finds nothing.** `/product:jira-search` searches words only, hides Done tickets, and covers 365 days. Fix: `triage.sh --jira KEY` queries by exact key. Use the host from the Jira link in the PR body. Host map: `config.md`.
3. **Jira returns 0 issues for a real key.** The key is on another host (another Jira site) or my credentials have no access. Fix: show "Jira not reachable", not "code does not match".
4. **HTTP 403 SAML on an org.** Treat it as a per-repo or per-team failure. List it at the end. Stop the run only for a login failure.
5. **Check runs and status contexts differ.** Check runs have `conclusion`. Status contexts have `state`. The script reads both.
6. **Team slugs include the org.** `reviewRequests` returns `your-org/priority-team`, not `priority-team`. The script splits it.
7. **CODEOWNERS teams I am not in cannot be read** (HTTP 404). Then "a code owner approved" cannot be confirmed. The PR is not skipped for this reason.
8. **A domain reviewer agent can post to GitHub by itself.** Tell it to return findings only.
9. **Search limit.** `gh search code` allows 10 searches per minute. `blast.sh` waits 7 seconds and caches by symbol.
10. **Large diffs.** `gh pr diff` fails over about 20000 lines. The PR is then hard ("diff unavailable").
11. **Noisy hard signals (tuning).** The words `href` and `target` match many ordinary link edits. Tune `attr_words` in `config.md` after week 1 if too many PRs are hard.
