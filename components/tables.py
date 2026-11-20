import pandas as pd
import streamlit as st


def render_dataframe(data, *, preference=None, **kwargs):
    """Render the original native Streamlit grid without altering its payload."""
    return st.dataframe(data, **kwargs)


def render_data_editor(data, *, preference=None, **kwargs):
    """Render the original native editor without altering its payload."""
    return st.data_editor(data, **kwargs)


def show_table(rows, columns=None, use_container_width=True):
    if not rows:
        return None
    df = pd.DataFrame(rows)
    if columns:
        existing = [c for c in columns if c in df.columns]
        df = df[existing]
    render_dataframe(df, use_container_width=use_container_width, hide_index=True)
    return df
