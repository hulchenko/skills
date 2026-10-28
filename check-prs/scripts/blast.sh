#!/usr/bin/env bash
# Blast-radius search: who uses a symbol? Usage: blast.sh <symbol>
# Results are cached by symbol in blast-cache.json. Waits 7 seconds between live searches (limit: 10 per minute).
set -euo pipefail
dir="$(cd "$(dirname "$0")/.." && pwd)"
cache="$dir/blast-cache.json"
[ -f "$cache" ] || echo '{}' > "$cache"
sym="$1"
if jq -e --arg s "$sym" 'has($s)' "$cache" >/dev/null 2>&1; then
  jq --arg s "$sym" '.[$s]' "$cache"
  exit 0
fi
sleep 7
res=$(env -u GITHUB_TOKEN gh search code "$sym" --owner "${CHECK_PRS_ORG:-your-org}" --limit 100 --json repository,path,url \
  | jq '{hits: length, capped: (length >= 100), top_repos: (group_by(.repository.nameWithOwner)
        | map({repo: .[0].repository.nameWithOwner, n: length}) | sort_by(-.n) | .[:8]),
        examples: .[:6] | map(.url)}')
tmp=$(mktemp)
jq --arg s "$sym" --argjson r "$res" '. + {($s): $r}' "$cache" > "$tmp" && mv "$tmp" "$cache"
echo "$res"
