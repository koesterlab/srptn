import streamlit as st


def desc_editor():
    col1, col2 = st.columns(2)

    with col1:
        desc = st.text_area("Description (markdown format)")

    with col2:
        st.caption("Preview")
        st.markdown(desc)

    return desc
