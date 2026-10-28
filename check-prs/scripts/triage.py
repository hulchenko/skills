#!/usr/bin/env python3
"""Fetch open PRs that need my review, apply the skip rules, and compute the code type.

Prints one JSON object. Read-only: this script never writes to GitHub or Jira.
Models never decide a type. This script does.
"""
import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = {k: v for k, v in os.environ.items() if k != "GITHUB_TOKEN"}
NOW = dt.datetime.now(dt.timezone.utc)

PR_FIELDS = (
    "number,title,body,author,isDraft,baseRefName,headRefOid,labels,reviewDecision,"
    "reviewRequests,reviews,statusCheckRollup,mergeable,createdAt,updatedAt,"
    "additions,deletions,changedFiles,files,url"
)
TEST_RE = re.compile(r"(\.(test|spec)\.[jt]sx?$|/__tests__/|/__mocks__/|\.snap$)")
STORY_RE = re.compile(r"(\.stories\.[jt]sx?$|\.stories\.mdx$|/stories/)")
LOCK_RE = re.compile(r"(^|/)(pnpm-lock\.yaml|package-lock\.json|yarn\.lock)$")
GENERATED_RE = re.compile(r"(/generated/|/__generated__/|^generated/)")
DOC_RE = re.compile(r"\.(md|mdx)$")
BINARY_RE = re.compile(r"\.(png|jpe?g|gif|webp|ico|woff2?|ttf|pdf|mp4|mov|zip)$", re.I)
HARD_PATHS = [
    ("auth/session/permissions", r"(auth|session|permission|login|oauth|jwt|consent|credential|token)"),
    ("checkout/cart/payments/pricing", r"(checkout|/cart|cart/|payment|pricing|billing)"),
    ("routing/middleware/next.config/workers", r"(middleware\.|next\.config|routing|cloudflare|/routes?/)"),
    ("build/CI/Helm/Docker/ArgoCD/stencil",
     r"(^\.github/|^\.circleci/|dockerfile|(^|/)helm/|argocd|stencil\.yaml|webpack\.config|turbo\.json)"),
]
COMMENT_LINE_RE = re.compile(r"^\s*(//|/\*|\*/|\*|#)")


class GhError(Exception):
    pass


def gh(args):
    r = subprocess.run(["gh"] + args, capture_output=True, text=True, env=ENV)
    if r.returncode:
        raise GhError((r.stderr or r.stdout).strip()[:300])
    return r.stdout


def load_config():
    text = open(os.path.join(ROOT, "config.md")).read()
    m = re.search(r"```json\n(.*?)\n```", text, re.S)
    cfg = json.loads(m.group(1))
    cfg["rules_version"] = hashlib.sha1(text.encode()).hexdigest()[:8]
    return cfg


def load_cache():
    try:
        return json.load(open(os.path.join(ROOT, "cache.json")))
    except (OSError, ValueError):
        return {}


def purge(cache, days):
    """Drop cache entries and reports older than `days`."""
    cutoff = NOW - dt.timedelta(days=days)
    keep = {k: v for k, v in cache.items() if _ts(v.get("ts")) >= cutoff}
    if len(keep) != len(cache):
        json.dump(keep, open(os.path.join(ROOT, "cache.json"), "w"), indent=1)
    rdir = os.path.join(ROOT, "reports")
    for f in os.listdir(rdir) if os.path.isdir(rdir) else []:
        p = os.path.join(rdir, f)
        if f.endswith(".md") and dt.datetime.fromtimestamp(os.path.getmtime(p), dt.timezone.utc) < cutoff:
            os.remove(p)
    return keep


def _ts(s):
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return dt.datetime.min.replace(tzinfo=dt.timezone.utc)


_members = {}


def members(team, failures):
    """Logins in a team, or None when GitHub does not let me read it."""
    if team not in _members:
        org, slug = team.split("/")
        try:
            out = gh(["api", f"orgs/{org}/teams/{slug}/members", "--paginate", "--jq", ".[].login"])
            _members[team] = {x.lower() for x in out.split()}
        except GhError as e:
            _members[team] = None
            failures.append(f"team {team}: {e}")
    return _members[team]


def codeowners(repo, ref, failures):
    for path in (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS"):
        try:
            out = gh(["api", f"repos/{repo}/contents/{path}?ref={ref}", "--jq", ".content"])
            text = base64.b64decode(out).decode("utf-8", "replace")
            rules = []
            for line in text.splitlines():
                line = line.split("#", 1)[0].strip()
                if line:
                    parts = line.split()
                    rules.append((parts[0], [o.lower() for o in parts[1:]]))
            return rules
        except GhError:
            continue
    failures.append(f"{repo}: no CODEOWNERS found")
    return []


def pattern_rx(pat):
    anchored = pat.startswith("/") or "/" in pat.rstrip("/")
    dir_only = pat.endswith("/")
    pat = pat.strip("/")
    rx = ""
    i = 0
    while i < len(pat):
        if pat.startswith("**/", i):
            rx += "(?:.*/)?"
            i += 3
        elif pat.startswith("**", i):
            rx += ".*"
            i += 2
        elif pat[i] == "*":
            rx += "[^/]*"
            i += 1
        elif pat[i] == "?":
            rx += "[^/]"
            i += 1
        else:
            rx += re.escape(pat[i])
            i += 1
    prefix = "^" if anchored else "(?:^|.*/)"
    return re.compile(prefix + rx + ("/.*$" if dir_only else "(?:/.*)?$"))


def owners_for(rules, path):
    owners = []
    for pat, who in rules:
        if pattern_rx(pat).match(path):
            owners = who
    return owners


def latest_reviews(reviews):
    """Latest non-comment review state per login, plus the commit it was made on."""
    out = {}
    for r in sorted(reviews, key=lambda r: r.get("submittedAt") or ""):
        login = ((r.get("author") or {}).get("login") or "").lower()
        if login and r.get("state") in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            out[login] = (r["state"], (r.get("commit") or {}).get("oid"))
    return out


def ci_state(rollup):
    """green, red, pending, or none. Check runs use conclusion, status contexts use state."""
    red = pend = False
    items = []
    for c in rollup or []:
        if c.get("__typename") == "StatusContext":
            s = (c.get("state") or "").upper()
            name = c.get("context")
            bad, wait = s in ("FAILURE", "ERROR"), s in ("PENDING", "EXPECTED", "")
        else:
            name = c.get("name")
            if (c.get("status") or "").upper() != "COMPLETED":
                s, bad, wait = (c.get("status") or "").upper(), False, True
            else:
                s = (c.get("conclusion") or "").upper()
                bad = s in ("FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE", "STALE")
                wait = s == ""
        red |= bad
        pend |= wait
        items.append((name, s))
    state = "red" if red else "pending" if pend else "green" if items else "none"
    digest = hashlib.sha1(json.dumps(sorted(items, key=str)).encode()).hexdigest()[:8]
    return state, digest


def parse_diff(diff):
    """Per-file: changed lines, deleted, binary."""
    files = {}
    cur = None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            m = re.match(r"diff --git a/(.*) b/(.*)$", line)
            cur = files.setdefault(m.group(2) if m else line, {"lines": [], "deleted": False, "binary": False})
        elif cur is None:
            continue
        elif line.startswith("deleted file mode"):
            cur["deleted"] = True
        elif line.startswith("Binary files") or line.startswith("GIT binary patch"):
            cur["binary"] = True
        elif line[:1] in "+-" and not line.startswith(("+++", "---")):
            cur["lines"].append(line)
    return files


def jira_fetch(key, cfg):
    prefix = key.split("-")[0]
    host = cfg["jira_hosts"].get(prefix, cfg["jira_hosts"]["default"])
    return jira_lookup(key, host)


def jira_lookup(key, host):
    user, token = os.environ.get("ATLASSIAN_USERNAME"), os.environ.get("ATLASSIAN_API_TOKEN")
    if not user or not token:
        return {"key": key, "host": host, "status": "not reachable: no credentials"}
    q = urllib.parse.urlencode({"jql": f"key = {key}", "fields": "key,summary,status,description"})
    req = urllib.request.Request(f"https://{host}/rest/api/3/search/jql?{q}")
    req.add_header("Authorization", "Basic " + base64.b64encode(f"{user}:{token}".encode()).decode())
    try:
        data = json.load(urllib.request.urlopen(req, timeout=20))
    except Exception as e:  # network, auth, or JSON error
        return {"key": key, "host": host, "status": f"not reachable: {type(e).__name__}"}
    issues = data.get("issues") or []
    if not issues:
        return {"key": key, "host": host, "status": "not reachable: 0 issues (wrong host or no access)"}
    f = issues[0]["fields"]
    return {"key": key, "host": host, "status": "ok", "summary": f.get("summary"),
            "ticket_status": (f.get("status") or {}).get("name")}


def classify(pr, repo, cfg, diff, trusted, is_lib):
    th = cfg["thresholds"]
    files = pr.get("files") or []

    def counted(f):
        p = f["path"]
        return not (TEST_RE.search(p) or STORY_RE.search(p) or LOCK_RE.search(p) or GENERATED_RE.search(p))

    cf = [f for f in files if counted(f)]
    lines = sum(f["additions"] + f["deletions"] for f in cf)
    flags = {
        "tests_stories_lines": sum(f["additions"] + f["deletions"] for f in files
                                   if TEST_RE.search(f["path"]) or STORY_RE.search(f["path"])),
        "lockfile_lines": sum(f["additions"] + f["deletions"] for f in files if LOCK_RE.search(f["path"])),
        "files_truncated": (pr.get("changedFiles") or 0) > len(files),
    }
    hard = []
    parsed = parse_diff(diff) if diff is not None else {}
    if diff is None:
        hard.append("diff unavailable (too large or fetch failed)")
    if flags["files_truncated"]:
        hard.append("file list truncated")
    for f in cf:
        low = f["path"].lower()
        for name, rx in HARD_PATHS:
            if re.search(rx, low) and name not in hard:
                hard.append(name)
    changed = [l for p, d in parsed.items() if any(f["path"] == p for f in cf) for l in d["lines"]]
    text = "\n".join(changed).lower()
    for w in cfg["auth_words"]:
        if re.search(rf"\b{re.escape(w)}", text):
            hard.append(f"diff word: {w}")
            break
    attrs = [w for w in cfg["attr_words"] if re.search(rf"\b{re.escape(w)}\b\s*[=:]", text)]
    if attrs:
        hard.append("sensitive attribute: " + ",".join(attrs))
    binary = any(d["binary"] for d in parsed.values()) or any(BINARY_RE.search(f["path"]) for f in files)
    deleted = any(d["deleted"] for d in parsed.values())
    body_lines = [l[1:] for l in changed if l[1:].strip()]
    comment_only = bool(changed) and all(COMMENT_LINE_RE.match(l) for l in body_lines)
    docs_only = bool(cf) and all(DOC_RE.search(f["path"]) for f in cf)
    shared_nontrivial = is_lib and bool(cf) and not (comment_only or docs_only)
    if shared_nontrivial:
        hard.append("change in shared package")
    if lines > th["medium_lines"]:
        hard.append(f"> {th['medium_lines']} counted lines")
    if len(cf) > th["medium_files"]:
        hard.append(f"> {th['medium_files']} counted files")
    dirs = {os.path.dirname(f["path"]).split("/")[0] for f in cf}
    if len(dirs) > 6:
        hard.append("spans many directories")
    suspicious = any(re.search(p, f"{pr.get('title','')}\n{pr.get('body','')}", re.I)
                     for p in cfg["ai_directed_patterns"])
    if suspicious:
        hard.append("suspicious: AI-directed text in PR")

    if hard:
        code_type = "hard"
    elif (lines <= th["easy_lines"] and len(cf) <= th["easy_files"] and trusted
          and not binary and not deleted):
        code_type = "easy"
    else:
        code_type = "medium"
    return {
        "counted_lines": lines, "counted_files": len(cf), "flags": flags, "hard_signals": hard,
        "binary_or_deleted": binary or deleted, "shared_nontrivial": shared_nontrivial,
        "needs_blast_search": shared_nontrivial, "suspicious": suspicious, "code_type": code_type,
        "trusted_author": trusted,
        "cannot_review_content": binary or deleted,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--team")
    ap.add_argument("--repo")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--jira", metavar="KEY", help="print one Jira ticket and exit")
    args = ap.parse_args()
    cfg = load_config()
    if args.jira:
        print(json.dumps(jira_fetch(args.jira, cfg), indent=1))
        return
    try:
        gh(["api", "user", "--jq", ".login"])
    except GhError as e:
        print(json.dumps({"fatal": f"GitHub login failed: {e}"}))
        sys.exit(2)

    cache = purge(load_cache(), cfg["purge_days"])
    me = cfg["me"].lower()
    my_teams = {t.lower() for t in cfg["teams"]}
    req_teams = {t.split("/")[1].lower() for t in cfg["default_review_teams"]}
    if args.team:
        req_teams = {args.team.split("/")[-1].lower()}
    prio_slug = cfg["priority_team"].split("/")[1].lower()
    failures, skipped, rows, skipped_rows = [], {}, [], []
    trusted_logins = set()
    for t in cfg["trusted_author_teams"]:
        trusted_logins |= members(t, failures) or set()
    bots = {b.lower() for b in cfg["bot_logins"]}
    libs = set(cfg["repos_libs"])
    repos = cfg["repos_apps"] + cfg["repos_libs"]
    if args.repo:
        repos = [r for r in repos if r == args.repo]
    today = dt.date.today().isoformat()

    def skip(reason, row=None):
        skipped[reason] = skipped.get(reason, 0) + 1
        if args.verbose and row:
            skipped_rows.append({"url": row["url"], "reason": reason})

    for repo in repos:
        try:
            base = gh(["repo", "view", repo, "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name"]).strip()
            prs = json.loads(gh(["pr", "list", "-R", repo, "--state", "open", "--limit", "100", "--json", PR_FIELDS]))
        except GhError as e:
            failures.append(f"{repo}: {e}")
            continue
        rules = None
        for pr in prs:
            reqs = pr.get("reviewRequests") or []
            direct = any(r.get("__typename") == "User" and (r.get("login") or "").lower() == me for r in reqs)
            team_hits = [(r.get("slug") or "").lower().split("/")[-1] for r in reqs
                         if r.get("__typename") == "Team"
                         and (r.get("slug") or "").lower().split("/")[-1] in req_teams]
            if not (direct or team_hits):
                continue
            row = {"url": pr["url"]}
            author = ((pr.get("author") or {}).get("login") or "").lower()
            is_bot = ((pr.get("author") or {}).get("is_bot") or author.endswith("[bot]")
                      or author.endswith("-bot") or author in bots)
            label_names = [l["name"].lower() for l in pr.get("labels") or []]
            title = pr.get("title") or ""
            lr = latest_reviews(pr.get("reviews") or [])
            mine = lr.get(me)
            head = pr["headRefOid"]
            ci, cihash = ci_state(pr.get("statusCheckRollup"))
            key = f"{repo}#{pr['number']}@{head}|v{cfg['rules_version']}|{ci}{cihash}"
            entry = cache.get(key) or {}
            if pr.get("isDraft"):
                skip("draft", row); continue
            if author == me:
                skip("mine", row); continue
            if is_bot:
                skip("bot author", row); continue
            if pr["baseRefName"] != base:
                skip("stacked PR", row); continue
            if any(re.search(r"(wip|do.?not.?review|hold)", n) for n in label_names) or re.match(r"\s*\[?wip\]?", title, re.I):
                skip("WIP/hold", row); continue
            if pr.get("reviewDecision") == "CHANGES_REQUESTED" and any(
                    s == "CHANGES_REQUESTED" for l, (s, _) in lr.items() if l != me):
                skip("changes requested by others", row); continue
            if mine and mine[0] == "APPROVED" and mine[1] == head:
                skip("already approved by me", row); continue
            if entry.get("dismissed") or entry.get("closed_date") == today:
                skip("done or dismissed today", row); continue
            if rules is None:
                rules = codeowners(repo, base, failures)
            files = pr.get("files") or []
            owned = {f["path"]: owners_for(rules, f["path"]) for f in files}
            owned = {p: o for p, o in owned.items() if o}
            owner_teams = {o.lstrip("@") for os_ in owned.values() for o in os_ if "/" in o}

            def me_owner(o):
                o = o.lstrip("@")
                return o == me or o in my_teams

            i_am_owner = any(me_owner(o) for os_ in owned.values() for o in os_)
            approvers = {l for l, (s, _) in lr.items() if s == "APPROVED" and l != me}
            co_approved = bool(owned) and all(
                any((o.lstrip("@") in approvers) or (
                    "/" in o and approvers & (members(o.lstrip("@"), failures) or set()))
                    for o in os_) for os_ in owned.values())
            if co_approved:
                skip("code owner already approved", row); continue
            if not i_am_owner and not direct:
                skip("not a code owner and not asked directly", row); continue
            try:
                diff = gh(["pr", "diff", str(pr["number"]), "-R", repo])
            except GhError:
                diff = None
            c = classify(pr, repo, cfg, diff, author in trusted_logins, repo in libs)
            jira = None
            if c["code_type"] == "medium":
                keys = re.findall(r"\b[A-Z][A-Z0-9]+-\d+\b", f"{title}\n{pr.get('body') or ''}")
                jira = []
                for k in dict.fromkeys(keys):
                    m = re.search(rf"https://([a-z0-9.-]+\.atlassian\.net)/browse/{k}", pr.get("body") or "")
                    jira.append(jira_lookup(k, m.group(1)) if m else jira_fetch(k, cfg))
            try:
                cmp = json.loads(gh(["api", f"repos/{repo}/compare/{base}...{head}"]))
                behind = cmp.get("behind_by", 0)
            except (GhError, ValueError):
                behind = None
            age = (NOW - _ts(pr["createdAt"])).days
            state = []
            if ci in ("red", "pending"):
                state.append(f"CI {ci}")
            if pr.get("mergeable") == "CONFLICTING":
                state.append("conflict")
            if age > cfg["stale_days"]:
                state.append("stale")
            rd = pr.get("reviewDecision") or ""
            body = re.sub(r"<!--.*?-->", "", pr.get("body") or "", flags=re.S)
            rows.append({
                "repo": repo, "number": pr["number"], "url": pr["url"], "title": title, "author": author,
                "kind": "library" if repo in libs else "app",
                "reason": "direct" if direct else "priority-team" if prio_slug in team_hits else "team",
                "priority": 1 if direct else 2 if prio_slug in team_hits else 3,
                "created_at": pr["createdAt"], "age_days": age, "head_sha": head, "base": base,
                "lines_total": pr["additions"] + pr["deletions"], "ci": ci, "review_decision": rd or "NONE",
                "state": state, "approve_blocked": bool(state) or rd not in ("REVIEW_REQUIRED", "APPROVED"),
                "my_prior_approval_sha": mine[1] if mine and mine[0] == "APPROVED" else None,
                "i_am_code_owner": i_am_owner, "owner_teams": sorted(owner_teams),
                "other_reviewers": sorted(approvers),
                "jira": jira, "description_chars": len(re.sub(r"[\s#\-\*\[\]x]", "", body)),
                "body_excerpt": body[:1500], "files": [(f["path"], f["additions"], f["deletions"]) for f in files],
                "behind_by": behind, "branch_behind": bool(behind),
                "cache_key": key, "cache_entry": entry, **c,
            })
    rows.sort(key=lambda r: (r["priority"], r["created_at"]))
    out = {"generated_at": NOW.isoformat(), "rules_version": cfg["rules_version"],
           "approvals_enabled": cfg["approvals_enabled"], "failures": failures, "skipped": skipped, "prs": rows}
    if args.verbose:
        out["skipped_rows"] = skipped_rows
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
