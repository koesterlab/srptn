import streamlit as st
import pandas as pd


def data_editor(data: pd.DataFrame):
    selected = st.selectbox("Select column", options=data.columns)
    col1, col2 = st.columns(2)
    with col1:
        renamed = st.text_input("Rename column", value=selected)
    with col2:
        deleted = st.button("Delete column")

    if renamed != selected:
        data = data.rename(columns={selected: renamed})
    if deleted:
        data = data.drop(columns=selected)

    return st.data_editor(data)
