import streamlit as st


def confirm_checkbox(label="I understand and want to continue"):
    return st.checkbox(label)
