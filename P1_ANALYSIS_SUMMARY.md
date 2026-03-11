# P1 Data Analysis – What’s Wrong

Summary of issues found in **P1** participant data under `Participants-data-pathFinder/Participants-data-pathFinder/P1/`.

---

## 1. **current-segment vs current-max-deviation mismatch**

**Affected:** `P1-Non-Urban-Haptic`, `P1-Non-Urban-Visual`

| File                      | current-segment | current-max-deviation |
|---------------------------|-----------------|------------------------|
| P1-Non-Urban-Haptic.db   | 3               | 2                      |
| P1-Non-Urban-Visual.db   | 5               | 3                      |

- The app expects **exactly one** `current-segment` and **exactly one** `current-max-deviation` in the selected screen’s time range (see `fetch_base_path_for_time_range` in `src/utils/base_path.py`).
- In **P1-Non-Urban-Haptic**, there are 3 segment logs but only 2 max-deviation logs. The **third** segment (timestamp `1760535833191`) has **no** matching max-deviation.
  - For the screen that uses that third segment, the app will raise: **“No max deviation found for this time range.”**
- Similar situation in **P1-Non-Urban-Visual** (5 segments vs 3 max-deviations): some screens will have no or multiple max-deviation in range, leading to **“No max deviation found”** or **“More than one max deviation found.”**

**Conclusion:** Logging is inconsistent: not every `current-segment` has a corresponding `current-max-deviation`, so base path cannot be resolved for some P1 screens.

---

## 2. **withHaptic = 0 not shown as “Visual” in screen dropdown**

**Affected:** All P1 (and any DB that logs Visual as `0`).

- In the logs, **Visual** sessions use `withHaptic: 0` and **Haptic** uses `1` or `2`.
- In `src/sections/screen_selection.py`, `haptic_visual_map` is:
  - `True`, `1`, `2` → `"Haptic"`
  - `False`, `None` → `"Visual"`
  - **`0` is not in the map**, so it falls back to `""`.
- So in the **screen selection dropdown**, Visual runs (withHaptic=0) show a **blank** instead of **“Visual”**.

**Conclusion:** P1 Visual sessions are mislabeled in the UI (empty label). The data is consistent; the app’s mapping is incomplete.

---

## 3. **Many navigation events excluded from screen list (by design)**

- Navigation logs include **Home** and **NavigationTypeSelectScreenType** (route has `{pathUri}` but not `{withHaptic}`). These are **intentionally** filtered out; only **FollowThePathScreenType** (both `{pathUri}` and `{withHaptic}`) appear in the dropdown.
- So “missing” screens for P1 are expected: only **Follow the path** sessions are listed. Counts:
  - P1-Non-Urban-Haptic: **2** screens
  - P1-Non-Urban-Visual: **3** screens
  - P1-Urban-haptic: **3** screens
  - P1-Urban-Visual: **1** screen

Not a data error; this is how the app is designed.

---

## 4. **Location and raw-location**

- All four P1 DBs have both `location` and `raw-location` with valid latitude/longitude in the sampled rows.
- No issues found with missing or malformed location payloads in the check.

---

## 5. **Summary table**

| Issue                                      | Where                    | Severity / effect                                      |
|-------------------------------------------|--------------------------|--------------------------------------------------------|
| Segment vs max-deviation count mismatch    | P1-Non-Urban-Haptic, P1-Non-Urban-Visual | **Error** for some screens: base path fails to load   |
| withHaptic=0 not mapped to “Visual”       | App code (screen_selection)              | **UI**: Visual runs show blank in screen dropdown     |
| Only FollowThePath screens in dropdown     | App design               | **By design**; not a P1 data bug                       |

---

## Recommended fixes (for app/data)

1. **Data / logging:** Ensure every `current-segment` log has a matching `current-max-deviation` (same or very close timestamp) so every screen has exactly one base path.
2. **App:** In `haptic_visual_map`, add `0: "Visual"` so Visual sessions (withHaptic=0) display correctly in the screen selection dropdown.
