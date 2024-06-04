import streamlit as st
from pandas import DataFrame
from streamlit_tags import st_tags
import yaml
import re

from common.components.schemas import get_property_type, infer_schema, update_schema
from common.components.data_editor import data_editor, data_selector


def create_form(config: dict, schema: dict, wd, parent_key: str = ""):
    prop_key = get_property_type(schema)
    required_fields = schema.get("required")
    items = []
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
            items.append((key, value))

    if items:
        tabs = st.tabs([key for key, _ in items])
        for tab, (key, value) in enumerate(items):
            updated_key = update_key(parent_key, key)
            if prop_key == "patternProperties":
                # assert re.search(list(schema.get(prop_key).keys())[0], key) # TODO: Proper Matching
                key = list(schema.get(prop_key).keys())[0]
            with tabs[tab]:
                new_schema = schema.get(prop_key).get(key)
                create_form(value, new_schema, wd, updated_key)
    return config


@st.experimental_fragment
def get_input_element(
    label: str, value, input_type: dict, key: str, required: bool, wd
):
    # TODO: Edit button to adapt input fields?
    input_value = None
    match input_type.get("type"):
        # implement accessing "format" for strings
        case input if isinstance(input, list) and isinstance(
            value, list
        ) and "array" in input:
            input_value = st_tags(
                label=label,
                value=value,
                key=key,
            )
        case input if isinstance(input, list) and not isinstance(value, list):
            input_value = st.text_input(label=label, value=value, key=key)
        case input if input == "array":  # Cannot differentiate type here yet
            input_value = st_tags(
                label=label,
                value=value,
                key=key,
            )
        case input if input == "string":
            if value == None or not value.endswith((".tsv", ".csv", ".xlsx")):
                input_value = st.text_input(label=label, value=value, key=key)
            else:
                input_value, show_data = data_selector(label, value, key, wd)
                if show_data & isinstance(st.session_state["data" + key], DataFrame):
                    st.session_state["data" + key] = data_editor(
                        st.session_state["data" + key]
                    )
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
            # empty endpoints default to list TODO: Better handling, let user choose?
            input_value = st_tags(
                label=label,
                value=value,
                key=key,
            )
        case value if type(value) == list:
            input_value = st_tags(
                label=label,
                value=value,
                key=key,
            )
        case input:
            # TODO more verbose
            print("No fitting input was found for your data!")
    if required:
        # TODO Also implement checks for formatting!
        valid = validate_input(st.session_state[key], input)
        st.session_state["valid_config_form"][key] = valid
        if not valid:
            report_invalid_input(key, input)
    return input_value


def load_yaml(config):
    try:
        config = yaml.load(config, Loader=yaml.SafeLoader)
        assert config != None
        return config
    except yaml.YAMLError as e:
        st.error(f"Error parsing config YAML: {e}")
        st.stop()
    except AssertionError:
        st.error(f"Configuration File is empty")
        st.stop()


def report_invalid_input(key, input_type):
    match input_type:
        case input_type if input_type == "string":
            st.error(f"{key} needs adjustment")


def update_key(parent_key, new_key):
    return ".".join((parent_key, new_key)) if parent_key != "" else new_key


def validate_input(value, input_type):
    valid = True
    # TODO: More elaborate depending on input type
    if value == None or value == "":
        valid = False
    return valid


def config_editor(conf_path, wd):
    config_schema = wd.get_json_schema("config")
    config = load_yaml(conf_path.read_text())
    if config_schema:
        final_schema = update_schema(config_schema, config)
    else:
        final_schema = infer_schema(config)
    st.session_state["valid_config_form"] = {}
    config = create_form(config, final_schema, wd)

    config = yaml.dump(config, sort_keys=False)
    return config
