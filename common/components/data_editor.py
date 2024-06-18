import pandas as pd
import polars as pl
import streamlit as st
from streamlit_ace import st_ace

from common.components.schemas import infer_schema, update_schema
from common.components.ui_components import toggle_button


def add_column(data: pd.DataFrame, key: str) -> pd.DataFrame:
    """
    Add a new column to the dataframe.

    Parameters
    ----------
    data : pandas.DataFrame
        The dataframe to which the column will be added.
    key : str
        The key for the Streamlit session state.

    Returns
    -------
    pandas.DataFrame
        The dataframe with the new column added.

    Notes
    -----
    This function uses a Streamlit popover to input the column name and add it to the dataframe.
    """
    with st.popover("Add column"):
        column = st.text_input("Add column", key=f"{key}-add_column_text")
        deleted = st.button("Add", key=f"{key}-add_column_button")
        if deleted and column not in data.columns and column.strip():
            data[column] = ""
    return data


def custom_upload(data: pd.DataFrame, key: str) -> pd.DataFrame:
    """
    Upload a custom configuration file and replace the dataframe.

    Parameters
    ----------
    data : pandas.DataFrame
        The dataframe to be replaced with the uploaded file.
    key : str
        The key for the Streamlit session state.

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
        replace = st.button("Confirm", key=f"{key}-custom_upload_button")
        if replace and uploaded_file:
            data = upload_data_table(uploaded_file)
    return data


def delete_column(data: pd.DataFrame, key: str) -> pd.DataFrame:
    """
    Delete a column from the dataframe.

    Parameters
    ----------
    data : pandas.DataFrame
        The dataframe from which the column will be deleted.
    key : str
        The key for the Streamlit session state.

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
            "Select column to delete",
            options=data.columns,
            key=f"{key}-delete_column_select",
        )
        deleted = st.button("Delete", key=f"{key}-delete_column_button")
        if deleted:
            data = data.drop(columns=selected)
    return data


def rename_column(data: pd.DataFrame, key: str) -> pd.DataFrame:
    """
    Rename a column in the dataframe.

    Parameters
    ----------
    data : pandas.DataFrame
        The dataframe containing the column to be renamed.
    key : str
        The key for the Streamlit session state.

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
            "Select column to delete",
            options=data.columns,
            key=f"{key}-rename_column_select",
        )
        renamed = st.text_input(
            "Rename column", value=selected, key=f"{key}-rename_column_text"
        )
        rename = st.button("Rename", key="rename_column_button")
        if rename and renamed.strip():
            data = data.rename(columns={selected: renamed})
    return data


def execute_custom_code(data, user_code: str, dataframe_type: str) -> pd.DataFrame:
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
            if dataframe_type == "Polars":
                if not isinstance(data, pl.DataFrame):
                    data = pl.from_pandas(data)
                value = pl.from_pandas(value)
                if value.to_dict(as_series=False) != data.to_dict(as_series=False):
                    local_vars[key.split("-")[1]] = value
            if dataframe_type == "Pandas":
                if value.to_string() != data.to_string():
                    local_vars[key.split("-")[1]] = value
    exec(user_code, {}, local_vars)
    data = local_vars.get("df", data)
    if dataframe_type == "Polars":
        if not isinstance(data, pd.DataFrame):
            data = data.to_pandas()
    return data


def process_user_code(data: pd.DataFrame, key: str) -> pd.DataFrame:
    """
    Modify the dataframe using user-provided Python code.

    Parameters
    ----------
    data : pandas.DataFrame
        The dataframe to be modified by the user's custom code.
    key : str
        The key for the Streamlit session state.

    Returns
    -------
    pandas.DataFrame
        The dataframe after applying the user's custom modifications.

    Notes
    -----
    This function allows users to input and execute custom Python code to modify the dataframe.
    It provides a preview and an apply option for the modifications.
    """
    with st.session_state[key + "-placeholders"][1].expander(
        "Advanced table modification"
    ):
        dataframe_type = st.radio(
            "Dataframe type", options=["Pandas", "Polars"], horizontal=True
        )

        acestring = "# All other tables are accessbile through their file name\n"
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
                if not line.strip().startswith("import"):
                    no_import = False
                    st.error("Remove line with 'import' as no imports are allowed.")
                    break

        col1, col2 = st.columns([0.14, 0.86], gap="small")
        with col1:
            preview = st.button(
                "Preview",
                key=f"{key}-advanced_manipulation_preview_config",
                disabled=not no_import,
            )
        with col2:
            apply = st.button(
                "Apply",
                key=f"{key}-advanced_manipulation_apply_config",
                disabled=not no_import,
            )
        if preview:
            preview_data = data.copy()
            preview_data = execute_custom_code(preview_data, user_code, dataframe_type)
            st.data_editor(
                preview_data,
                use_container_width=True,
                disabled=True,
                num_rows="fixed",
                key=f"{key}-advanced_manipulation_preview_window",
            )
            validate_data(key, preview_data)
    if apply:
        data = execute_custom_code(data, user_code, dataframe_type)
    return data


def data_editor(data: pd.DataFrame, key: str):
    """
    Provide an interface for editing a dataframe with various options.

    Parameters
    ----------
    data : pandas.DataFrame
        The dataframe to be edited.
    key : str
        The key for the Streamlit session state.

    Returns
    -------
    pandas.DataFrame
        The dataframe after applying the edits.

    Notes
    -----
    This function provides a Streamlit interface for adding, deleting, renaming columns,
    applying custom configurations, and executing user-provided Python code to modify the dataframe.
    """
    col1, col2, col3, col4 = st.session_state[key + "-placeholders"][0].columns(4)
    with col1:
        data = add_column(data, key)
    with col2:
        data = delete_column(data, key)
    with col3:
        data = rename_column(data, key)
    with col4:
        data = custom_upload(data, key)
    data = process_user_code(data, key)
    input = st.data_editor(
        data,
        use_container_width=True,
        num_rows="dynamic",
        on_change=update_data,
        args=(key,),
        key=key + "-editor",
    )
    st.session_state[key + "-data"] = data
    validate_data(key, data)
    return input


def data_selector(label: str, value: str, key: str, wd):
    """
    Create a data selector widget in Streamlit.

    Parameters
    ----------
    label : str
        The label for the text input widget.
    value : str
        The initial value of the text input.
    key : str
        The key to store the text input value in Streamlit's session state.
    wd : object
        The workflow deployer object to get the JSON schema.

    Returns
    -------
    tuple
        The input value and a boolean indicating whether to show the data editor.
    """
    st.text(label)
    col1, col2 = st.columns([9, 1])
    with col1:
        input_value = st.text_input(
            label=label, value=value, key=key, label_visibility="collapsed"
        )
    data_key = key + "-data"
    if data_key not in st.session_state:
        st.session_state[data_key] = get_data_table(input_value)
    if not isinstance(st.session_state[data_key], pd.DataFrame):
        st.error(f'{value.split("/")[-1]} not found!')
        return input_value, False
    schema_key = key + "-schema"
    if schema_key not in st.session_state:
        data_schema = wd.get_json_schema(value.split("/")[-1].split(".")[0])
        if data_schema:
            final_schema = update_schema(data_schema, st.session_state[data_key])
        else:
            final_schema = infer_schema(st.session_state[data_key])
        st.session_state[schema_key] = final_schema

    with col2:
        show_data = toggle_button("Edit", key)
    return input_value, show_data


def get_data_table(file_name: str) -> pd.DataFrame:
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


def upload_data_table(uploaded_file) -> pd.DataFrame:
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


def update_data(key):
    """
    Update the data in the session state based on user edits.

    Parameters
    ----------
    key : str
        The key for the Streamlit session state of the data.
    """
    editor = st.session_state[key + "-editor"]["edited_rows"]
    data = st.session_state[key + "-data"]
    coldictkey = list(editor.keys())[0]
    colname = list(editor[coldictkey].keys())[0]
    data.loc[coldictkey, colname] = editor[coldictkey][colname]
    st.session_state[key + "-data"] = data


def validate_data(key, data=None):
    """
    Validate data against a schema.

    Parameters
    ----------
    key : str
        The key for the Streamlit session state.
    data : pd.DataFrame, optional
        The data to be validated. If not provided, it will be fetched from the session state.

    Notes
    -----
    This function checks if the data conforms to the required schema and highlights errors.
    """
    st.session_state["workflow_config-form-valid"][key] = True
    if not isinstance(data, pd.DataFrame):
        data = st.session_state[key + "-data"]
    data = data.to_dict(orient="list")
    schema = st.session_state[key + "-schema"]
    for field in schema.get("properties"):
        required = schema.get("required")
        column = data.get(field)
        if required and field in required and not column:
            st.error(f'Column "{field}" is required but not found.')
        if column:
            rows = []
            for idx, value in enumerate(column):
                valid = True
                match schema["properties"][field]["type"]:
                    case typing if typing == "boolean":
                        if not any(
                            value == bools for bools in ("True", "False", "0", "1")
                        ):
                            valid = False
                    case typing if typing == "string":
                        # No isinstance as the value might be an int or float as string
                        if not str(value).strip() or not value:
                            valid = False
                    case typing if typing == "number":
                        if not isinstance(value, (int, float)):
                            valid = False
                if not valid:
                    rows.append(str(idx + 1))
            if rows:
                st.session_state["workflow_config-form-valid"][key] = False
                rowstring = "s " + ", ".join(rows) if len(rows) > 1 else " " + rows[0]
                st.error(
                    f'Column "{field}" expects a "{schema["properties"][field]["type"]}" on row{rowstring}.'
                )
