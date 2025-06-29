import streamlit as st

from srptn.common.components.ui_components import persistent_text_area


def desc_editor(key: str) -> str:
    """
    Edit and preview a text description in Markdown format.

    :param key: A string prefix to identify session state keys for descriptions.
    :return: The text entered in the description area as a string.
    """
    col1, col2 = st.columns(2)

    with col1:
        desc = persistent_text_area(
            "Description",
            f"{key}-description",
            "Enter description",
            "Markdown Format",
        )

    with col2:
        st.caption("Preview")
        st.markdown(desc)

    return desc
