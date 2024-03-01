import streamlit as st


def category_editor():
    categories = []
    while not categories or categories[-1]:
        categories.append(st.text_input("Category" if not categories else "Subcategory", key=f"category-{len(categories)}"))

    return categories