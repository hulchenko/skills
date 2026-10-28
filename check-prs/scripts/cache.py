#!/usr/bin/env python3
"""Small helper for cache.json. Usage: cache.py set <key> field=value [field=value ...]
Values "true" and "false" become booleans. Adds a timestamp. Used to record tab closes and dismissals."""
import datetime as dt
import json
import os
import sys

path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache.json")
if len(sys.argv) < 4 or sys.argv[1] != "set":
    sys.exit(__doc__)
cache = json.load(open(path)) if os.path.exists(path) else {}
entry = cache.setdefault(sys.argv[2], {})
for kv in sys.argv[3:]:
    k, _, v = kv.partition("=")
    entry[k] = {"true": True, "false": False}.get(v, v)
entry["ts"] = dt.datetime.now(dt.timezone.utc).isoformat()
json.dump(cache, open(path, "w"), indent=1)
