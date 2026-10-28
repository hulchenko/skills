# check-prs config (template)

This is a template. Replace every `your-*` and `example-*` value with your own before use.
Keep your real values out of public repos.

The scripts read the JSON block below. Change a value here to change a rule.
Any change to this file changes `rules_version`. Old cached verdicts then stop matching.

```json
{
  "me": "your-github-login",
  "org": "your-org",
  "approvals_enabled": false,
  "priority_team": "your-org/priority-team",
  "default_review_teams": ["your-org/priority-team"],
  "teams": [
    "your-org/priority-team",
    "your-org/team-b",
    "your-org/team-c",
    "your-org/team-d"
  ],
  "trusted_author_teams": ["your-org/priority-team", "your-org/team-b"],
  "repos_apps": [
    "your-org/app-1",
    "your-org/app-2",
    "your-org/app-3",
    "your-org/app-4",
    "your-org/app-5",
    "your-org/app-6",
    "your-org/app-7",
    "your-org/app-8",
    "your-org/app-9"
  ],
  "repos_libs": [
    "your-org/library-1",
    "your-org/library-2",
    "your-org/library-3",
    "your-org/library-4",
    "your-org/library-5"
  ],
  "bot_logins": ["example-service-bot"],
  "thresholds": {
    "easy_lines": 40,
    "easy_files": 4,
    "medium_lines": 200,
    "medium_files": 8
  },
  "stale_days": 14,
  "purge_days": 30,
  "jira_hosts": {
    "default": "yourcompany.atlassian.net",
    "ABC": "yourcompany.atlassian.net",
    "XYZ": "other.atlassian.net"
  },
  "auth_words": ["token", "credential", "session", "jwt", "oauth", "consent", "grpc"],
  "attr_words": ["rel", "target", "href", "sandbox", "crossorigin"],
  "ai_directed_patterns": [
    "\\b(ai|llm|claude|assistant|bot)\\s+(reviewer|agent|review)",
    "\\bnote to (the )?(ai|llm|claude|assistant|reviewer bot)",
    "\\bignore (all |any )?(previous|prior|your|the above) (instructions|rules)",
    "\\b(please )?approve (this|it)( now| immediately)?\\b.*\\b(ai|bot|automatically)",
    "\\bclassify (this )?as (easy|safe)",
    "\\bskip (the )?(checks|review|ci)"
  ]
}
```

## Notes

- `approvals_enabled: false` is the week-1 setting. The skill never batch-approves. It posts only what I choose, one PR at a time.
- Shared packages are all repos in `repos_libs`. Apps get `frontends:frontend-reviewer`. Libraries get the generic Sonnet reviewer.
- Excluded repos: list repos you do not review here.
- Size reference: measure your own past weeks of PRs, then set `thresholds`.
