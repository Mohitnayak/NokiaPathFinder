import os
import streamlit as st

from utils.participants_data import (
    extract_participants_zip,
    get_participants_data,
    get_participants_list,
    get_types_for_participant,
)

# Session state keys for zip-based participant data
SESSION_ENTRIES = "participants_entries_from_zip"


def select_database_section() -> str:
    """
    Left sidebar: Participant dropdown and Type (Urban/Non Urban, Haptic/Visual) dropdown.
    Loads from folder if present, else from uploaded zip, else single .db file upload.
    """
    entries = get_participants_data()

    if not entries and SESSION_ENTRIES in st.session_state:
        entries = st.session_state[SESSION_ENTRIES]

    if entries:
        participants = get_participants_list(entries)
        with st.sidebar:
            st.subheader("Participants data")
            participant = st.selectbox(
                "Participant",
                options=participants,
                key="participant_select",
            )
            type_entries = get_types_for_participant(entries, participant)
            type_options = [e["display"] for e in type_entries]
            type_display = st.selectbox(
                "Type (Urban / Non Urban — Haptic / Visual)",
                options=type_options,
                key="type_select",
            )
            chosen = next(
                (e for e in type_entries if e["display"] == type_display),
                None,
            )
            if chosen:
                db_path = chosen["db_path"]
                st.caption(f"Loaded: {participant} — {type_display}")
                return db_path

        st.sidebar.warning("No database selected.")
        st.stop()
    else:
        # No folder and no zip data: require zip first (single .db is optional alternative)
        st.sidebar.subheader("Participants data")
        st.sidebar.write(
            "Upload a **zip** of Participants-data-pathFinder (folder with P1, P2, … and .db files) to use the filters."
        )
        # Don't restrict type=zip so Cloud platforms that block application/x-zip-compressed still accept the file
        zip_file = st.sidebar.file_uploader(
            "Upload participants zip (.zip)",
            type=None,
            key="participants_zip_upload",
        )
        if zip_file:
            if not (zip_file.name and zip_file.name.lower().endswith(".zip")):
                st.sidebar.error("Please upload a .zip file.")
                st.stop()
            temp_zip = os.path.join("temp", "participants_upload.zip")
            os.makedirs("temp", exist_ok=True)
            with open(temp_zip, "wb") as f:
                f.write(zip_file.getbuffer())
            entries = extract_participants_zip(temp_zip)
            if entries:
                st.session_state[SESSION_ENTRIES] = entries
                st.sidebar.success(f"Loaded {len(entries)} participant/type combinations. Select below.")
                st.rerun()
            else:
                st.sidebar.error("Zip invalid or no P1/P2/… folders with .db files found.")
                if SESSION_ENTRIES in st.session_state:
                    del st.session_state[SESSION_ENTRIES]
                st.stop()
        else:
            if SESSION_ENTRIES in st.session_state:
                del st.session_state[SESSION_ENTRIES]
            # Single .db only as optional alternative inside expander
            with st.sidebar.expander("Or use a single database file"):
                st.caption("Upload one .db file to analyze that run only (no Participant/Type filters).")
                db_path = "temp/db.db"
                os.makedirs("temp", exist_ok=True)
                file = select_file("Select database file", db_path, type="db")
                if file:
                    return db_path
            st.sidebar.info("Upload a participants zip above to continue.")
            st.stop()


def select_file(label: str, temp_file_name: str = "", type=""):
    uploaded_file = st.sidebar.file_uploader(label=label, type=type)
    if temp_file_name:
        if uploaded_file:
            with open(temp_file_name, "wb") as f:
                f.write(uploaded_file.getbuffer())
    return uploaded_file
