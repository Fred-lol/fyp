import pandas as pd
import streamlit as st


def show_table(rows, columns=None, use_container_width=True):
    if not rows:
        return None
    df = pd.DataFrame(rows)
    if columns:
        existing = [c for c in columns if c in df.columns]
        df = df[existing]
    st.dataframe(df, use_container_width=use_container_width, hide_index=True)
    return df
