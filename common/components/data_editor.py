import streamlit as st
import pandas as pd

from common.components.schemas import get_property_type, infer_schema, update_schema
from common.components.ui_components import toggle_button

#@st.experimental_dialog("Delete a column")
def add_column(data):
    with st.popover("Add column"):
        column = st.text_input("Add column", key="add_column_text")
        deleted = st.button("Add", key="add_column_button")
        if deleted and column not in data.columns and column != "":
            data[column] = ""
    return data


def custom_config(data):
    with st.popover("Custom config"):
        uploaded_file = st.file_uploader("Choose a file", type=("xlsx", "tsv", "csv"))
        replace = st.button("Confirm", key="custom_config_button")
        if replace and uploaded_file:
            data = upload_data_table(uploaded_file)
    return data


def delete_column(data):
    with st.popover("Delete column"):
        selected = st.selectbox("Select column to delete", options=data.columns, key="delete_column_select")
        deleted = st.button("Delete", key="delete_column_button")
        if deleted:
            data = data.drop(columns=selected)
    return data


def rename_column(data):
    with st.popover("Rename column"):
        selected = st.selectbox("Select column to delete", options=data.columns, key="rename_column_select")
        renamed = st.text_input("Rename column", value=selected, key="rename_column_text")
        rename = st.button("Rename", key="rename_column_button")
        if rename:
            data = data.rename(columns={selected: renamed})
    return data


def data_editor(data: pd.DataFrame):
    col1, col2, col3, col4, col5 = st.columns([0.22, 0.22, 0.24, 0.22, 0.11])
    with col1:
        data = add_column(data)
    with col2:
        data = delete_column(data)
    with col3:
        data = rename_column(data)
    with col4:
        data = custom_config(data)
    with col5:
        store = st.button("Store", key="store_data_config")
    if store:
        # TODO implement once its possible
        pass
    return st.data_editor(data, use_container_width=True, num_rows="dynamic")


def data_selector(label: str, value: str, key: str, wd):
    col1, col2 = st.columns([9, 1])
    with col1:
        input_value = st.text_input(label=label, value=value, key=key)

    if "data" + key not in st.session_state:
        st.session_state["data" + key] = get_data_table(input_value)
    if not isinstance(st.session_state["data" + key], pd.DataFrame):
        st.error(f'{value.split("/")[-1]} not found!')
        return input_value, False  # TODO Handle missing error
    # restructure to create output from schema if present

    data_schema = wd.get_json_schema(value.split("/")[-1].split(".")[0])
    if data_schema:
        final_schema = update_schema(data_schema, st.session_state["data" + key])
    else:
        final_schema = infer_schema(st.session_state["data" + key])
    if data_schema:
        validate_data_with_schema(st.session_state["data" + key], final_schema)

    with col2:
        show_data = toggle_button("Edit", key)
    return input_value, show_data


def get_data_table(value):
    table_path = f"{st.session_state['dir_path']}/{value}"
    try:
        match value:
            case value if value.endswith(".tsv"):
                data = pd.read_csv(table_path, sep="\t")
            case value if value.endswith(".csv"):
                data = pd.read_csv(table_path)
            case value if value.endswith(".xlsx"):
                data = pd.read_excel(table_path)
    except FileNotFoundError:
        st.error(f"File {value} does not exist")
        # st.stop()
        return None
    return data


def data_validator(data, schema):
    pass


def upload_data_table(uploaded_file):
    match uploaded_file:
        case uploaded_file if uploaded_file.type == "text/tab-separated-values":
            data = pd.read_csv(uploaded_file, sep="\t")
        case uploaded_file if uploaded_file.type == "text/csv":
            data = pd.read_csv(uploaded_file)
        case uploaded_file if uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            data = pd.read_excel(uploaded_file)
    return data


def validate_data_with_schema(data, schema):
    for field in schema.get("properties"):
        #print(field)
        continue
    #print(schema)
    #print(data.to_dict(orient="list"))
