import polars as pl
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from streamlit_ace import THEMES, st_ace

from common.components.schemas import infer_schema, update_schema
from common.components.ui_components import toggle_button
from common.data.entities.analysis import WorkflowManager
from common.utils.polars_utils import (
    enforce_typing,
    get_type_specific_default,
    load_data_table,
    merge_dataframes,
)


def add_column(key: str) -> None:
    """Add a new column to the dataframe.

    :param key: The key for the Streamlit session state.
    """

    def add(data: pl.DataFrame, column: str) -> None:
        if column.strip() and column not in data.columns:
            st.session_state[f"{key}-data"] = data.with_columns(
                pl.Series(column, [""] * len(data)),
            )

    with st.popover("", icon=":material/add:", help="Add a column"):
        column = st.text_input("Add column", key=f"{key}-add_column_text")
        st.button(
            "Add",
            key=f"{key}-add_column_button",
            on_click=add,
            args=(
                st.session_state[f"{key}-data"],
                column,
            ),
        )


def clear_data(key: str) -> None:
    """Clear all rows of the dataframe.

    :param key: The key for the Streamlit session state.
    """

    def clear(data: pl.DataFrame) -> None:
        st.session_state[f"{key}-data"] = pl.DataFrame(schema=data.schema)

    st.button(
        "",
        icon=":material/mop:",
        help="Clear all entries",
        key=f"{key}-clear_data_button",
        on_click=clear,
        args=(st.session_state[f"{key}-data"],),
    )


def custom_upload(key: str) -> None:
    """Upload a custom configuration file and replace the dataframe.

    :param key: The key for the Streamlit session state.
    """

    def upload(uploaded_file: UploadedFile) -> None:
        st.session_state[f"{key}-data"] = load_data_table(
            uploaded_file,
            source="upload",
        )

    with st.popover("", icon=":material/upload:", help="Upload a config"):
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=("xlsx", "tsv", "csv"),
            key=f"{key}-custom_upload_field",
        )
        st.button(
            "Confirm",
            key=f"{key}-custom_upload_button",
            on_click=upload,
            args=(uploaded_file,),
        )


def data_editor(key: str) -> None:
    """Provide an interface for editing a dataframe with various options.

    :param key: The key for the Streamlit session state.
    """
    col1, col2, col3, col4, col5, col6 = st.session_state[f"{key}-placeholders"][
        0
    ].columns(6)
    with col1:
        add_column(key)
    with col2:
        rename_column(key)
    with col3:
        delete_column(key)
    with col4:
        custom_upload(key)
    with col5:
        data_fill(key)
    with col6:
        clear_data(key)
    process_user_code(key)
    dataset_ids = list(st.session_state.get("workflow-meta-datasets-sheets"))
    st.session_state[f"{key}-placeholders"][2].data_editor(
        st.session_state[f"{key}-data"],
        use_container_width=True,
        num_rows="dynamic",
        on_change=update_data,
        args=(key,),
        key=f"{key}-editor",
        column_config={
            "datasetid": st.column_config.SelectboxColumn(
                "datasetid",
                options=dataset_ids,
                default=dataset_ids[0] if dataset_ids else None,
            ),
        },
    )
    validate_data(key, st.session_state[f"{key}-data"])


def generate_from_to_fields(
    idx: int,
    from_col: str,
    to_col: str,
    key: str,
    data_selected: pl.DataFrame,
) -> tuple[str]:
    """Generate UI for selecting 'From' and 'To' column pairs."""
    cols = st.columns([3, 3, 1])
    with cols[0]:
        st.text("From")
    with cols[1]:
        st.text("To")
    cols = st.columns([3, 3, 1])
    with cols[0]:
        from_col_val = st.selectbox(
            "From",
            options=data_selected.columns,
            index=data_selected.columns.index(from_col)
            if from_col in data_selected.columns
            else 0,
            key=f"{key}-fill_column_select-{idx}",
            label_visibility="collapsed",
        )
    with cols[1]:
        to_col_val = st.text_input(
            "To",
            to_col,
            key=f"{key}-fill_column_alias-{idx}",
            label_visibility="collapsed",
        )
    with cols[2]:
        st.button(
            "",
            key=f"{key}-remove-{idx}",
            on_click=lambda: st.session_state[f"{key}-fill_pairs"].pop(idx),
            icon=":material/remove:",
        )
    return from_col_val, to_col_val


def add_new_from_to_field(key: str, data_selected: pl.DataFrame) -> None:
    """Add a new 'From-To' field pair to the session state."""
    next_idx = st.session_state[f"{key}-next_col_idx"]
    next_col = data_selected.columns[next_idx]
    st.session_state[f"{key}-fill_pairs"].append((next_col, next_col))
    st.session_state[f"{key}-next_col_idx"] = (next_idx + 1) % len(
        data_selected.columns,
    )


def prepare_fill_pairs(key: str, data_selected: pl.DataFrame) -> None:
    """Initialize the 'fill_pairs' and related session state variables."""
    if f"{key}-fill_pairs" not in st.session_state:
        default_col = data_selected.columns[0]
        st.session_state[f"{key}-fill_pairs"] = [(default_col, default_col)]
        st.session_state[f"{key}-next_col_idx"] = 1


def validate_and_cast_columns(
    data_selected: pl.DataFrame,
    data_modified: pl.DataFrame,
    from_col: str,
    to_col: str,
) -> pl.DataFrame:
    """Validate and cast columns as necessary."""
    column_to_add = data_selected.select(pl.col(from_col).alias(to_col))
    if to_col in data_modified.columns:
        if data_modified.schema[to_col] != column_to_add.schema[to_col]:
            st.warning(f"Column '{to_col}' has a different type")
            try:
                column_to_add = column_to_add.cast(data_modified.schema[to_col])
            except pl.InvalidOperationError:
                st.error(
                    f"Failed to cast column '{from_col}' to match the existing '{to_col}' type",
                )
                st.stop()
    else:
        col_type = data_selected[from_col].dtype
        default_value = get_type_specific_default(col_type)
        new_column = pl.Series(
            to_col,
            [default_value] * len(data_modified),
            dtype=col_type,
        )
        data_modified = data_modified.with_columns(new_column)
    return column_to_add


def data_fill(key: str) -> None:
    """Fill the configuration file with data from a selected dataset."""
    with st.popover("", icon=":material/library_add:"):
        selected = None
        if "workflow-meta-datasets-sheets" in st.session_state:
            dataset = st.session_state.get("workflow-meta-datasets-sheets")
            if dataset:
                selected = st.selectbox(
                    "Select a dataset",
                    options=list(dataset),
                    key=f"{key}-fill_data_select",
                )
        if selected:
            data_selected = dataset[selected]
            data_modified = st.session_state[f"{key}-data"].clone()

            prepare_fill_pairs(key, data_selected)
            fill_pairs = st.session_state[f"{key}-fill_pairs"]

            for i, (from_col, to_col) in enumerate(fill_pairs):
                fill_pairs[i] = generate_from_to_fields(
                    i,
                    from_col,
                    to_col,
                    key,
                    data_selected,
                )

            st.button(
                "",
                key=f"{key}-add_next",
                on_click=lambda: add_new_from_to_field(key, data_selected),
                icon=":material/add:",
            )

            columns_to_add = []
            for from_col, to_col in fill_pairs:
                column_to_add = validate_and_cast_columns(
                    data_selected,
                    data_modified,
                    from_col,
                    to_col,
                )
                columns_to_add.append(column_to_add)

            if columns_to_add:
                data_modified = merge_dataframes(
                    data_modified,
                    columns_to_add,
                    selected,
                )

            st.dataframe(
                data_modified,
                height=250,
                use_container_width=True,
                key=f"{key}-fill_preview_window",
            )

            if st.button("Confirm", key=f"{key}-fill_button"):
                st.session_state[f"{key}-data"] = data_modified.clone()


def data_selector(
    label: str,
    value: str,
    key: str,
    workflow_manager: WorkflowManager,
) -> tuple[str, bool]:
    """Create a data selector widget in Streamlit.

    :param label: The label for the text input widget.
    :param value: The initial value of the text input.
    :param key: The key to store the text input value in Streamlit's session state.
    :param workflow_manager: An object providing data-related functions.
    :return: A tuple containing the input value and a boolean indicating whether to show the data editor.
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
    data_key = f"{key}-data"
    data_key_changed = f"{key}-data_token"
    data_schema_key = f"{key}-schema"

    if (
        data_key not in st.session_state
        or data_key_changed not in st.session_state
        or st.session_state.get(data_key_changed) != input_value
    ):
        if data_schema_key in st.session_state:
            st.session_state.pop(data_schema_key)

        st.session_state[data_key] = load_data_table(
            workflow_manager.data_path / input_value,
        )

        st.session_state[data_key_changed] = input_value

    if not isinstance(st.session_state[data_key], pl.DataFrame):
        st.error(f"File {value.split('/')[-1]} not found!")
        return input_value, False
    st.session_state[data_key] = st.session_state[data_key].with_columns(
        datasetid=pl.lit(""),
    )

    if data_schema_key not in st.session_state:
        data_schema = workflow_manager.get_schema(value.split("/")[-1].split(".")[0])
        data_config = st.session_state[data_key].to_dict(as_series=False)
        if data_schema:
            final_schema = update_schema(data_schema, data_config)
        else:
            final_schema = infer_schema(data_config)
        st.session_state[data_schema_key] = final_schema
        st.session_state[data_key] = enforce_typing(
            st.session_state[data_key],
            final_schema,
        )

    with col2:
        show_data = toggle_button("", key, icon=":material/keyboard_arrow_down:")
    return input_value, show_data


def delete_column(key: str) -> None:
    """Delete a column from the dataframe.

    :param key: The key for the Streamlit session state.
    """

    def delete(data: pl.DataFrame, selected: str) -> None:
        st.session_state[f"{key}-data"] = data.drop(selected)

    with st.popover("", icon=":material/remove:", help="Remove a column"):
        selected = st.selectbox(
            "Select column to delete",
            options=st.session_state[f"{key}-data"].columns,
            key=f"{key}-delete_column_select",
        )
        st.button(
            "Delete",
            key=f"{key}-delete_column_button",
            on_click=delete,
            args=(
                st.session_state[f"{key}-data"],
                selected,
            ),
        )


def execute_custom_code(
    data: pl.DataFrame,
    key: str,
    user_code: str,
    mode: str,
) -> pl.DataFrame | None:
    """Execute custom code provided by the user on the dataframe.

    :param data: The dataframe on which the custom code will be executed.
    :param user_code: The custom code to execute on the dataframe.
    :param mode: The mode to determine whether the result should be applied or returned.
    :return: The dataframe after the custom code has been executed, or None if mode is 'apply'.
    """
    user_code = "import polars as pl\nimport numpy as np\n" + user_code
    local_vars = {}
    for k, value in [
        (k, value)
        for k, value in st.session_state.items()
        if (
            k.startswith("workflow-config-")
            and k.endswith("-data")
            and isinstance(value, pl.DataFrame)
            and f"{key}-data" != k
        )
    ]:
        local_var_key = k.split("-")[2].split(".")[-1]
        local_vars[local_var_key] = value

    local_vars["df"] = data
    exec(user_code, {}, local_vars)
    data = local_vars.get("df", data)
    if not isinstance(data, pl.DataFrame):
        st.error("The returned object is not a Polars DataFrame.")
    if mode == "apply":
        st.session_state[f"{key}-data"] = data
        return None
    return data


def modify_schema(schema: dict, key: str) -> dict:
    """Rename a column in the dataframe schema.

    :param schema: The data schema.
    :param key: The key for the Streamlit session state.
    :return: The data schema with the renamed column.
    """
    with st.popover("Modify"):
        selected = st.selectbox(
            "Select column-schema to rename",
            options=schema["properties"].keys(),
            key=f"{key}-modify_column_select",
        )
        renamed = st.text_input(
            "Rename to",
            value=selected,
            key=f"{key}-modify_column_text",
        )
        rename = st.button("Rename", key=f"{key}-modify_column_button")
        if rename and renamed.strip():
            schema["properties"][renamed] = schema["properties"].pop(selected)
            if selected in schema["required"]:
                schema["required"] = [
                    x.replace(selected, renamed) for x in schema["required"]
                ]
    return schema


def process_user_code(key: str) -> None:
    """Modify the dataframe using user-provided Python code.

    :param key: The key for the Streamlit session state that identifies the data.
    """
    with st.session_state[f"{key}-placeholders"][1].expander(
        "Advanced table modification",
        expanded=True,
    ):
        acestring = "# The table is available as df: pl.DataFrame\n# All other tables are accessible through their file name\n"

        c1, c2 = st.columns([3.25, 1])
        with c1:
            user_code = st_ace(
                acestring,
                auto_update=False,
                language="python",
                height=300,
                theme=c2.selectbox(
                    "Theme",
                    options=THEMES,
                    index=35,
                    key=f"{key}-color_theme",
                ),
                font_size=c2.slider(
                    "Font size",
                    5,
                    24,
                    14,
                    key=f"{key}-font_size_slider",
                ),
                key=f"{key}-st_ace",
            )
        no_import = True
        if "import " in user_code:
            for line in user_code.splitlines():
                if line.strip().startswith("import"):
                    no_import = False
                    st.error("Remove line with 'import' as no imports are allowed.")
                    break
        col1, col2 = c2.columns(2)
        with col1:
            preview = st.button(
                "",
                key=f"{key}-advanced_manipulation_preview_config",
                disabled=not no_import,
                icon=":material/pageview:",
                help="Preview the changes",
            )
        with col2:
            st.button(
                "",
                key=f"{key}-advanced_manipulation_apply_config",
                disabled=not no_import,
                icon=":material/publish:",
                help="Apply the changes",
                on_click=execute_custom_code,
                args=(
                    st.session_state[f"{key}-data"],
                    key,
                    user_code,
                    "apply",
                ),
            )
        if preview:
            preview_data = st.session_state[f"{key}-data"].clone()
            # returned again as preview_data does not need to be placed in session state
            preview_data = execute_custom_code(preview_data, key, user_code, "preview")
            st.dataframe(
                preview_data,
                use_container_width=True,
                key=f"{key}-advanced_manipulation_preview_window",
            )
            validate_data(key, preview_data)


def rename_column(key: str) -> None:
    """Rename a column in the dataframe.

    :param key: The key for the Streamlit session state that identifies the data.
    """

    def rename(data: pl.DataFrame, selected: str, renamed: str) -> None:
        if rename and renamed.strip():
            st.session_state[f"{key}-data"] = data.rename({selected: renamed})

    with st.popover("", icon=":material/edit:", help="Rename a column"):
        selected = st.selectbox(
            "Select column to rename",
            options=st.session_state[f"{key}-data"].columns,
            key=f"{key}-rename_column_select",
        )
        renamed = st.text_input(
            "Rename to",
            value=selected,
            key=f"{key}-rename_column_text",
        )
        st.button(
            "Rename",
            key=f"{key}-rename_column_button",
            on_click=rename,
            args=(
                st.session_state[f"{key}-data"],
                selected,
                renamed,
            ),
        )


def update_data(key: str) -> None:
    """Update the data in the session state based on user edits.

    :param key: The key for the Streamlit session state that identifies the data.
    """
    editor = st.session_state[f"{key}-editor"]["edited_rows"]
    data = st.session_state[f"{key}-data"]
    if editor:
        for idx, row_edits in editor.items():
            for colname, new_value in row_edits.items():
                data[idx, colname] = new_value
        st.session_state[f"{key}-data"] = data
    else:
        st.warning("No edits detected in the data editor.")


def validate_data(key: str, data: pl.DataFrame | None = None) -> None:
    """Validate a dataset against its associated schema.

    :param key: The key for the Streamlit session state identifying the dataset and schema.
    :param data: The dataset to be validated. If not provided, it will be fetched from the Streamlit session state.
    """
    st.session_state["workflow-config-form-valid"][key] = True

    # Fetch data and schema if not provided
    if not isinstance(data, pl.DataFrame):
        data = st.session_state.get(f"{key}-data")
    if data is None:
        st.error(f"No data found for key: {key}")
        return

    data_dict = data.to_dict(as_series=False)
    schema = st.session_state.get(f"{key}-schema")
    if not schema:
        st.error(f"No schema found for key: {key}")
        return

    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})

    for field, field_info in properties.items():
        column_data = data_dict.get(field)
        if field in required_fields and not column_data:
            report_missing_required_field(key, field)
            continue

        if column_data:
            validate_column_data(
                key,
                field,
                column_data,
                field_info,
                is_required=(field in required_fields),
            )


def report_missing_required_field(key: str, field: str) -> None:
    """Report a missing required field.

    :param key: The key for the Streamlit session state identifying the dataset.
    :param field: The missing field name.
    """
    st.session_state["workflow-config-form-valid"][key] = False
    st.error(f'Column "{field}" is required but not found.')


def validate_column_data(
    key: str,
    field: str,
    column_data: list,
    field_info: dict,
    *,
    is_required: bool,
) -> None:
    """Validate a single column against its schema definition.

    :param key: The key for the Streamlit session state identifying the dataset.
    :param field: The name of the column being validated.
    :param column_data: The data of the column as a list.
    :param field_info: Schema definition for the field, including type constraints.
    :param is_required: Whether the field is marked as required.
    """

    def is_value_valid(value: any, expected_type: str) -> bool:
        match expected_type:
            case "boolean":
                return str(value).lower() in {"true", "false", "0", "1"}
            case "string":
                return bool(str(value).strip())
            case "number":
                return isinstance(value, int | float)
            case _:
                return True

    invalid_rows = []

    for idx, value in enumerate(column_data):
        if not is_value_valid(value, field_info["type"]):
            invalid_rows.append(idx + 1)

    if invalid_rows:
        row_string = (
            "s " + ", ".join(map(str, invalid_rows))
            if len(invalid_rows) > 1
            else f" {invalid_rows[0]}"
        )
        message = (
            f'Column "{field}" expects a "{field_info["type"]}" on row{row_string}.'
        )

        if is_required:
            st.session_state["workflow-config-form-valid"][key] = False
            st.error(message)
        else:
            st.warning(message)
