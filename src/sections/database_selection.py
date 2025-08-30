import os
import streamlit as st


def select_database() -> str:
    st.subheader("Database with logs")
    st.write("This is the database exported from the application")
    db_path = "temp/db.db"
    if not os.path.exists("temp"):
        os.makedirs("temp")

    file = select_file("Select database file", db_path, type="db")

    if not file:
        st.stop()

    return db_path

def select_file(label: str, temp_file_name: str = "", type=""):
    uploaded_file = st.file_uploader(label=label, type=type)
    if temp_file_name:
        if uploaded_file:
            with open(temp_file_name, "wb") as f:
                f.write(uploaded_file.getbuffer())
    return uploaded_file