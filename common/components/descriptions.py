import streamlit as st
from common.components.ui_components import persistend_text_area


def desc_editor(key):
    col1, col2 = st.columns(2)

    with col1:
        desc = persistend_text_area(
            "Description (markdown format)", f"{key}-description"
        )

    with col2:
        st.caption("Preview")
        st.markdown(desc)

    return desc
