"""
Analyze P1 participant data for issues (navigation, screen selection, location, base path).
"""
import os
import sys
import json
import sqlite3

sys.path.insert(0, "src")
import pandas as pd
from utils.logs import fetch_logs, normalize_logs

BASE = os.path.join(
    "Participants-data-pathFinder", "Participants-data-pathFinder", "P1"
)
DBs = [
    ("P1-Non-Urban-Haptic", "P1-Non-Urban-Haptic.db"),
    ("P1-Non-Urban-Visual", "P1-Non-Urban-Visual.db"),
    ("P1-Urban-haptic", "P1-Urban-Haptics.db"),
    ("P1-Urban-Visual", "P1-Urban-Visual.db"),
]


def get_db_path(folder: str, fname: str) -> str:
    return os.path.join(BASE, folder, fname)


def parse_nav_value(value):
    if not value:
        return None
    try:
        j = json.loads(value)
        route = j.get("route")
        args_raw = j.get("args")
        args = json.loads(args_raw) if isinstance(args_raw, str) else None
        pathUri = None
        withHaptic = None
        if args and isinstance(args, dict) and args.get("mMap"):
            pathUri = args["mMap"].get("pathUri")
            withHaptic = args["mMap"].get("withHaptic")
        return {"route": route, "pathUri": pathUri, "withHaptic": withHaptic}
    except (json.JSONDecodeError, TypeError):
        return None


def main():
    print("=" * 60)
    print("P1 DATA ANALYSIS")
    print("=" * 60)

    for folder, fname in DBs:
        path = get_db_path(folder, fname)
        if not os.path.isfile(path):
            print(f"\n--- {folder} / {fname} --- FILE NOT FOUND")
            continue

        print(f"\n--- {folder} / {fname} ---")
        conn = sqlite3.connect(path)
        cur = conn.cursor()

        # Log type counts
        cur.execute("SELECT type, COUNT(*) FROM logs GROUP BY type ORDER BY type")
        type_counts = cur.fetchall()
        key_types = ["navigation", "navigation-started", "current-segment", "current-max-deviation", "location", "raw-location", "is-on-track"]
        for t, c in type_counts:
            if t in key_types:
                print(f"  {t}: {c}")

        # Navigation logs
        cur.execute("SELECT timestamp, value FROM logs WHERE type='navigation' ORDER BY timestamp")
        nav_rows = cur.fetchall()
        print(f"  navigation rows: {len(nav_rows)}")

        parse_fail = 0
        no_route = 0
        no_placeholders = 0
        no_pathUri = 0
        samples = []
        for ts, val in nav_rows[:8]:
            data = parse_nav_value(val)
            if data is None:
                parse_fail += 1
                continue
            if data.get("route") is None:
                no_route += 1
            route = (data.get("route") or "")
            if "{withHaptic}" not in route or "{pathUri}" not in route:
                no_placeholders += 1
            if not data.get("pathUri"):
                no_pathUri += 1
            samples.append((ts, route[:60], data.get("pathUri"), data.get("withHaptic")))

        for ts, r, pu, wh in samples[:4]:
            print(f"    sample: route={r!r} pathUri={pu!r} withHaptic={wh}")

        if parse_fail or no_route or no_placeholders:
            print(f"  ISSUES: parse_fail={parse_fail} no_route={no_route} route_without_placeholders={no_placeholders} no_pathUri={no_pathUri}")

        # Screens in dropdown (route has both placeholders)
        screens_count = 0
        for ts, val in nav_rows:
            data = parse_nav_value(val)
            if data and data.get("route"):
                if "{withHaptic}" in data["route"] and "{pathUri}" in data["route"]:
                    screens_count += 1
        print(f"  screens (FollowThePath) in dropdown: {screens_count}")

        # current-segment / current-max-deviation (base path)
        cur.execute("SELECT COUNT(*) FROM logs WHERE type='current-segment'")
        cs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM logs WHERE type='current-max-deviation'")
        cmd = cur.fetchone()[0]
        print(f"  current-segment: {cs}, current-max-deviation: {cmd}")
        if cs == 0 or cmd == 0:
            print("  ISSUE: missing base path data (current-segment or current-max-deviation)")

        # location vs raw-location
        cur.execute("SELECT COUNT(*) FROM logs WHERE type='location'")
        loc = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM logs WHERE type='raw-location'")
        raw = cur.fetchone()[0]
        print(f"  location: {loc}, raw-location: {raw}")
        if loc == 0 and raw == 0:
            print("  ISSUE: no location data")

        # is-on-track
        cur.execute("SELECT value, COUNT(*) FROM logs WHERE type='is-on-track' GROUP BY value")
        iot = cur.fetchall()
        print(f"  is-on-track values: {iot}")

        # Timestamp range
        cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM logs")
        tmin, tmax = cur.fetchone()
        if tmin and tmax:
            print(f"  timestamp range: {tmin} .. {tmax}")

        # Sample raw location value (valid lat/lon?)
        cur.execute("SELECT value FROM logs WHERE type='raw-location' LIMIT 1")
        row = cur.fetchone()
        if row and row[0]:
            v = row[0]
            if '"latitude"' in v and '"longitude"' in v:
                print("  raw-location sample: has latitude/longitude")
            else:
                print("  raw-location sample: MISSING or malformed latitude/longitude")

        conn.close()

    # Deep dive: P1-Non-Urban-Haptic segment vs max-deviation alignment
    print("\n--- P1-Non-Urban-Haptic: current-segment vs current-max-deviation timestamps ---")
    path = get_db_path("P1-Non-Urban-Haptic", "P1-Non-Urban-Haptic.db")
    if os.path.isfile(path):
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute(
            "SELECT timestamp, type FROM logs WHERE type IN ('current-segment', 'current-max-deviation') ORDER BY timestamp"
        )
        for ts, typ in cur.fetchall():
            from datetime import datetime
            dt = datetime.utcfromtimestamp(ts / 1000)
            print(f"  {ts} {dt} {typ}")
        conn.close()

    print("\n" + "=" * 60)
    print("Done.")


if __name__ == "__main__":
    main()
