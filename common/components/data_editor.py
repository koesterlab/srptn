import streamlit as st
from streamlit_ace import st_ace
import pandas as pd
import polars as pl

from common.components.schemas import infer_schema, update_schema
from common.components.ui_components import toggle_button


def add_column(data: pd.DataFrame):
    """
    Add a new column to the dataframe.

    Parameters
    ----------
    data : pandas.DataFrame
        The dataframe to which the column will be added.

    Returns
    -------
    pandas.DataFrame
        The dataframe with the new column added.

    Notes
    -----
    This function uses a Streamlit popover to input the column name and add it to the dataframe.
    """
    with st.popover("Add column"):
        column = st.text_input("Add column", key="add_column_text")
        deleted = st.button("Add", key="add_column_button")
        if deleted and column not in data.columns and column != "":
            data[column] = ""
    return data


def custom_upload(data: pd.DataFrame):
    """
    Upload a custom configuration file and replace the dataframe.

    Parameters
    ----------
    data : pandas.DataFrame
        The dataframe to be replaced with the uploaded file.

    Returns
    -------
    pandas.DataFrame
        The dataframe loaded from the uploaded file.

    Notes
    -----
    This function uses a Streamlit popover to upload a file and replace the dataframe.
    """
    with st.popover("Upload"):
        uploaded_file = st.file_uploader("Choose a file", type=("xlsx", "tsv", "csv"))
        replace = st.button("Confirm", key="custom_upload_button")
        if replace and uploaded_file:
            data = upload_data_table(uploaded_file)
    return data


def delete_column(data: pd.DataFrame):
    """
    Delete a column from the dataframe.

    Parameters
    ----------
    data : pandas.DataFrame
        The dataframe from which the column will be deleted.

    Returns
    -------
    pandas.DataFrame
        The dataframe with the specified column deleted.

    Notes
    -----
    This function uses a Streamlit popover to select and delete a column from the dataframe.
    """
    with st.popover("Delete column"):
        selected = st.selectbox(
            "Select column to delete", options=data.columns, key="delete_column_select"
        )
        deleted = st.button("Delete", key="delete_column_button")
        if deleted:
            data = data.drop(columns=selected)
    return data


def rename_column(data: pd.DataFrame):
    """
    Rename a column in the dataframe.

    Parameters
    ----------
    data : pandas.DataFrame
        The dataframe containing the column to be renamed.

    Returns
    -------
    pandas.DataFrame
        The dataframe with the renamed column.

    Notes
    -----
    This function uses a Streamlit popover to rename a column in the dataframe.
    """
    with st.popover("Rename column"):
        selected = st.selectbox(
            "Select column to delete", options=data.columns, key="rename_column_select"
        )
        renamed = st.text_input(
            "Rename column", value=selected, key="rename_column_text"
        )
        rename = st.button("Rename", key="rename_column_button")
        if rename:
            data = data.rename(columns={selected: renamed})
    return data


def execute_custom_code(data, user_code: str, dataframe_type: str):
    """
    Execute custom code provided by the user on the dataframe.

    Parameters
    ----------
    data
        The dataframe on which the custom code will be executed.
    user_code : str
        The custom code to execute on the dataframe.
    dataframe_type : str
        The type of dataframe accessible on the frontend.

    Returns
    -------
    pandas.DataFrame
        The dataframe after the custom code has been executed.

    Notes
    -----
    This function uses Python's `exec` to run the custom code in a local scope.
    The dataframes can either be in Pandas or Polars.
    """
    local_vars = {"df": data}
    for key, value in st.session_state.items():
        if (
            key.startswith("workflow_config-")
            and key.endswith("-data")
            and isinstance(value, pd.DataFrame)
        ):
            if dataframe_type == "Polars": # TODO cleaner approach to this
                if not isinstance(data, pl.DataFrame):
                    data = pl.from_pandas(data)
                value = pl.from_pandas(value)
                if value.to_dict(as_series=False) == data.to_dict(as_series=False):
                    local_vars[key.split("-")[1]] = value
            if dataframe_type == "Pandas":
                if value.to_string() != data.to_string():
                    local_vars[key.split("-")[1]] = value
    exec(user_code, {}, local_vars)  # Sandboxing Polars?
    data = local_vars.get("df", data)
    if dataframe_type == "Polars":
        if not isinstance(data, pd.DataFrame):
            data = data.to_pandas()
    return data


def process_user_code(data: pd.DataFrame):
    """
    Modify the dataframe using user-provided Python code.

    Parameters
    ----------
    data : pandas.DataFrame
        The dataframe to be modified by the user's custom code.

    Returns
    -------
    pandas.DataFrame
        The dataframe after applying the user's custom modifications.

    Notes
    -----
    This function allows users to input and execute custom Python code to modify the dataframe.
    It provides a preview and an apply option for the modifications.
    """
    with st.expander("Advanced table modification"):
        dataframe_type = st.radio(
            "Dataframe type", options=["Pandas", "Polars"], horizontal=True
        )

        acestring = "# Simply modify the df, e.g. df['lorem'] = 'ipsum'\n# Other tables are accessbile through their file name\n"
        if dataframe_type == "Polars":
            acestring = "# The table is available as df: pl.DataFrame\n" + acestring
        else:
            acestring = "# The table is available as df: pd.DataFrame\n" + acestring
        user_code = st_ace(
            acestring,
            auto_update=True,
            language="python",
        )
        no_import = True
        if "import " in user_code:
            for line in user_code:
                if not line.strip().startswith("import "):
                    no_import = False
                    st.error("Remove line with 'import' as no imports are allowed.")
                    break

        col1, col2 = st.columns([0.14, 0.86], gap="small")
        with col1:
            preview = st.button(
                "Preview",
                key="advance_manipulation_preview_config",
                disabled=not no_import,
            )
        with col2:
            apply = st.button(
                "Apply", key="advance_manipulation_apply_config", disabled=not no_import
            )
        if preview:
            preview_data = data.copy()
            preview_data = execute_custom_code(preview_data, user_code, dataframe_type)
            st.data_editor(
                preview_data,
                use_container_width=True,
                disabled=True,
                num_rows="fixed",
                key="advance_manipulation_preview_window",
            )
    if apply:
        data = execute_custom_code(data, user_code, dataframe_type)
    return data


def data_editor(data: pd.DataFrame):
    """
    Provide an interface for editing a dataframe with various options.

    Parameters
    ----------
    data : pandas.DataFrame
        The dataframe to be edited.

    Returns
    -------
    pandas.DataFrame
        The dataframe after applying the edits.

    Notes
    -----
    This function provides a Streamlit interface for adding, deleting, renaming columns,
    applying custom configurations, and executing user-provided Python code to modify the dataframe.
    """
    col1, col2, col3, col4, col5 = st.columns([0.20, 0.22, 0.24, 0.22, 0.11])
    with col1:
        data = add_column(data)
    with col2:
        data = delete_column(data)
    with col3:
        data = rename_column(data)
    with col4:
        data = custom_upload(data)
    # with col5:
    #    store = st.button("Store", key="store_data_config")
    # if store:
    # TODO implement once its possible
    #    pass
    data = process_user_code(data)
    input = st.data_editor(data, use_container_width=True, num_rows="dynamic")
    return input


def data_selector(label: str, value: str, key: str, wd):
    col1, col2 = st.columns([9, 1])
    with col1:
        input_value = st.text_input(label=label, value=value, key=key)
    data_key = "workflow_config-" + key + "-data"
    if data_key not in st.session_state:
        st.session_state[data_key] = get_data_table(input_value)
    if not isinstance(st.session_state[data_key], pd.DataFrame):
        st.error(f'{value.split("/")[-1]} not found!')
        return input_value, False
    # restructure to create output from schema if present

    data_schema = wd.get_json_schema(value.split("/")[-1].split(".")[0])
    if data_schema:
        final_schema = update_schema(data_schema, st.session_state[data_key])
    else:
        final_schema = infer_schema(st.session_state[data_key])
    # if final_schema:
    #    validate_data(st.session_state[data_key], final_schema) #.to_dict(orient="list")

    with col2:
        show_data = toggle_button("Edit", "workflow_config-" + key)
    return input_value, show_data


st.cache_data()


def get_data_table(file_name: str):
    """
    Load a data table from a file based on its extension.

    Parameters
    ----------
    file_name : str
        The name of the file to be loaded.

    Returns
    -------
    pandas.DataFrame or None
        The loaded data table as a pandas DataFrame, or None if the file is not found.

    Notes
    -----
    This function reads a file from the directory specified in the Streamlit session state and loads it into a
    pandas DataFrame. The function supports `.tsv`, `.csv`, and `.xlsx` file formats.
    """
    table_path = f"{st.session_state['workflow_config-dir_path']}/{file_name}"
    try:
        match file_name:
            case file_name if file_name.endswith(".tsv"):
                data = pd.read_csv(table_path, sep="\t")
            case file_name if file_name.endswith(".csv"):
                data = pd.read_csv(table_path)
            case file_name if file_name.endswith(".xlsx"):
                data = pd.read_excel(table_path)
    except FileNotFoundError:
        st.error(f"File {file_name} does not exist")
        return None
    return data


def upload_data_table(uploaded_file):
    """
    Load a data table from an uploaded file based on its MIME type.

    Parameters
    ----------
    uploaded_file : UploadedFile
        The file uploaded by the user via Streamlit's file uploader.

    Returns
    -------
    pandas.DataFrame
        The loaded data table as a pandas DataFrame.

    Notes
    -----
    This function reads an uploaded file and loads it into a pandas DataFrame.
    The function supports text/tab-separated-values (`.tsv`), text/csv (`.csv`),
    and Excel (`.xlsx`) file formats.
    """
    match uploaded_file:
        case uploaded_file if uploaded_file.type == "text/tab-separated-values":
            data = pd.read_csv(uploaded_file, sep="\t")
        case uploaded_file if uploaded_file.type == "text/csv":
            data = pd.read_csv(uploaded_file)
        case (
            uploaded_file
        ) if uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            data = pd.read_excel(uploaded_file)
    return data


def validate_data(data, schema):
    for field in schema.get("properties"):
        if field in schema.get("required"):
            for value in data[field]:
                if not value:
                    st.error(f"{field} is filled incorrectly")
