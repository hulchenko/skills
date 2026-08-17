---
name: pr-create
description: Use when the user asks for a PR description, PR title, or a summary of the current branch's changes to open a pull request. Optionally takes a JIRA ticket (e.g. CVR-2411) as an argument.
---

Generate PR description text for the current branch.

## Steps

1. Run `git log main..HEAD --oneline` and `git diff main...HEAD --stat` to understand all commits and changed files.
2. Run `git diff main...HEAD` on key changed files as needed to understand the substance of changes.
3. The JIRA ticket is provided in $ARGUMENTS (e.g. `CVR-2411`).
4. Output the PR description text — nothing else. Do not push, do not run `gh pr create`.

## Output Format

Keep everything concise, factual, and trimmed — no elaborate paragraphs, no filler, only what's crucial and important to note. Output exactly four things in order:

**1. A PR title** — one line, under 70 characters, in the form `type(scope): short description`. Use conventional commit types (`feat`, `fix`, `refactor`, `chore`). No period at the end.

**2. A `###### What:` section** — 1–2 sentences stating what changed and why. No restating the title, no bullet list, no elaboration beyond what's necessary to understand the change.

**3. A `###### Key changes:` section** — one bullet per file or area, only where it adds information beyond the title: `filename — what changed`. One short line per bullet, no sub-bullets. Omit trivial or self-evident changes.

**4. A `###### JIRA:` line** — a full Atlassian URL in the form `https://udemy.atlassian.net/browse/TICKET`. If no ticket is provided in $ARGUMENTS, omit this line.

Example:

> `refactor(lohp): migrate LOHP data layer to hide-on-failure policy`
>
> ###### What:
>
> Aligns all LOHP sections with v1's "hide on failure" policy: removes hardcoded fixture fallbacks and makes every data-driven section return `null` on fetch failure instead of rendering stale content.
>
> ###### Key changes:
>
> - `hero-banner.tsx` — extracted `useHeroBanners` hook; kept `HERO_BANNER_FALLBACK` as the lone exception
> - `gwg-section.tsx` — hides when no data is present
> - `discovery-units.tsx` — removed fixture data; hides on empty
>
> ###### JIRA: https://udemy.atlassian.net/browse/CVR-2411

That is the complete output. No checklist, no extra headers — just the title, What, Key changes, and JIRA.
