import pandas as pd
import polars as pl
import streamlit as st
from streamlit_ace import st_ace, THEMES

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
    """
    with st.popover("Add"):
        column = st.text_input("Add column", key=f"{key}-add_column_text")
        added = st.button("Add", key=f"{key}-add_column_button")
        if added and column.strip() and column not in data.columns:
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
    """
    with st.popover("Upload"):
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=("xlsx", "tsv", "csv"),
            key=f"{key}-custom_upload_field",
        )
        replace = st.button("Confirm", key=f"{key}-custom_upload_button")
        if replace and uploaded_file:
            data = upload_data_table(uploaded_file)
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

    Notes
    -----
    This function provides a Streamlit interface for adding, deleting, renaming columns, applying custom configurations, and executing user-provided Python code to modify the dataframe.
    """
    col1, col2, col3, col4, col5 = st.session_state[key + "-placeholders"][0].columns(5)
    with col1:
        data = add_column(data, key)
    with col2:
        data = rename_column(data, key)
    with col3:
        data = delete_column(data, key)
    with col4:
        data = custom_upload(data, key)
    with col5:
        data = data_fill(data, key)
    # with col5:
    #     schema_key = key + "-schema"
    #     st.session_state[schema_key] = modify_schema(
    #         st.session_state[schema_key], schema_key
    #     )
    data = process_user_code(data, key)
    data = st.session_state[key + "-placeholders"][2].data_editor(
        data,
        use_container_width=True,
        num_rows="dynamic",
        on_change=update_data,
        args=(key,),
        key=key + "-editor",
    )
    st.session_state[key + "-data"] = data
    validate_data(key, data)


def data_fill(data: pd.DataFrame, key: str) -> pd.DataFrame:
    """
    Fill the configuration file with data from the selected dataset.

    Parameters
    ----------
    data : pandas.DataFrame
        The dataframe to be replaced with the uploaded file.
    key : str
        The key for the Streamlit session state.

    Returns
    -------
    pandas.DataFrame
        The dataframe with specified column added
    """
    with st.popover("Fill"):
        selected = None
        if "workflow-meta-datasets-sheets" in st.session_state.keys():
            dataset = st.session_state.get("workflow-meta-datasets-sheets")
            selected = st.selectbox(
                "Select a dataset",
                options=[names for names in dataset.keys()],
                key=f"{key}-fill_data_select",
            )
        if selected:
            data_selected = dataset[selected]
            col1, col2 = st.columns(2)
            with col1:
                column = st.selectbox(
                    "From",
                    options=data_selected.columns,
                    key=f"{key}-fill_column_select",
                )
            with col2:
                column_alias = st.text_input(
                    "To", column, key=f"{key}-fill_column_alias"
                )

            data_modified = data.copy()

            if column_alias in data_modified.columns:
                data_as_list = data_modified[column_alias].tolist()
                data_as_list.extend(data_selected[column].tolist())
                data_modified = data_modified.reindex(range(len(data_as_list)))
                data_modified[column_alias] = data_as_list
            else:
                if len(data_selected) > len(data_modified):
                    data_modified = data_modified.reindex(range(len(data_selected)))
                data_modified[column_alias] = data_selected[column]

            st.data_editor(
                data_modified,
                height=225,
                use_container_width=True,
                disabled=True,
                num_rows="fixed",
                key=f"{key}-fill_preview_window",
            )
            replace = st.button("Confirm", key=f"{key}-fill_button")
            if replace:
                data = data_modified
    return data


# Fill button
# @st.fragment
def data_selector(label: str, value: str, key: str, wd) -> tuple[str, bool]:
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
    wd : WorkflowDeployer
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
            label=label,
            value=value,
            key=key,
            disabled=True,
            label_visibility="collapsed",
        )
    data_key = key + "-data"
    data_key_changed = key + "-data_token"
    data_schema_key = key + "-schema"

    if (
        data_key not in st.session_state
        or data_key_changed not in st.session_state
        or st.session_state.get(data_key_changed) != input_value
    ):
        # In preparation for new data storing that will allow hotswap of data
        if data_schema_key in st.session_state:
            st.session_state.pop(data_schema_key)
        st.session_state[data_key] = get_data_table(input_value)
        st.session_state[data_key_changed] = input_value

    if not isinstance(st.session_state[data_key], pd.DataFrame):
        st.error(f'File {value.split("/")[-1]} not found!')
        return input_value, False

    if data_schema_key not in st.session_state:
        data_schema = wd.get_json_schema(value.split("/")[-1].split(".")[0])
        if data_schema:
            final_schema = update_schema(data_schema, st.session_state[data_key])
        else:
            final_schema = infer_schema(st.session_state[data_key])
        st.session_state[data_schema_key] = final_schema

    with col2:
        show_data = toggle_button("Edit", key)
    return input_value, show_data


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
    """
    with st.popover("Remove"):
        selected = st.selectbox(
            "Select column to delete",
            options=data.columns,
            key=f"{key}-delete_column_select",
        )
        deleted = st.button("Delete", key=f"{key}-delete_column_button")
        if deleted:
            data = data.drop(columns=selected)
    return data


def execute_custom_code(
    data: pd.DataFrame, user_code: str, dataframe_type: str
) -> pd.DataFrame:
    """
    Execute custom code provided by the user on the dataframe.

    Parameters
    ----------
    data : pd.DataFrame
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
    local_vars = {}
    for key, value in [
        (key, value)
        for key, value in st.session_state.items()
        if (
            key.startswith("workflow-config-")
            and key.endswith("-data")
            and isinstance(value, pd.DataFrame)
            and value.to_string() != data.to_string()
        )
    ]:
        local_var_key = key.split("-")[2].split(".")[-1]
        if dataframe_type == "Polars":
            local_vars[local_var_key] = pl.from_pandas(value)
        if dataframe_type == "Pandas":
            local_vars[local_var_key] = value
    if dataframe_type == "Polars":
        data = pl.from_pandas(data)
    local_vars["df"] = data
    exec(user_code, {}, local_vars)
    data = local_vars.get("df", data)
    if not isinstance(data, pd.DataFrame):
        data = data.to_pandas()
    return data


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
    table_path = st.session_state["workflow-config-dir_path"] / file_name
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
        "Advanced table modification", expanded=True
    ):
        dataframe_type = st.radio(
            "Dataframe type",
            options=["Pandas", "Polars"],
            horizontal=True,
            key=f"{key}-dataframetype",
        )

        if dataframe_type == "Polars":
            acestring = "# The table is available as df: pl.DataFrame\n"
        else:
            acestring = "# The table is available as df: pd.DataFrame\n"
        acestring = (
            acestring + "# All other tables are accessbile through their file name\n"
        )
        c1, c2 = st.columns([3.25, 1])
        with c1:
            user_code = st_ace(
                acestring,
                auto_update=False,
                language="python",
                height=300,
                theme=c2.selectbox("Theme", options=THEMES, index=35),
                font_size=c2.slider("Font size", 5, 24, 14),
            )
        no_import = True
        if "import " in user_code:
            for line in user_code:
                if not line.strip().startswith("import"):
                    no_import = False
                    st.error("Remove line with 'import' as no imports are allowed.")
                    break
        preview = c2.button(
            "Preview Changes",
            key=f"{key}-advanced_manipulation_preview_config",
            disabled=not no_import,
        )
        apply = c2.button(
            "Apply Changes",
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
    """
    with st.popover("Rename"):
        selected = st.selectbox(
            "Select column to rename",
            options=data.columns,
            key=f"{key}-rename_column_select",
        )
        renamed = st.text_input(
            "Rename to", value=selected, key=f"{key}-rename_column_text"
        )
        rename = st.button("Rename", key=f"{key}-rename_column_button")
        if rename and renamed.strip():
            data = data.rename(columns={selected: renamed})
    return data


def modify_schema(schema: dict, key: str) -> dict:
    """
    Rename a column in the dataframe schema.

    Parameters
    ----------
    schema : dict
        The data schema.
    key : str
        The key for the Streamlit session state.

    Returns
    -------
    dict
        The data schema with the renamed column.
    """
    with st.popover("Modify"):
        selected = st.selectbox(
            "Select column-schema to rename",
            options=schema["properties"].keys(),
            key=f"{key}-modify_column_select",
        )
        renamed = st.text_input(
            "Rename to", value=selected, key=f"{key}-modify_column_text"
        )
        rename = st.button("Rename", key=f"{key}-modify_column_button")
        if rename and renamed.strip():
            schema["properties"][renamed] = schema["properties"].pop(selected)
            if selected in schema["required"]:
                schema["required"] = list(
                    map(
                        lambda x: x.replace(selected, renamed),
                        schema["required"],
                    )
                )
    return schema


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


def validate_data(key: str, data=None):
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
    st.session_state["workflow-config-form-valid"][key] = True
    if not isinstance(data, pd.DataFrame):
        data = st.session_state[key + "-data"]
    data = data.to_dict(orient="list")
    schema = st.session_state[key + "-schema"]
    for field in schema.get("properties"):
        required = schema.get("required")
        column = data.get(field)
        if required and field in required and not column:
            st.session_state["workflow-config-form-valid"][key] = False
            st.error(f'Column "{field}" is required but not found.')
        elif column:
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
                        # no isinstance as the value might be an int or float as string
                        if not str(value).strip() or not value:
                            valid = False
                    case typing if typing == "number":
                        if not isinstance(value, (int, float)):
                            valid = False
                if not valid:
                    rows.append(str(idx + 1))
            if rows:
                st.session_state["workflow-config-form-valid"][key] = False
                rowstring = "s " + ", ".join(rows) if len(rows) > 1 else " " + rows[0]
                st.error(
                    f'Column "{field}" expects a "{schema["properties"][field]["type"]}" on row{rowstring}.'
                )
