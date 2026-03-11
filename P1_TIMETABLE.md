# P1 Timetable – What P1 Did

All times in **UTC** (2025-10-15). Each section is one exported session (one DB file).

---

## Session 1: P1-Urban (Visual + Haptic DBs)

**Approx. 12:16 – 12:43 (~27 min for haptic DB; Visual DB has 1 run ~12:16–12:21)**

| Time (UTC) | Activity |
|------------|----------|
| 12:16:22 | Home |
| 12:16:24 | Navigation type select (choose path) |
| 12:16:26 | **Follow path** (urban-2-path.gpx) – **Visual** |
| 12:21:59 | Navigation type select (choose path) |
| 12:22:03 | Home |
| 12:23:53 | GPS Logs list screen |
| 12:27:40 | Home |
| 12:27:57 | GPS Logs list screen |
| 12:28:36 | Home |
| 12:36:34 | Navigation type select (choose path) |
| 12:36:35 | **Follow path** (winola.gpx) – **Haptic** |
| 12:37:09 | Navigation type select (choose path) |
| 12:37:10 | Home |
| 12:42:58 | Home |
| 12:43:07 | Navigation type select (choose path) |
| 12:43:08 | **Follow path** (urban-2-path.gpx) – **Haptic** |

**Urban summary:** 1 Visual run (urban-2-path), 2 Haptic runs (winola.gpx, then urban-2-path.gpx).

---

## Session 2: P1-Non-Urban (Haptic + Visual DBs)

**Approx. 13:27 – 13:55 (~29 min for Visual DB; Haptic DB ~17 min)**

| Time (UTC) | Activity |
|------------|----------|
| 13:27:09 | Home |
| 13:30:06 | Home |
| 13:32:01 | Home |
| 13:32:07 | Navigation type select (choose path) |
| 13:32:08 | **Follow path** (pyn-2-path.gpx) – **Haptic** |
| 13:34:16 | Navigation type select (choose path) |
| 13:34:19 | Home |
| 13:34:39 | Navigation type select (choose path) |
| 13:34:42 | **Follow path** (pyn-2-path.gpx) – **Haptic** |
| 13:44:27 | Navigation type select (choose path) |
| 13:44:29 | Home *(Visual DB only)* |
| 13:46:05 | GPS Logs list screen *(Visual DB only)* |
| 13:46:48 | Home *(Visual DB only)* |
| 13:55:47 | Home *(Visual DB only)* |
| 13:55:51 | Navigation type select (choose path) *(Visual DB only)* |
| 13:55:53 | Home *(Visual DB only)* |
| 13:55:55 | Navigation type select (choose path) *(Visual DB only)* |
| 13:55:56 | **Follow path** (pyn-2-path.gpx) – **Visual** *(Visual DB only)* |

**Non-Urban summary:** 2 Haptic runs (pyn-2-path.gpx), 1 Visual run (pyn-2-path.gpx) at the end.

---

## Summary: What P1 Did

| Order | When (UTC) | What |
|-------|-------------|------|
| 1 | **12:16–12:22** | Urban – Follow path **urban-2-path.gpx** (Visual) |
| 2 | **12:36–12:37** | Urban – Follow path **winola.gpx** (Haptic) |
| 3 | **12:43** *(one time)* | Urban – Follow path **urban-2-path.gpx** (Haptic) |
| 4 | **13:32–13:34** | Non-Urban – Follow path **pyn-2-path.gpx** (Haptic), 1st run |
| 5 | **13:34–13:44** | Non-Urban – Follow path **pyn-2-path.gpx** (Haptic), 2nd run |
| 6 | **13:55** *(one time)* | Non-Urban – Follow path **pyn-2-path.gpx** (Visual) |

- **Paths used:** urban-2-path.gpx (urban), winola.gpx (urban), pyn-2-path.gpx (non-urban).
- **Modes:** Visual and Haptic on both urban and non-urban; Urban first, then Non-Urban.
- **12:43** and **13:55** are a single timestamp each (the time P1 entered that screen); no end time in the log for that run.

---

## Data for the “one timers” (12:43 and 13:55)

| Run | Data after start? | Details |
|-----|--------------------|--------|
| **12:43** Urban – urban-2-path.gpx (Haptic) | **Yes** | **565** fused location points and **1** is-on-track event. Location data runs until ~**12:50:54** UTC (~7 min). No **raw-location** (GPS-only) after 12:43 in this DB; raw-location in the file stops at 12:36 (previous run). So this run has **fused location only**. |
| **13:55** Non-Urban – pyn-2-path.gpx (Visual) | **Yes** | **316** raw-location + **413** fused location points, **2** is-on-track events. Data from **13:55:57** to **14:02:51** UTC (~7 min). Full tracking data. |
