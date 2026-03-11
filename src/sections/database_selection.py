import os
import streamlit as st

from utils.participants_data import (
    get_participants_data,
    get_participants_list,
    get_types_for_participant,
)


def select_database_section() -> str:
    """
    Left sidebar: Participant dropdown and Type (Urban/Non Urban, Haptic/Visual) dropdown.
    Loads data from Participants-data-pathFinder. Falls back to file upload if folder missing.
    """
    entries = get_participants_data()

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

        # Should not reach here if entries and type_entries are non-empty
        st.sidebar.warning("No database selected.")
        st.stop()
    else:
        # Fallback: file upload (original behavior)
        st.sidebar.subheader("Database with logs")
        st.sidebar.write(
            "Participants-data-pathFinder not found. Upload a database file."
        )
        db_path = "temp/db.db"
        if not os.path.exists("temp"):
            os.makedirs("temp")
        file = select_file("Select database file", db_path, type="db")
        if not file:
            st.stop()
        return db_path


def select_file(label: str, temp_file_name: str = "", type=""):
    uploaded_file = st.sidebar.file_uploader(label=label, type=type)
    if temp_file_name:
        if uploaded_file:
            with open(temp_file_name, "wb") as f:
                f.write(uploaded_file.getbuffer())
    return uploaded_file
