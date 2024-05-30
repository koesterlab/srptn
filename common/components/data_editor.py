import streamlit as st
import pandas as pd

from common.components.ui_components import toggle_button

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
    return st.data_editor(data, use_container_width=True, num_rows="dynamic")


def data_selector(label:str, value: str, key: str, wd):
    col1, col2 = st.columns([9, 1])
    with col1:
        input_value = st.text_input(label=label, value=value, key=key)
    #if "data" + key not in st.session_state:
    data_schema = wd.get_json_schema(value.split("/")[-1].split(".")[0])
    # TODO: Verify DataFrame with schema
    st.session_state["data" + key] = get_data_table(input_value)
    with col2:
        show_data = toggle_button("Edit", key)
    return input_value, show_data


def get_data_table(value):
    table_path = f"{st.session_state['dir_path']}/{value}"
    try:
        match value:
            case value if value.endswith(".tsv"):
                df = pd.read_csv(table_path, sep="\t")
            case value if value.endswith(".csv"):
                df = pd.read_csv(table_path)
            case value if value.endswith(".xlsx"):
                df = pd.read_excel(table_path)
    except FileNotFoundError:
        st.error("File does not exist")
        #st.stop()
        return None
    return df
