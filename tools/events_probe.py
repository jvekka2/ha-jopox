#!/usr/bin/env python3
"""Jopox events probe: read-only debug helper.

Prints only the SHAPE of the responses (field names, types, counts). No titles,
names, tokens or passwords are printed, so the output is safe to attach to an issue.

What it does (the same requests as the Jopox+ app / the integration):
  POST /api/v1/myjopoxaccount/login
  GET  /api/v1/lockerrooms
  GET  /api/v1/site/subsites/<subsiteId>/calendar/upcoming
       ?year=Y&month=M&showMyEventsOnly=false|true

Credentials: JOPOX_EMAIL / JOPOX_PASSWORD environment variables, or prompts
(the password prompt is hidden). Nothing is stored.

Usage:  python tools/events_probe.py [team_index]     (default 0 = first team)
Needs:  Python 3.8+, no extra packages. About six requests, one second apart.
"""
import datetime
import getpass
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://myapi.jopox.fi"
UA = "ha-jopox-probe/0.1 (own account, read-only)"


def req(path, method="GET", body=None, token=None, meta=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Accept-Language": "fi"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    if meta is not None:
        headers["x-metadata"] = str(meta)
    time.sleep(1)
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:  # network problem
        return 0, str(e)


def shape(v, depth=0):
    """Describe JSON without leaking values."""
    if depth > 4:
        return "..."
    if isinstance(v, dict):
        return {k: shape(x, depth + 1) for k, x in v.items()}
    if isinstance(v, list):
        return [f"{len(v)} items"] + ([shape(v[0], depth + 1)] if v else [])
    if isinstance(v, str):
        return f"str(len={len(v)})"
    if isinstance(v, bool) or v is None:
        return type(v).__name__
    return type(v).__name__


def count_events(j):
    if isinstance(j, dict):
        return {k: len(v) for k, v in j.items() if isinstance(v, list)}
    return len(j) if isinstance(j, list) else None


def main():
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    user = os.environ.get("JOPOX_EMAIL") or input("Jopox email: ").strip()
    pw = os.environ.get("JOPOX_PASSWORD") or getpass.getpass("Jopox password (hidden): ")

    st, raw = req("/api/v1/myjopoxaccount/login", "POST", {"username": user, "password": pw})
    if st != 200:
        print("login failed, HTTP", st)
        return
    token = json.loads(raw)["tokens"]["accessToken"]

    st, raw = req("/api/v1/lockerrooms", token=token)
    rooms = json.loads(raw).get("lockerRooms", [])
    print(f"teams on this account: {len(rooms)}; using index {idx}")
    room = rooms[idx]
    meta, sub = room["metadataId"], room["subsiteId"]

    now = datetime.date.today()
    base_path = (
        f"/api/v1/site/subsites/{sub}/calendar/upcoming"
        f"?year={now.year}&month={now.month}&showMyEventsOnly="
    )
    for flag in ("false", "true"):
        st, raw = req(base_path + flag, token=token, meta=meta)
        print(f"\n== showMyEventsOnly={flag} -> HTTP {st}")
        if st != 200:
            print("body (digits hidden):", "".join("#" if c.isdigit() else c for c in raw[:120]))
            continue
        j = json.loads(raw)
        print("counts:", count_events(j))
        if flag == "true":
            print(json.dumps(shape(j), indent=2, ensure_ascii=False)[:3500])

    print("\nDone. The output has no tokens or personal text; review it before sharing.")


if __name__ == "__main__":
    main()
