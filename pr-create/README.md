# pr-create

This skill opens a draft pull request (PR) for the current changes.

## Use

Run `/pr-create <ticket>`. Example: `/pr-create abc-123`.

If you do not give a ticket, the skill asks for it. The skill never guesses the ticket.

## What the skill does

1. Gets the Jira ticket.
2. Finds the base branch from the remote default branch.
3. Moves the work to a branch named after the ticket, on top of the latest base branch.
4. Runs the `lint`, `typecheck`, and `test` scripts, if they exist. The skill stops if a script fails.
5. Writes the PR title and description, and copies them to the clipboard.
6. Shows a preview with the branch, the title, and the description.
7. Waits for your confirmation.
8. Commits, pushes, and opens a draft PR with the configured assignee.
9. Prints the PR URL.

## Rules

- The skill does not commit or push before you confirm.
- The skill opens only draft PRs. It never merges.
- The skill does not stage secrets or `.env` files.
- The skill uses `--force-with-lease` only to push a rebased branch that you own.

## PR format

- **Title:** `type(scope): short description`. Maximum 70 characters.
- **Description:** level-3 headings in this order:
  - `Summary` (always)
  - `Testing`, `Risk`, `Rollout`, `Screenshots` (only when they apply)
  - `JIRA` (always)

The `Screenshots` part is a Before and After table with placeholder images. Replace the placeholders after the PR opens.

## Files

- `SKILL.md`: the full instructions for the skill.
