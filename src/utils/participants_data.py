"""
Scan Participants-data-pathFinder folder and resolve participant + type to db path.
Supports optional base_path (e.g. from extracted zip).
"""
import os
import re
import zipfile

# Base path relative to project root (where streamlit is typically run from)
PARTICIPANTS_BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "Participants-data-pathFinder",
    "Participants-data-pathFinder",
)

PARTICIPANT_DIR_PATTERN = re.compile(r"^P\d+$", re.IGNORECASE)

# Default extract dir for zip uploads (relative to project root)
ZIP_EXTRACT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "temp",
    "participants_extracted",
)


def extract_participants_zip(zip_path: str) -> list[dict]:
    """
    Extract a zip containing Participants-data-pathFinder structure and return
    get_participants_data() entries for the extracted tree.

    Returns:
        list[dict]: Same shape as get_participants_data(); empty if zip invalid or no .db found.
    """
    if not os.path.isfile(zip_path):
        return []
    os.makedirs(ZIP_EXTRACT_DIR, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(ZIP_EXTRACT_DIR)
    except (zipfile.BadZipFile, OSError):
        return []
    base = find_participants_base(ZIP_EXTRACT_DIR)
    if base is None:
        return []
    return get_participants_data(base_path=base)


def find_participants_base(extract_dir: str) -> str | None:
    """
    Find the directory that contains participant folders (P1, P2, ...).
    Checks extract_dir and one level of subdirs (for zips with Participants-data-pathFinder/...).
    """
    if not os.path.isdir(extract_dir):
        return None
    # Check root
    try:
        names = os.listdir(extract_dir)
    except OSError:
        return None
    participant_dirs = [n for n in names if PARTICIPANT_DIR_PATTERN.match(n)]
    if participant_dirs:
        return extract_dir
    # One level down (e.g. Participants-data-pathFinder or Participants-data-pathFinder/Participants-data-pathFinder)
    for name in names:
        sub = os.path.join(extract_dir, name)
        if os.path.isdir(sub):
            try:
                sub_names = os.listdir(sub)
            except OSError:
                continue
            if any(PARTICIPANT_DIR_PATTERN.match(n) for n in sub_names):
                return sub
    return None


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


def get_participants_data(base_path: str | None = None) -> list[dict]:
    """
    Scan base_path (or PARTICIPANTS_BASE) and return structure for dropdowns.

    Args:
        base_path: Directory containing P1, P2, ... folders. If None, uses PARTICIPANTS_BASE.

    Returns:
        list[dict]: Each item has 'participant' (e.g. 'P1'), 'env' ('Urban'|'Non Urban'),
                    'mode' ('Visual'|'Haptic'), 'display' (e.g. 'Urban - Visual'), 'db_path' (absolute path to .db).
        Empty list if base path does not exist or has no valid data.
    """
    root = base_path if base_path is not None else PARTICIPANTS_BASE
    if not os.path.isdir(root):
        return []

    entries = []
    for p_dir in sorted(os.listdir(root)):
        p_path = os.path.join(root, p_dir)
        if not os.path.isdir(p_path) or not PARTICIPANT_DIR_PATTERN.match(p_dir):
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
