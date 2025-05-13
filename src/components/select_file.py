import streamlit as st


def select_file(label: str, temp_file_name: str = "", type=""):
    uploaded_file = st.file_uploader(label=label, type=type)
    if temp_file_name:
        if uploaded_file:
            with open(temp_file_name, "wb") as f:
                f.write(uploaded_file.getbuffer())
    return uploaded_file
