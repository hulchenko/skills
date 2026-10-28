---
name: pr-create
description: Use when the user asks to open a pull request, or asks for a PR description or PR title for the current changes. Creates the branch, commits, and opens a draft PR. Takes the JIRA ticket from the args. Asks the user when the args have no ticket.
---

Write the PR description for the current changes. Then create the branch, commit, and open a draft PR.

## Language rule

Write all output in ASD-STE100 Simplified Technical English. This rule has no exception.

- Use short, active sentences. Use one idea in each sentence.
- Use 20 words or fewer in each descriptive sentence. Use 25 words or fewer in each instruction.
- Use articles (a, an, the). Do not use arrows, idioms, or fragments.
- Use one word for one thing. Keep technical names and code exactly as they are, in code format.

## Rules for git and GitHub

- The user gave permission for this skill to create a branch, commit, push, and open a draft PR. This permission applies only to this skill.
- Open only a draft PR. Never mark it ready for review. Never merge.
- Use `--force-with-lease` only to push a rebased branch that you own. Never use `--force`.
- Stop and tell the user when a step fails. Do not continue after a failed step.
- Do not stage secrets or env files (`.env*`, keys, tokens). Tell the user if you skip a file.

## Steps

1. Get the JIRA ticket before you do anything else. If $ARGUMENTS has a ticket (example: `abc-123`), use that ticket. If $ARGUMENTS has no ticket, ask the user for it and wait for the answer. Never assume the ticket. Never take it from the conversation, the branch name, the commits, or an earlier run. A ticket from earlier work can belong to a different task. Do not run any git command until you have the ticket.
2. Find the base branch. Run `git symbolic-ref refs/remotes/origin/HEAD`. If the command fails, use `main`.
3. Find the current branch and the state of the work. Run `git branch --show-current` and `git status --short`.
4. Put the work on the task branch, on top of the latest base branch. The task branch is always `<username>/<ticket in lowercase>`. The username is the GitHub login. Get it with `gh api user --jq .login`. Example: `jdoe/abc-123`. Run `git fetch origin` first.
   - **Current branch is the base branch (`main` or `master`).** Pull the latest. Create the task branch from it. Carry the uncommitted changes to the new branch. If the carry fails with a conflict, stop and ask the user.
   - **Current branch is the task branch.** Rebase it onto `origin/<base>`. Resolve each conflict, keeping the intent of both sides. Run `git rebase --continue`. If a conflict is not clear, stop and ask the user.
   - **Current branch is any other branch.** The branch can belong to another task or to another person. Do not use it as the task branch. Do not rename it.
     1. Run `git log origin/<base>..HEAD --oneline`. Show the commits to the user. Ask which commits belong to this task. Wait for the answer.
     2. If the task branch does not exist, create it from the latest `origin/<base>`. If it exists, check it out and rebase it onto `origin/<base>`.
     3. Apply the chosen commits to the task branch with `git cherry-pick`. Carry the uncommitted changes too.
     4. Resolve each conflict, keeping the intent of both sides. If a conflict is not clear, stop and ask the user.
     5. Do not change or delete the original branch.
   - After this step, the current branch must be the task branch. It must be on top of the latest `origin/<base>`. Check it with `git branch --show-current` and `git merge-base --is-ancestor origin/<base> HEAD`.
5. Check that the code works. Read `package.json` scripts. Run the scripts that exist, in this order: `lint`, `typecheck` (or `tsc`), `test`. If a script fails, stop and show the failure. Do not open the PR.
6. Run `git log <base>..HEAD --oneline` and `git diff <base>...HEAD --stat`. Read all commits and changed files. Include the uncommitted changes in your reading.
7. Run `git diff <base>...HEAD` on the key files. Read enough to understand the substance of the change.
8. Ignore lockfiles, generated files, snapshots, and binary files when you write the Summary. Mention them in one short sentence only when they matter. Example: "The lockfile is regenerated."
9. Write the description (see Output). Copy the same text to the clipboard with the clipboard tool of the OS (`pbcopy` on macOS, `xclip` on Linux).
10. Show the user a preview in the format below. Wait for the user to confirm. Do not commit or push before the user confirms.

    ```
    branch: <task branch>
    title: <PR title>
    preview:
    <the PR body, as it will look on GitHub>
    ```
11. After the user confirms:
    - Commit the changes that are not committed yet. Use the PR title as the commit message. Do not add attribution lines.
    - Push the branch with `git push -u origin <branch>`. Use `--force-with-lease` only if you rebased a branch that is already on the remote.
    - Open the PR: `gh pr create --draft --assignee @me --base <base> --title "<title>" --body "<body>"`. The body is the description without the title line.
12. Print the PR URL.

## Output

Keep the text short and factual. Write only what a reviewer must know. Do not add a checklist or other headings.

Write each part under its own level-3 heading (`### Summary`, `### Testing`, `### Risk`, `### Rollout`, `### Screenshots`, `### JIRA`). Do not use a colon in a heading. Put the text on the lines below the heading. Write the parts in this order. Omit a conditional part when it does not apply.

**1. Title (always).** Use one line, under 70 characters: `type(scope): short description`. Use a conventional commit type (`feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `perf`, `ci`, `build`, `style`). Choose the closest type. The scope is optional. Do not put a period at the end.

**2. Summary (always).** Write the heading `### Summary`. Under it, start with 1–2 prose sentences. State the main change and the reason for it. Put the most important information first. Put the less important information after it.
- Add bullets after the prose only when bullets make the change easier to scan. Each bullet is one STE sentence, in order of importance.
- Name files or functions in code format where they help the reader find the change.
- If the PR changes more than about 15 files (not counting ignored files), write the text by area, not by file.
- State the reason only when the commits, the branch name, or the code show it. If the reason is not clear, state the change only. Never invent a reason.

**3. Testing (conditional).** Add this part only in one of these two cases.
- A reviewer can smoke test the change. Give at most 3 short steps. Example: "Open `/settings/`. The page title shows the new copy."
- A reviewer cannot smoke test the change. Write only: "Unit tests." or "E2E tests." or "Unit and E2E tests." Name only the kinds that cover the change.

**4. Risk (conditional).** Add this part only when the diff touches one of these critical items.
- Auth, session, permissions, or consent code.
- Routing, middleware, or `next.config`.
- Build, CI, Helm, Docker, or deploy files.
- A removed or renamed public prop or export in a shared package. A shared package is a package that other repositories import.

Name the trigger and say who or what is affected. Example text under the heading: "This change removes a public prop. All consumers of `UserCard` must update."

Do not add Risk for other changes. Examples: an edit in a shared package that keeps the API, a dependency bump, or a changed default.

**5. Rollout (conditional).** Add one sentence under the heading only when the change needs a feature flag, a config value, or a deploy order. Name the flag, the value, or the order.

**6. Screenshots (conditional).** Add this part only when the diff changes visible UI. You cannot take screenshots. Write the heading `### Screenshots`, then this HTML table. The user replaces the placeholder images later. Do not use a Markdown table. GitHub shows empty Markdown cells very small. Use exactly this table:

```
<table>
<tr><th width="50%">Before</th><th width="50%">After</th></tr>
<tr>
<td><img src="https://placehold.co/600x360?text=Before" alt="Before" width="100%"></td>
<td><img src="https://placehold.co/600x360?text=After" alt="After" width="100%"></td>
</tr>
</table>
```

**7. JIRA (conditional).** Always add this part, under the heading `### JIRA`, as one line. Use the ticket from step 1. Use the form `<jira-base-url>/browse/TICKET`. If you do not know the Jira base URL, ask the user. If the user says there is no ticket, omit the line.

## Example

> `feat(settings): add profile page copy and metadata`
>
> ### Summary
>
> The profile page now shows the new intro copy and its own page metadata. The metadata falls back to the default metadata for all other pages.
>
> - `metadata.ts` adds `PROFILE_METADATA`.
> - `page.tsx` selects the metadata when the page is `profile`.
> - `ProfilePage` takes a new `description` prop.
>
> ### Testing
>
> Open `/settings/profile/`. The page title and the intro show the new copy.
>
> ### JIRA
>
> https://example.atlassian.net/browse/ABC-123
