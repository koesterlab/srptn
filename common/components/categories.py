import streamlit as st


def category_editor(key: str) -> list:
    """Create and manages a category editor interface using Streamlit.

    :param key: A string prefix to uniquely identify session state keys for categories.
    :returns: A list of category and subcategory inputs, excluding the placeholder for
    new entries.
    """

    def update_categories(position: int) -> None:
        st.session_state[f"{key}-categories"][position] = st.session_state[
            f"{key}-category-{position}"
        ]
        st.session_state[f"{key}-categories"] = [
            cat for cat in st.session_state[f"{key}-categories"] if cat
        ] + [""]

    if f"{key}-categories" not in st.session_state:
        st.session_state[f"{key}-categories"] = [""]

    categories = [
        st.text_input(
            "Category" if not position else "Subcategory",
            value=cat,
            key=f"{key}-category-{position}",
            on_change=update_categories,
            args=(position,),
            placeholder="Enter category/subcategory",
        )
        for position, cat in enumerate(st.session_state[f"{key}-categories"])
    ]
    return categories[:-1]
