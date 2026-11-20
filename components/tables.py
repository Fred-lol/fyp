import pandas as pd
import streamlit as st


def _dark_text_only(data, preference=None):
    """Set only dataframe text colors for AquaLoad's explicit Dark mode.

    Light and System leave Streamlit's original table renderer/theme intact.
    No cell backgrounds, dimensions, borders, or typography are changed.
    """
    preference = preference or st.session_state.get("theme_preference", "System")
    if (preference or "System").strip().lower() != "dark":
        return data

    frame = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    styler = frame.style
    if len(frame.columns):
        # The Streamlit grid itself keeps its original light canvas in every
        # portal appearance. Keep its text at the native dark ink colour so
        # Dark portal mode does not turn cells white-on-white.
        styler = styler.set_properties(subset=list(frame.columns), color="#173b58")
    return styler.set_table_styles(
        [{"selector": "th", "props": [("color", "#173b58")]},
         {"selector": "td", "props": [("color", "#173b58")]}],
        overwrite=False,
    )


def render_dataframe(data, *, preference=None, **kwargs):
    """Use the native Streamlit dataframe, adjusting only Dark text contrast."""
    return st.dataframe(_dark_text_only(data, preference), **kwargs)


def render_data_editor(data, *, preference=None, **kwargs):
    """Use the native Streamlit editor, adjusting text on disabled cells only."""
    return st.data_editor(_dark_text_only(data, preference), **kwargs)


def show_table(rows, columns=None, use_container_width=True):
    if not rows:
        return None
    df = pd.DataFrame(rows)
    if columns:
        existing = [c for c in columns if c in df.columns]
        df = df[existing]
    render_dataframe(df, use_container_width=use_container_width, hide_index=True)
    return df
