import re

import streamlit as st
import yaml
from pandas import DataFrame
from streamlit_tags import st_tags

from common.components.data_editor import data_editor, data_selector
from common.components.schemas import get_property_type, infer_schema, update_schema


def create_form(config: dict, schema: dict, wd, parent_key: str = ""):
    """
    Create a pseudo Streamlit form based on a config dictionary and schema.

    Parameters
    ----------
    config : dict
        The config dictionary to generate the form from.
    schema : dict
        The schema defining the structure and types of the config.
    wd : any
        An object providing data-related functions.
    parent_key : str, optional
        The key of the parent config item, by default "".

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
            unique_element_key = update_key(parent_key, key)
            input_type = schema.get(prop_key).get(key)
            config[key] = get_input_element(
                key,
                value,
                input_type,
                unique_element_key,
                required_fields and key in required_fields,
                wd,
            )
        else:
            new_tabs.append((key, value))

    if new_tabs:
        tabs = st.tabs([key for key, _ in new_tabs])
        for tab, (key, value) in enumerate(new_tabs):
            updated_key = update_key(parent_key, key)
            if prop_key == "patternProperties":
                if not re.search(list(schema.get(prop_key).keys())[0], key):
                    print("Match unsuccessful")
                    st.error("Field name does not match schema.")
                key = list(schema[prop_key].keys())[0]
            with tabs[tab]:
                new_schema = schema[prop_key].get(key)
                create_form(value, new_schema, wd, updated_key)
    return config


@st.experimental_fragment
def get_input_element(
    label: str, value, input_type: dict, key: str, required: bool, wd
):
    """
    Get the appropriate Streamlit input element based on the input type.

    Parameters
    ----------
    label : str
        The label for the input element.
    value : any
        The current value of the input element.
    input_type : dict
        The schema type definition for the input element.
    key : str
        The unique key for the input element.
    required : bool
        Whether the input element is required.
    wd : any
        An object providing data-related functions.

    Returns
    -------
    any
        The value of the input element after user input.
    """
    input_value = None
    match input_type.get("type"):
        case input if input == "array" or "array" in input or (
            isinstance(input, list) and isinstance(value, list)
        ):
            if not isinstance(value, list):
                value = [value]
            # Cannot differentiate type here ~ no way to represent array of ints or floats
            input_value = st_tags(
                label=label,
                value=value,
                key=key,
            )
        case input if isinstance(input, list) and not isinstance(value, list):
            # input has multiple types and value is not a list => text_input can handle all remaining types
            input_value = st.text_input(label=label, value=value, key=key)
        case input if input == "string":
            if value is None or not value.endswith((".tsv", ".csv", ".xlsx")):
                input_value = st.text_input(label=label, value=value, key=key)
            else:
                input_value, show_data = data_selector(label, value, key, wd)
                data_key = key + "-data"
                # Workaround for popver and expander bug
                st.session_state[key + "-placeholders"] = [st.empty() for _ in range(2)]
                if show_data & isinstance(st.session_state[data_key], DataFrame):
                    data_editor(st.session_state[data_key], key)
                else:
                    [
                        placeholder.empty()
                        for placeholder in st.session_state[key + "-placeholders"]
                    ]
        case input if input == "integer":
            input_value = st.number_input(label=label, value=value, key=key)
        case input if input == "number":
            if "e" in str(value).lower():
                input_value = st.text_input(label=label, value=value, key=key)
            else:
                input_value = st.number_input(
                    label=label,
                    value=value,
                    key=key,
                    step=10
                    ** -len(str(value).split(".")[-1]),  # infer significant decimals
                    format="%f",
                )
        case input if input == "boolean":
            input_value = st.checkbox(label=label, value=value, key=key)
        case input if input == "missing":
            # empty endpoints default to list
            input_value = st_tags(
                label=label,
                value=value,
                key=key,
            )
        case input:
            st.error("No fitting input was found for your data!")
    if required:
        valid = validate_input(st.session_state[key], input)
        # data inputs are validated in the data_editor and must not be overwritten
        if key not in st.session_state["workflow_config-form-valid"]:
            st.session_state["workflow_config-form-valid"][key] = valid
        if not valid:
            report_invalid_input(st.session_state[key], key, input)
    return input_value


def load_yaml(config: str):
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
        assert config is not None
        return config
    except yaml.YAMLError as e:
        st.error(f"Error parsing config YAML: {e}")
        st.stop()
    except AssertionError:
        st.error("Configuration File is empty")
        st.stop()


def report_invalid_input(value, key: str, input_type: str):
    """
    Report an invalid input in the Streamlit app.

    Parameters
    ----------
    key : str
        The key of the invalid input.
    input_type : str
        The type of the invalid input.
    """
    msg = " => ".join(key.split(".")[1:])
    match input_type:
        case input_type if input_type == "string" and not value.strip():
            st.error(f"{msg} must not be empty")
        case input_type:
            st.error(f"{msg} is filled incorrectly")


def update_key(parent_key: str, new_key: str):
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
    return ".".join((parent_key, new_key)) if parent_key != "" else new_key


def validate_input(value, input_type: str):
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
            # No isinstance as the value might be an int or float as string
            if not str(value).strip() or not value:
                return False
        case typing if typing == "number":
            if not isinstance(value, (int, float)):
                return False
    return True


st.cache_data


def load_config_and_schema(conf_path, wd):
    """
    Load configuration and schema.

    Parameters
    ----------
    conf_path : Path
        The path to the configuration file.
    wd : object
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


def config_editor(conf_path, wd):
    """
    Edit a configuration file in the Streamlit app.

    Parameters
    ----------
    conf_path : Path
        The path to the configuration file.
    wd : any
        An object providing data-related functions.

    Returns
    -------
    str
        The updated configuration as a YAML string.
    """
    config, final_schema = load_config_and_schema(conf_path, wd)
    st.session_state["workflow_config-form-valid"] = {}
    config = create_form(config, final_schema, wd, "workflow_config-")
    config = yaml.dump(config, sort_keys=False)
    return config
