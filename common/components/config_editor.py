import re
from pathlib import Path

import streamlit as st
import yaml
from polars import DataFrame
from snakedeploy.deploy import WorkflowDeployer
from streamlit_ace import st_ace
from streamlit_tags import st_tags

from common.components.data_editor import data_editor, data_selector
from common.components.schemas import get_property_type, infer_schema, update_schema


def ace_config_editor(conf_path: Path, wd: WorkflowDeployer) -> str:
    """
    Edit a configuration file in the Streamlit app with st_ace.

    Parameters
    ----------
    conf_path : Path
        The path to the configuration file.
    wd : WorkflowDeployer
        An object providing data-related functions.

    Returns
    -------
    str
        The updated configuration as a YAML string.
    """
    config, final_schema = load_config_and_schema(conf_path, wd)
    st.session_state["workflow-config-form-valid"] = {}
    config = st_ace(conf_path.read_text(), language="yaml")
    create_form(
        yaml.safe_load(config),
        final_schema,
        wd,
        "workflow-config-",
        ace_editor=True,
    )
    return config


def config_editor(conf_path: Path, wd: WorkflowDeployer) -> str:
    """
    Edit a configuration file in the Streamlit app.

    Parameters
    ----------
    conf_path : Path
        The path to the configuration file.
    wd : WorkflowDeployer
        An object providing data-related functions.

    Returns
    -------
    str
        The updated configuration as a YAML string.
    """
    config, final_schema = load_config_and_schema(conf_path, wd)
    st.session_state["workflow-config-form-valid"] = {}
    config = create_form(config, final_schema, wd, "workflow-config-")
    return yaml.dump(config, sort_keys=False)


def create_form(
    config: dict,
    schema: dict,
    wd: WorkflowDeployer,
    parent_key: str = "",
    ace_editor: bool = False,
) -> dict:
    """
    Create a pseudo Streamlit form based on a config dictionary and schema.

    Parameters
    ----------
    config : dict
        The config dictionary to generate the form from.
    schema : dict
        The schema defining the structure and types of the config.
    wd : WorkflowDeployer
        An object providing data-related functions.
    parent_key : str, optional
        The key of the parent config item, by default "".
    ace_editor : bool, optional
        If True, adjusts input generation and validation to be compatible with the ACE editor interface.

    Returns
    -------
    dict
        The updated config dictionary after form input.
    """
    prop_key = get_property_type(schema)
    required_fields = schema.get("required")
    new_tabs = []
    for key, value in config.items():
        if not isinstance(value, dict):  # check for leaf nodes = endpoints
            unique_element_id = update_key(parent_key, key)
            input_dict = schema[prop_key].get(key)
            only_validation = ace_editor and not (
                input_dict["type"] == "string"
                and value
                and value.endswith((".tsv", ".csv", ".xlsx"))
            )
            config[key] = get_input_element(
                key,
                value,
                input_dict,
                unique_element_id,
                required_fields and key in required_fields,
                wd,
                ace_editor=only_validation,
            )
        else:
            new_tabs.append((key, value))

    if new_tabs:
        if not ace_editor:
            tabs = st.tabs([key for key, _ in new_tabs])
        for tab, (key, value) in enumerate(new_tabs):
            updated_parent_key = update_key(parent_key, key)
            if prop_key == "patternProperties":
                if not re.search(next(iter(schema[prop_key])), key):
                    st.error("Field name does not match schema.")
                updated_key = next(iter(schema[prop_key]))
            else:
                updated_key = key
            if not ace_editor:
                with tabs[tab]:
                    new_schema = schema[prop_key].get(updated_key)
                    create_form(value, new_schema, wd, updated_parent_key)
            else:
                new_schema = schema[prop_key].get(updated_key)
                create_form(value, new_schema, wd, updated_parent_key, ace_editor=True)
    return config


@st.fragment
def get_input_element(
    label: str,
    value: any,
    input_dict: dict,
    key: str,
    required: bool,
    wd: WorkflowDeployer,
    ace_editor: bool,
) -> any:
    """
    Get the appropriate Streamlit input element based on the input type and validate it.

    Parameters
    ----------
    label : str
        The label for the input element.
    value : any
        The current value of the input element.
    input_dict : dict
        The schema type definition for the input element.
    key : str
        The unique key for the input element.
    required : bool
        Whether the input element is required.
    wd : WorkflowDeployer
        An object providing data-related functions.
    ace_editor : bool
        Different behavior for inputs accompanying the ace_editor

    Returns
    -------
    any
        The value of the input element after user input.

    Notes
    -----
    Input generation and validation combined with @st.fragment to create inputs that do not cause page reload on change but can still produce verbose warnings and errors.
    """
    input_value = value
    input_type = input_dict.get("type", "missing")
    if not ace_editor:  # Do not show in ace_editor just validate
        match input_type:
            case input_type if input_type == "array" or "array" in input_type or (
                isinstance(input_type, list) and isinstance(value, list)
            ):
                # cannot differentiate type here ~ no way to represent array of ints or floats except stringified
                if not isinstance(value, list):
                    value = [value]
                input_value = st_tags(
                    label=label,
                    value=value,
                    key=key,
                )
            case input_type if isinstance(input_type, list) and not isinstance(
                value, list
            ):
                # input has multiple types and value is not a list => text_input can handle all remaining types
                input_value = st.text_input(label=label, value=value, key=key)
            case input_type if input_type == "string":
                if not value.endswith((".tsv", ".csv", ".xlsx")):
                    input_value = st.text_input(label=label, value=value, key=key)
                else:
                    input_value, show_data = data_selector(label, value, key, wd)
                    data_key = key + "-data"
                    # workaround for popver and expander "bug"
                    st.session_state[key + "-placeholders"] = [
                        st.empty() for _ in range(3)
                    ]
                    if show_data and isinstance(st.session_state[data_key], DataFrame):
                        data_editor(st.session_state[data_key], key)
            case input_type if input_type == "integer":
                input_value = st.number_input(label=label, value=value, key=key)
            case input_type if input_type == "number":
                if "e" in str(value).lower():
                    input_value = st.text_input(label=label, value=value, key=key)
                else:
                    input_value = st.number_input(
                        label=label,
                        value=value,
                        key=key,
                        step=10
                        ** (
                            -len(str(value).split(".")[-1]) if "." in str(value) else 0
                        ),  # infer significant decimals
                        format="%f",
                    )
            case input_type if input_type == "boolean":
                input_value = st.checkbox(label=label, value=value, key=key)
            case input_type if input_type == "missing":
                # empty endpoints default to list
                input_value = st_tags(
                    label=label,
                    value=value,
                    key=key,
                )
            case input_type:
                st.error("No fitting input was found for your data!")
    if required:
        valid = validate_input(input_value, input_type)
        # data inputs are validated in the data_editor and must not be overwritten here
        if key not in st.session_state["workflow-config-form-valid"]:
            st.session_state["workflow-config-form-valid"][key] = valid
        if not valid:
            report_invalid_input(input_value, key, input_type)
    return input_value


def load_config_and_schema(conf_path: Path, wd: WorkflowDeployer) -> tuple[dict, dict]:
    """
    Load configuration and schema.

    Parameters
    ----------
    conf_path : Path
        The path to the configuration file.
    wd : WorkflowDeployer
        The workflow deployer object to get the JSON schema.

    Returns
    -------
    tuple
        The configuration and the final schema.
    """
    config_schema = wd.get_json_schema("config")
    config = load_yaml(conf_path.read_text())
    if config_schema:
        final_schema = update_schema(config_schema, config)
    else:
        final_schema = infer_schema(config)
    return config, final_schema


def load_yaml(config: str) -> dict:
    """
    Load a YAML configuration file.

    Parameters
    ----------
    config : str
        The YAML configuration string.

    Returns
    -------
    dict
        The loaded configuration dictionary.

    Raises
    ------
    st.error
        If there is an error parsing the YAML or if the configuration is empty.
    """
    try:
        config = yaml.load(config, Loader=yaml.SafeLoader)
        if config is not None:
            return config
        st.error("Configuration File is empty")
        st.stop()

    except yaml.YAMLError as e:
        st.error(f"Error parsing config YAML: {e}")
        st.stop()


def report_invalid_input(value: any, key: str, input_type: str):
    """
    Report an invalid input in the Streamlit app.

    Parameters
    ----------
    value : any
        The current value of the input element.
    key : str
        The key of the invalid input.
    input_type : str
        The type of the invalid input.
    """
    msg = ">".join(key.split(".")[1:])
    match input_type:
        case input_type if input_type == "string" and not str(value).strip():
            st.error(f"{msg} must not be empty")
        case input_type:
            st.error(f"{msg} is filled incorrectly")


def update_key(parent_key: str, new_key: str) -> str:
    """
    Update a key by appending a new key to a parent key.

    Parameters
    ----------
    parent_key : str
        The parent key.
    new_key : str
        The new key to append.

    Returns
    -------
    str
        The updated key.
    """
    return f"{parent_key}.{new_key}" if parent_key != "" else new_key


def validate_input(value: any, input_type: str) -> bool:
    """
    Validate an input value based on its type.

    Parameters
    ----------
    value : any
        The value to validate.
    input_type : str
        The type of the input value.

    Returns
    -------
    bool
        True if the value is valid, False otherwise.
    """
    match input_type:
        case typing if typing == "boolean":
            return True
        case typing if typing == "string":
            # no isinstance as the value might be an int or float as string
            if not str(value).strip() or not value:
                return False
        case typing if typing == "number":
            if "e" in str(value).lower():
                return True
            if not isinstance(value, (int, float)):
                return False
    return True
