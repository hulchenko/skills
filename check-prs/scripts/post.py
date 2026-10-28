#!/usr/bin/env python3
"""The only code that writes to GitHub. It posts one review (Comment or Approve) after a user choice.

It refuses to post when:
- --user-confirmed is missing;
- CHECK_PRS_DRY_RUN is set;
- the head SHA changed since the PR was reviewed;
- the same action was already posted on the same PR and SHA;
- it is a batch approve while approvals_enabled is false.
It never sends REQUEST_CHANGES.
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = {k: v for k, v in os.environ.items() if k != "GITHUB_TOKEN"}
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from triage import load_config  # noqa: E402


def die(msg, code=1):
    print(json.dumps({"posted": False, "reason": msg}))
    sys.exit(code)


def gh(args, stdin=None):
    r = subprocess.run(["gh"] + args, capture_output=True, text=True, env=ENV, input=stdin)
    if r.returncode:
        die(f"gh failed: {(r.stderr or r.stdout).strip()[:300]}", 4)
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("number", type=int)
    ap.add_argument("sha", help="head SHA saved when the PR was reviewed")
    ap.add_argument("action", choices=["approve", "comment"])
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--comments-file", help="JSON list of {path, line, body}")
    ap.add_argument("--user-confirmed", action="store_true")
    ap.add_argument("--batch", action="store_true")
    a = ap.parse_args()
    cfg = load_config()
    if not a.user_confirmed:
        die("missing --user-confirmed")
    if os.environ.get("CHECK_PRS_DRY_RUN"):
        die("dry run")
    if a.batch and a.action == "approve" and not cfg["approvals_enabled"]:
        die("batch approve is off while approvals_enabled is false")
    head = json.loads(gh(["pr", "view", str(a.number), "-R", a.repo, "--json", "headRefOid,state"]))
    if head["state"] != "OPEN":
        die("PR is not open")
    if head["headRefOid"] != a.sha:
        die(f"head SHA changed: reviewed {a.sha}, now {head['headRefOid']}. Review again.", 3)
    path = os.path.join(ROOT, "cache.json")
    cache = json.load(open(path)) if os.path.exists(path) else {}
    rec = f"post:{a.repo}#{a.number}@{a.sha}"
    if a.action in cache.get(rec, {}).get("actions", []):
        die("already posted this action on this PR and SHA")
    payload = {
        "commit_id": a.sha,
        "event": "APPROVE" if a.action == "approve" else "COMMENT",
        "body": open(a.body_file).read(),
    }
    if a.comments_file:
        payload["comments"] = [{"path": c["path"], "line": c["line"], "side": "RIGHT", "body": c["body"]}
                               for c in json.load(open(a.comments_file))]
    gh(["api", f"repos/{a.repo}/pulls/{a.number}/reviews", "--input", "-"], stdin=json.dumps(payload))
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    entry = cache.setdefault(rec, {"actions": [], "log": []})
    entry["actions"].append(a.action)
    entry["log"].append({"action": a.action, "sha": a.sha, "time": now})
    entry["ts"] = now
    json.dump(cache, open(path, "w"), indent=1)
    print(json.dumps({"posted": True, "action": a.action, "sha": a.sha, "time": now}))


if __name__ == "__main__":
    main()
