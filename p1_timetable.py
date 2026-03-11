"""
Build P1 timetable: what P1 did, when (from all P1 DBs).
"""
import os
import json
import sqlite3
from datetime import datetime

BASE = "Participants-data-pathFinder/Participants-data-pathFinder/P1"
# (folder_name, db_filename)
P1_DBS = [
    ("P1-Non-Urban-Haptic", "P1-Non-Urban-Haptic.db"),
    ("P1-Non-Urban-Visual", "P1-Non-Urban-Visual.db"),
    ("P1-Urban-haptic", "P1-Urban-Haptics.db"),
    ("P1-Urban-Visual", "P1-Urban-Visual.db"),
]


def parse_nav_value(value):
    if not value:
        return None
    try:
        j = json.loads(value)
        route = j.get("route") or ""
        args_raw = j.get("args")
        args = json.loads(args_raw) if isinstance(args_raw, str) else None
        path_uri = None
        with_haptic = None
        if args and isinstance(args, dict) and args.get("mMap"):
            path_uri = args["mMap"].get("pathUri")
            with_haptic = args["mMap"].get("withHaptic")
        return {"route": route, "pathUri": path_uri, "withHaptic": with_haptic}
    except (json.JSONDecodeError, TypeError):
        return None


def route_to_activity(route, path_uri, with_haptic):
    """Human-readable activity label."""
    if "Home" in route:
        return "Home"
    if "NavigationTypeSelectScreenType" in route:
        return "Navigation type select (choose path)"
    if "FollowThePathScreenType" in route:
        mode = "Haptic" if with_haptic in (True, 1, 2) else "Visual"
        path_name = os.path.basename(path_uri) if path_uri else "?"
        return f"Follow path ({path_name}) – {mode}"
    return route.split(".")[-1][:40] if route else "?"


def main():
    events = []  # (timestamp_ms, db_label, activity, path_uri, with_haptic)

    for folder, fname in P1_DBS:
        path = os.path.join(BASE, folder, fname)
        if not os.path.isfile(path):
            continue
        db_label = folder  # e.g. P1-Non-Urban-Haptic
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute(
            "SELECT timestamp, value FROM logs WHERE type='navigation' ORDER BY timestamp"
        )
        for ts, val in cur.fetchall():
            data = parse_nav_value(val)
            if not data:
                continue
            activity = route_to_activity(
                data.get("route"),
                data.get("pathUri"),
                data.get("withHaptic"),
            )
            events.append(
                (
                    ts,
                    db_label,
                    activity,
                    data.get("pathUri"),
                    data.get("withHaptic"),
                )
            )
        conn.close()

    # Sort by timestamp
    events.sort(key=lambda x: x[0])

    # Build timetable (by DB so we see sessions per file, then one merged timeline)
    print("=" * 80)
    print("P1 TIMETABLE – What P1 did (all navigation events)")
    print("=" * 80)

    print("\n--- By database (session) ---\n")
    for folder, fname in P1_DBS:
        path = os.path.join(BASE, folder, fname)
        if not os.path.isfile(path):
            continue
        db_events = [e for e in events if e[1] == folder]
        if not db_events:
            continue
        print(f"### {folder} ###")
        for ts, _, activity, path_uri, wh in db_events:
            dt = datetime.utcfromtimestamp(ts / 1000)
            path_short = os.path.basename(path_uri) if path_uri else ""
            print(f"  {dt.strftime('%Y-%m-%d %H:%M:%S')}  {activity}")
        print()

    print("\n--- Merged timeline (all P1 events by time) ---\n")
    print("| Time (UTC) | Session (DB) | Activity |")
    print("|------------|---------------|----------|")
    for ts, db_label, activity, _, _ in events:
        dt = datetime.utcfromtimestamp(ts / 1000)
        print(f"| {dt.strftime('%Y-%m-%d %H:%M:%S')} | {db_label} | {activity} |")

    # Time spans per session
    print("\n--- Approximate session duration per DB ---\n")
    for folder, fname in P1_DBS:
        path = os.path.join(BASE, folder, fname)
        if not os.path.isfile(path):
            continue
        db_events = [e for e in events if e[1] == folder]
        if not db_events:
            continue
        t0 = db_events[0][0]
        t1 = db_events[-1][0]
        dur_m = (t1 - t0) / 1000 / 60
        start = datetime.utcfromtimestamp(t0 / 1000)
        end = datetime.utcfromtimestamp(t1 / 1000)
        follow = sum(1 for e in db_events if "Follow path" in e[2])
        print(f"{folder}: {start.strftime('%H:%M')} – {end.strftime('%H:%M')} (~{dur_m:.0f} min), {len(db_events)} nav events, {follow} 'Follow path' entries")


if __name__ == "__main__":
    main()
