#!/usr/bin/env bash
# Fetch and classify PRs that need my review. Read-only. Pass-through args: --team, --repo, --verbose, --jira KEY.
# GITHUB_TOKEN in my shell is invalid, so triage.py removes it before every gh call.
exec python3 "$(dirname "$0")/triage.py" "$@"
