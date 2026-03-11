"""
Check if there is any location/tracking data for the 'one timer' runs:
- 12:43 Urban urban-2-path.gpx (Haptic)  -> P1-Urban-Haptics.db
- 13:55 Non-Urban pyn-2-path.gpx (Visual) -> P1-Non-Urban-Visual.db
"""
import os
import sqlite3
from datetime import datetime

BASE = "Participants-data-pathFinder/Participants-data-pathFinder/P1"

def run_checks():
    # 1) 12:43 Urban Haptic (urban-2-path) - get exact nav timestamp then count logs after
    path_urban = os.path.join(BASE, "P1-Urban-haptic", "P1-Urban-Haptics.db")
    if os.path.isfile(path_urban):
        conn = sqlite3.connect(path_urban)
        cur = conn.cursor()
        # Get timestamp of "Follow path urban-2-path" with Haptic (withHaptic=2 or 1)
        cur.execute("""
            SELECT timestamp, value FROM logs
            WHERE type='navigation'
            ORDER BY timestamp
        """)
        start_urban_ms = None
        for ts, val in cur.fetchall():
            if val and "urban-2-path" in val and "FollowThePathScreenType" in val and ("withHaptic\":2" in val or "withHaptic\":1" in val):
                # Last occurrence is the 12:43 one (first is 12:16 Visual)
                start_urban_ms = ts
        if start_urban_ms is None:
            # fallback: last navigation event in this DB
            cur.execute("SELECT MAX(timestamp) FROM logs WHERE type='navigation'")
            start_urban_ms = cur.fetchone()[0]
        start_urban_dt = datetime.utcfromtimestamp(start_urban_ms / 1000)
        print("--- 12:43 Urban urban-2-path.gpx (Haptic) ---")
        print(f"  Start timestamp (nav log): {start_urban_ms} = {start_urban_dt} UTC")
        cur.execute(
            "SELECT COUNT(*) FROM logs WHERE type='raw-location' AND timestamp >= ?",
            (start_urban_ms,),
        )
        raw_after = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM logs WHERE type='location' AND timestamp >= ?",
            (start_urban_ms,),
        )
        loc_after = cur.fetchone()[0]
        cur.execute(
            "SELECT MIN(timestamp), MAX(timestamp) FROM logs WHERE type='raw-location' AND timestamp >= ?",
            (start_urban_ms,),
        )
        raw_range = cur.fetchone()
        cur.execute(
            "SELECT COUNT(*) FROM logs WHERE type='is-on-track' AND timestamp >= ?",
            (start_urban_ms,),
        )
        iot_after = cur.fetchone()[0]
        conn.close()
        print(f"  raw-location after start: {raw_after}")
        print(f"  location (fused) after start: {loc_after}")
        print(f"  is-on-track events after start: {iot_after}")
        if raw_range and raw_range[0]:
            print(
                f"  raw-location range: {datetime.utcfromtimestamp(raw_range[0]/1000)} to {datetime.utcfromtimestamp(raw_range[1]/1000)}"
            )
        print()

    # 2) 13:55 Non-Urban Visual (pyn-2-path)
    path_non = os.path.join(BASE, "P1-Non-Urban-Visual", "P1-Non-Urban-Visual.db")
    if os.path.isfile(path_non):
        conn = sqlite3.connect(path_non)
        cur = conn.cursor()
        cur.execute("""
            SELECT timestamp, value FROM logs
            WHERE type='navigation'
            ORDER BY timestamp
        """)
        rows = cur.fetchall()
        # Last "Follow path pyn-2-path" with Visual (withHaptic=0 or False)
        start_non_ms = None
        for ts, val in rows:
            if val and "pyn-2-path" in val and "FollowThePathScreenType" in val:
                start_non_ms = ts
        if start_non_ms is None:
            cur.execute("SELECT MAX(timestamp) FROM logs WHERE type='navigation'")
            start_non_ms = cur.fetchone()[0]
        start_non_dt = datetime.utcfromtimestamp(start_non_ms / 1000)
        print("--- 13:55 Non-Urban pyn-2-path.gpx (Visual) ---")
        print(f"  Start timestamp (nav log): {start_non_ms} = {start_non_dt} UTC")
        cur.execute(
            "SELECT COUNT(*) FROM logs WHERE type='raw-location' AND timestamp >= ?",
            (start_non_ms,),
        )
        raw_after = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM logs WHERE type='location' AND timestamp >= ?",
            (start_non_ms,),
        )
        loc_after = cur.fetchone()[0]
        cur.execute(
            "SELECT MIN(timestamp), MAX(timestamp) FROM logs WHERE type='raw-location' AND timestamp >= ?",
            (start_non_ms,),
        )
        raw_range = cur.fetchone()
        cur.execute(
            "SELECT COUNT(*) FROM logs WHERE type='is-on-track' AND timestamp >= ?",
            (start_non_ms,),
        )
        iot_after = cur.fetchone()[0]
        conn.close()
        print(f"  raw-location after start: {raw_after}")
        print(f"  location (fused) after start: {loc_after}")
        print(f"  is-on-track events after start: {iot_after}")
        if raw_range and raw_range[0]:
            print(
                f"  raw-location range: {datetime.utcfromtimestamp(raw_range[0]/1000)} to {datetime.utcfromtimestamp(raw_range[1]/1000)}"
            )
        print()

    # 12:43 run: why 0 raw-location? Check overall raw vs location range in Urban haptic DB
    print("--- 12:43 run detail: raw-location vs location range in P1-Urban-Haptics.db ---")
    if os.path.isfile(path_urban):
        conn = sqlite3.connect(path_urban)
        cur = conn.cursor()
        cur.execute(
            "SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM logs WHERE type='raw-location'"
        )
        r = cur.fetchone()
        print(f"  raw-location total: count={r[2]}, range {datetime.utcfromtimestamp(r[0]/1000)} to {datetime.utcfromtimestamp(r[1]/1000)}")
        cur.execute(
            "SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM logs WHERE type='location'"
        )
        r = cur.fetchone()
        print(f"  location total: count={r[2]}, range {datetime.utcfromtimestamp(r[0]/1000)} to {datetime.utcfromtimestamp(r[1]/1000)}")
        conn.close()


if __name__ == "__main__":
    run_checks()
