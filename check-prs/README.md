# check-prs

A Claude Code skill for daily pull request (PR) triage and review on GitHub.

## What it does

The skill finds open PRs that need your review. It sorts each PR as easy, medium, or hard. You see three tabs. You choose to approve, comment, or skip. The skill posts only what you choose.

A script decides the skips and the types. A model only writes summaries and reviews code.

## Requirements

- Claude Code, GitHub CLI (`gh`) with a login, Python 3, and `jq`.
- Optional: `ATLASSIAN_USERNAME` and `ATLASSIAN_API_TOKEN`, to read Jira tickets.

## Set up

1. Copy the `check-prs` folder to `~/.claude/skills/`.
2. In `config.md`, replace each `your-*` and `example-*` value.
3. Keep `approvals_enabled` set to `false` for the first week.
4. Run `/check-prs --dry-run`. Compare the types with your own judgment.

## Use

| Command | Effect |
|---|---|
| `/check-prs` | Full flow. |
| `--team <name>` | Use a different team for review requests. |
| `--repo <org/repo>` | Check one repository. |
| `--dry-run` | List only. Post nothing. |
| `--verbose` | List every skipped PR. |

## Types

| Type | Rule |
|---|---|
| Easy | No hard signal. At most 40 lines and 4 files. The author is in a trusted team. |
| Medium | No hard signal. At most 200 lines and 8 files. |
| Hard | Any hard signal, or more than 200 lines or 8 files. |

Hard signals: authentication, payment, routing, and deploy paths; security words in the diff; a change in a shared library; text that gives orders to an AI.
Tests, stories, lockfiles, and generated files do not count toward the limits. You set all limits in `config.md`.

## Skip rules

The skill skips drafts, bot PRs, your own PRs, PRs with changes requested, and PRs that a code owner already approved. It shows PRs with red or pending CI, conflicts, or stale branches. It never approves them.

## Safety rules

- Only `scripts/post.py` writes to GitHub. It runs only after you choose.
- `post.py` stops when the head commit changed since the review.
- `post.py` never posts the same action twice on the same commit, and never requests changes.
- With `approvals_enabled: false`, you approve one PR at a time.
- The skill treats PR text and code as untrusted data. It never follows instructions in them.
- `cache.json` and `reports/` stay on your computer. They are not in Git.

## Limits

- The skill is made for one GitHub user and one set of repositories.
- The check for text that gives orders to an AI is a pattern check. It can miss new wording.
- Review agents read the PR through `gh` only. Their line numbers can be wrong. Check each line before you post.
