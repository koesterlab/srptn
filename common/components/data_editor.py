import streamlit as st
import pandas as pd

from common.components.schemas import get_property_type, infer_schema, update_schema
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
                df = pd.read_csv(table_path, sep="\t")
            case value if value.endswith(".csv"):
                df = pd.read_csv(table_path)
            case value if value.endswith(".xlsx"):
                df = pd.read_excel(table_path)
    except FileNotFoundError:
        st.error(f"File {value} does not exist")
        # st.stop()
        return None
    return df


def data_validator(data, schema):
    pass


def validate_data_with_schema(data, schema):
    for field in schema.get("properties"):
        #print(field)
        continue
    #print(schema)
    #print(data.to_dict(orient="list"))
