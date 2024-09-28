import polars as pl
import streamlit as st
from snakedeploy.deploy import WorkflowDeployer
from streamlit_ace import THEMES, st_ace

from common.components.schemas import infer_schema, update_schema
from common.components.ui_components import toggle_button
from common.utils.polars_utils import (
    enforce_typing,
    get_type_specific_default,
    load_data_table,
)


def add_column(data: pl.DataFrame, key: str) -> pl.DataFrame:
    """
    Add a new column to the dataframe.

    Parameters
    ----------
    data : polars.DataFrame
        The dataframe to which the column will be added.
    key : str
        The key for the Streamlit session state.

    Returns
    -------
    polars.DataFrame
        The dataframe with the new column added.
    """
    with st.popover("Add"):
        column = st.text_input("Add column", key=f"{key}-add_column_text")
        added = st.button("Add", key=f"{key}-add_column_button")
        if added and column.strip() and column not in data.columns:
            data = data.with_columns(pl.Series(column, [""] * len(data)))
    return data


def custom_upload(data: pl.DataFrame, key: str) -> pl.DataFrame:
    """
    Upload a custom configuration file and replace the dataframe.

    Parameters
    ----------
    data : polars.DataFrame
        The dataframe to be replaced with the uploaded file.
    key : str
        The key for the Streamlit session state.

    Returns
    -------
    polars.DataFrame
        The dataframe loaded from the uploaded file.
    """
    with st.popover("Upload"):
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=("xlsx", "tsv", "csv"),
            key=f"{key}-custom_upload_field",
        )
        upload = st.button("Confirm", key=f"{key}-custom_upload_button")
        if upload and uploaded_file:
            data = load_data_table(uploaded_file, source="upload")
    return data


def data_editor(data: pl.DataFrame, key: str):
    """
    Provide an interface for editing a dataframe with various options.

    Parameters
    ----------
    data : polars.DataFrame
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


def data_fill(data: pl.DataFrame, key: str) -> pl.DataFrame:
    """
    Fill the configuration file with data from the selected dataset.

    Parameters
    ----------
    data : polars.DataFrame
        The dataframe to be replaced with the uploaded file.
    key : str
        The key for the Streamlit session state.

    Returns
    -------
    polars.DataFrame
        The dataframe with specified column added
    """
    with st.popover("Fill"):
        selected = None
        if "workflow-meta-datasets-sheets" in st.session_state:
            dataset = st.session_state.get("workflow-meta-datasets-sheets")
            selected = st.selectbox(
                "Select a dataset",
                options=list(dataset),
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

            data_modified = data.clone()
            column_to_add = data_selected.select(pl.col(column).alias(column_alias))

            if column_alias in data_modified.columns:
                if (
                    data_modified.schema[column_alias]
                    != column_to_add.schema[column_alias]
                ):
                    st.warning(f"Column '{column_alias}' has a different type")
                    try:
                        column_to_add = column_to_add.cast(
                            data_modified.schema[column_alias]
                        )
                    except pl.InvalidOperationError:
                        st.error("Failed translation to match types")
                        st.stop()

                column_to_add = column_to_add.with_columns(
                    [
                        pl.Series(
                            col,
                            [get_type_specific_default(data_modified[col].dtype)]
                            * len(column_to_add),
                        )
                        for col in data_modified.columns
                        if col != column_alias
                    ]
                ).select(data_modified.columns)  # Sort column order
                data_modified = pl.concat([data_modified, column_to_add])
            else:
                padding = len(data_selected) - len(data_modified)
                if padding > 0:
                    padding_df = pl.DataFrame(
                        {
                            col: [get_type_specific_default(data_modified[col].dtype)]
                            * padding
                            for col in data_modified.columns
                        }
                    )
                    data_modified = pl.concat([data_modified, padding_df])
                elif padding < 0:
                    padding_df = pl.DataFrame(
                        {
                            column_alias: [
                                get_type_specific_default(
                                    column_to_add[column_alias].dtype
                                )
                            ]
                            * -padding
                        }
                    )
                    column_to_add = pl.concat([column_to_add, padding_df])

                data_modified = data_modified.with_columns(column_to_add)

            st.dataframe(
                data_modified,
                height=225,
                use_container_width=True,
                key=f"{key}-fill_preview_window",
            )
            replace = st.button("Confirm", key=f"{key}-fill_button")
            if replace:
                data = data_modified
    return data


def data_selector(
    label: str, value: str, key: str, wd: WorkflowDeployer
) -> tuple[str, bool]:
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

        st.session_state[data_key] = load_data_table(
            st.session_state["workflow-config-dir_path"] / input_value
        )
        st.session_state[data_key_changed] = input_value

    if not isinstance(st.session_state[data_key], pl.DataFrame):
        st.error(f'File {value.split("/")[-1]} not found!')
        return input_value, False

    if data_schema_key not in st.session_state:
        data_schema = wd.get_json_schema(value.split("/")[-1].split(".")[0])
        data_config = st.session_state[data_key].to_dict(as_series=False)
        if data_schema:
            final_schema = update_schema(data_schema, data_config)
        else:
            final_schema = infer_schema(data_config)
        st.session_state[data_schema_key] = final_schema
        st.session_state[data_key] = enforce_typing(
            st.session_state[data_key], final_schema
        )

    with col2:
        show_data = toggle_button("Edit", key)
    return input_value, show_data


def delete_column(data: pl.DataFrame, key: str) -> pl.DataFrame:
    """
    Delete a column from the dataframe.

    Parameters
    ----------
    data : polars.DataFrame
        The dataframe from which the column will be deleted.
    key : str
        The key for the Streamlit session state.

    Returns
    -------
    polars.DataFrame
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
            data = data.drop(selected)
    return data


def execute_custom_code(data: pl.DataFrame, user_code: str) -> pl.DataFrame:
    """
    Execute custom code provided by the user on the dataframe.

    Parameters
    ----------
    data : polars.DataFrame
        The dataframe on which the custom code will be executed.
    user_code : str
        The custom code to execute on the dataframe.

    Returns
    -------
    polars.DataFrame
        The dataframe after the custom code has been executed.

    Notes
    -----
    This function uses Python's `exec` to run the custom code in a local scope.
    """
    local_vars = {}
    for key, value in [
        (key, value)
        for key, value in st.session_state.items()
        if (
            key.startswith("workflow-config-")
            and key.endswith("-data")
            and isinstance(value, pl.DataFrame)
            and not value.equals(data)
        )
    ]:
        local_var_key = key.split("-")[2].split(".")[-1]
        local_vars[local_var_key] = value

    local_vars["df"] = data
    exec(user_code, {}, local_vars)
    data = local_vars.get("df", data)
    if not isinstance(data, pl.DataFrame):
        st.error("The returned object is not a Polars DataFrame.")
    return data


def process_user_code(data: pl.DataFrame, key: str) -> pl.DataFrame:
    """
    Modify the dataframe using user-provided Python code.

    Parameters
    ----------
    data : polars.DataFrame
        The dataframe to be modified by the user's custom code.
    key : str
        The key for the Streamlit session state.

    Returns
    -------
    polars.DataFrame
        The dataframe after applying the user's custom modifications.

    Notes
    -----
    This function allows users to input and execute custom Python code to modify the dataframe.
    It provides a preview and an apply option for the modifications.
    """
    with st.session_state[key + "-placeholders"][1].expander(
        "Advanced table modification", expanded=True
    ):
        acestring = "# The table is available as df: pl.DataFrame\n# All other tables are accessible through their file name\n"

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
            for line in user_code.splitlines():
                if line.strip().startswith("import"):
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
            preview_data = data.clone()
            preview_data = execute_custom_code(preview_data, user_code)
            st.dataframe(
                preview_data,
                use_container_width=True,
                key=f"{key}-advanced_manipulation_preview_window",
            )
            validate_data(key, preview_data)
    if apply:
        data = execute_custom_code(data, user_code)
    return data


def rename_column(data: pl.DataFrame, key: str) -> pl.DataFrame:
    """
    Rename a column in the dataframe.

    Parameters
    ----------
    data : polars.DataFrame
        The dataframe containing the column to be renamed.
    key : str
        The key for the Streamlit session state.

    Returns
    -------
    polars.DataFrame
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
            data = data.rename({selected: renamed})
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
                schema["required"] = [
                    x.replace(selected, renamed) for x in schema["required"]
                ]
    return schema


def update_data(key: str):
    """
    Update the data in the session state based on user edits.

    Parameters
    ----------
    key : str
        The key for the Streamlit session state of the data.
    """
    editor = st.session_state[key + "-editor"]["edited_rows"]
    data = st.session_state[key + "-data"]
    if editor:
        for idx, row_edits in editor.items():
            for colname, new_value in row_edits.items():
                data[idx, colname] = new_value
        st.session_state[key + "-data"] = data
    else:
        st.warning("No edits detected in the data editor.")


def validate_data(key: str, data: pl.DataFrame | None = None):
    """
    Validate data against a schema.

    Parameters
    ----------
    key : str
        The key for the Streamlit session state.
    data : polars.DataFrame, optional
        The data to be validated. If not provided, it will be fetched from the session state.

    Notes
    -----
    This function checks if the data conforms to the required schema and highlights errors.
    """
    st.session_state["workflow-config-form-valid"][key] = True
    if not isinstance(data, pl.DataFrame):
        data = st.session_state[key + "-data"]
    data = data.to_dict(as_series=False)
    schema = st.session_state[key + "-schema"]
    required = schema.get("required")
    for field, field_info in schema.get("properties", {}).items():
        column = data.get(field)
        if required and field in required and not column:
            st.session_state["workflow-config-form-valid"][key] = False
            st.error(f'Column "{field}" is required but not found.')
            continue

        if column:
            invalid_rows = []
            for idx, value in enumerate(column):
                valid = True
                match field_info["type"]:
                    case typing if typing == "boolean":
                        if not any(str(value).lower() in ("true", "false", "0", "1")):
                            valid = False
                    case typing if typing == "string":
                        # no isinstance as the value might be an int or float as string
                        if not str(value).strip():
                            valid = False
                    case typing if typing == "number":
                        if not isinstance(value, (int | float)):
                            valid = False
                if not valid:
                    invalid_rows.append(str(idx + 1))
            if invalid_rows:
                rowstring = (
                    "s " + ", ".join(invalid_rows)
                    if len(invalid_rows) > 1
                    else " " + invalid_rows[0]
                )
                msg = f'Column "{field}" expects a "{schema["properties"][field]["type"]}" on row{rowstring}.'
                if field in required:
                    st.session_state["workflow-config-form-valid"][key] = False
                    st.error(msg)
                else:
                    st.warning(msg)
