"""
Scan Participants-data-pathFinder folder and resolve participant + type to db path.
"""
import os
import re

# Base path relative to project root (where streamlit is typically run from)
PARTICIPANTS_BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "Participants-data-pathFinder",
    "Participants-data-pathFinder",
)


def _parse_type_folder(folder_name: str) -> tuple[str, str] | None:
    """
    Parse folder name like 'P1-Urban-Visual' or 'P2-Non-urban-haptic' into (environment, mode).
    Returns ('Urban'|'Non Urban', 'Visual'|'Haptic') or None if not recognized.
    """
    lower = folder_name.lower()
    if "non" in lower and "urban" in lower:
        env = "Non Urban"
    elif "urban" in lower:
        env = "Urban"
    else:
        return None
    if "haptic" in lower:
        mode = "Haptic"
    elif "visual" in lower:
        mode = "Visual"
    else:
        return None
    return (env, mode)


def _type_display(env: str, mode: str) -> str:
    """Display label for dropdown, e.g. 'Urban - Visual'."""
    return f"{env} - {mode}"


def get_participants_data():
    """
    Scan PARTICIPANTS_BASE and return structure for dropdowns.

    Returns:
        list[dict]: Each item has 'participant' (e.g. 'P1'), 'env' ('Urban'|'Non Urban'),
                    'mode' ('Visual'|'Haptic'), 'display' (e.g. 'Urban - Visual'), 'db_path' (absolute path to .db).
        Empty list if base path does not exist or has no valid data.
    """
    if not os.path.isdir(PARTICIPANTS_BASE):
        return []

    entries = []
    for p_dir in sorted(os.listdir(PARTICIPANTS_BASE)):
        p_path = os.path.join(PARTICIPANTS_BASE, p_dir)
        if not os.path.isdir(p_path) or not re.match(r"^P\d+$", p_dir, re.IGNORECASE):
            continue
        participant = p_dir  # e.g. P1, P2

        for type_dir in os.listdir(p_path):
            type_path = os.path.join(p_path, type_dir)
            if not os.path.isdir(type_path):
                continue
            parsed = _parse_type_folder(type_dir)
            if not parsed:
                continue
            env, mode = parsed
            # Find first .db file in this folder (skip names containing 'Wrong')
            db_path = None
            for f in sorted(os.listdir(type_path)):
                if f.lower().endswith(".db") and "wrong" not in f.lower():
                    db_path = os.path.join(type_path, f)
                    break
            if db_path and os.path.isfile(db_path):
                entries.append({
                    "participant": participant,
                    "env": env,
                    "mode": mode,
                    "display": _type_display(env, mode),
                    "db_path": db_path,
                })
    return entries


def get_participants_list(entries: list[dict]) -> list[str]:
    """Unique sorted participant ids from entries (P1, P2, ..., P14)."""
    ids = set(e["participant"] for e in entries)
    return sorted(ids, key=lambda x: int(re.search(r"\d+", x).group()) if re.search(r"\d+", x) else 0)


def get_types_for_participant(entries: list[dict], participant: str) -> list[dict]:
    """Entries for one participant (for type dropdown)."""
    return [e for e in entries if e["participant"] == participant]
