"""Inspect navigation logs in all_participants_db for screen selection issues."""
import sqlite3
import os
import json

db_dir = "all_participants_db"
dbs = sorted([f for f in os.listdir(db_dir) if f.endswith(".db")])

print("=== Schema and log type counts (first 3 DBs) ===\n")
for db_name in dbs[:3]:
    path = os.path.join(db_dir, db_name)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    print(f"--- {db_name} ---")
    print("Tables:", tables)
    cur.execute("PRAGMA table_info(logs)")
    print("logs columns:", cur.fetchall())
    cur.execute("SELECT type, COUNT(*) FROM logs GROUP BY type ORDER BY type")
    print("Log types and counts:", cur.fetchall())
    conn.close()
    print()

print("=== Navigation log samples (raw value) from first DB ===\n")
path = os.path.join(db_dir, dbs[0])
conn = sqlite3.connect(path)
cur = conn.cursor()
cur.execute("SELECT timestamp, type, value FROM logs WHERE type='navigation' LIMIT 5")
rows = cur.fetchall()
for ts, typ, val in rows:
    print(f"ts={ts} type={typ}")
    print(f"  value (first 500 chars): {repr(val[:500]) if val else None}")
    print()
conn.close()

print("=== All navigation 'value' formats (sample across DBs) ===\n")
seen_formats = set()
for db_name in dbs[:5]:
    path = os.path.join(db_dir, db_name)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT value FROM logs WHERE type='navigation' LIMIT 2")
    for (val,) in cur.fetchall():
        if val:
            try:
                j = json.loads(val)
                keys = tuple(sorted(j.keys()))
                args = j.get("args")
                args_keys = tuple(sorted(json.loads(args).keys())) if isinstance(args, str) else (type(args).__name__,)
                seen_formats.add((keys, args_keys))
            except Exception as e:
                seen_formats.add(("PARSE_ERROR", str(e)[:80]))
    conn.close()
print("Seen (top-level keys, args keys):", seen_formats)

print("\n=== Check for missing route/pathUri/withHaptic (manual parse) ===\n")
def parse_nav_value(value):
    if not value:
        return None
    try:
        j = json.loads(value)
        route = j.get("route")
        args_raw = j.get("args")
        args = json.loads(args_raw) if args_raw else None
        pathUri = None
        withHaptic = None
        if args and isinstance(args, dict):
            mMap = args.get("mMap")
            if mMap:
                pathUri = mMap.get("pathUri")
                withHaptic = mMap.get("withHaptic")
        return {"route": route, "pathUri": pathUri, "withHaptic": withHaptic}
    except (json.JSONDecodeError, TypeError):
        return None

for db_name in dbs[:5]:
    path = os.path.join(db_dir, db_name)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT value FROM logs WHERE type='navigation'")
    rows = cur.fetchall()
    conn.close()
    none_count = 0
    missing_route = 0
    missing_path = 0
    missing_haptic = 0
    no_placeholders = 0  # route without {withHaptic} or {pathUri}
    for (val,) in rows:
        data = parse_nav_value(val)
        if data is None:
            none_count += 1
            continue
        if data.get("route") is None:
            missing_route += 1
        if data.get("pathUri") is None or data.get("pathUri") == "":
            missing_path += 1
        if data.get("withHaptic") is None:
            missing_haptic += 1
        route = data.get("route") or ""
        if "{withHaptic}" not in route or "{pathUri}" not in route:
            no_placeholders += 1
    print(f"{db_name}: total={len(rows)}, parse=None={none_count}, route missing={missing_route}, pathUri missing={missing_path}, withHaptic missing={missing_haptic}, route without placeholders={no_placeholders}")

print("\n=== Simulate screen_selection: how many screens per DB? ===\n")
import sys
sys.path.insert(0, "src")
import pandas as pd
from utils.logs import fetch_logs

zero_screens = []
for db_name in dbs:
    path = os.path.join(db_dir, db_name)
    raw = fetch_logs(path, ["navigation"])
    if raw.empty:
        print(f"{db_name}: 0 nav logs -> 0 screens")
        continue
    # Build same df as fetch_navigation_logs (simplified: no process_row, we need route/pathUri/withHaptic)
    parsed = []
    for _, row in raw.iterrows():
        data = parse_nav_value(row["value"])
        if data is None:
            parsed.append({"timestamp": row["timestamp"], "route": None, "pathUri": None, "withHaptic": None})
        else:
            parsed.append({
                "timestamp": row["timestamp"],
                "route": data.get("route"),
                "pathUri": data.get("pathUri"),
                "withHaptic": data.get("withHaptic"),
            })
    df = pd.DataFrame(parsed)
    df["next_screen_timestamp"] = df["timestamp"].shift(-1)
    # Filter like screen_selection: route must contain both placeholders
    mask = df["route"].notna() & df["route"].str.contains("{withHaptic}", na=False) & df["route"].str.contains("{pathUri}", na=False)
    nav_screens = df[mask]
    n = len(nav_screens)
    empty_path = (nav_screens["pathUri"].isna() | (nav_screens["pathUri"] == "")).sum()
    unknown_haptic = nav_screens["withHaptic"].apply(lambda x: x not in (True, False, 1, 2, None)).sum()
    last_na_end = nav_screens["next_screen_timestamp"].isna().sum()
    if n == 0:
        zero_screens.append(db_name)
    print(f"{db_name}: {n} screens in dropdown, pathUri empty={empty_path}, withHaptic not True/False/1/2={unknown_haptic}, last row has NaT end={last_na_end}")
print("\nDBs with 0 screens in dropdown (but may have nav logs):", zero_screens)
