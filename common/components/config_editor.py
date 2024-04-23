import streamlit as st
import pandas as pd
from streamlit_ace import st_ace
from streamlit_tags import st_tags
from pathlib import Path
import yaml

from common.components.data_editor import data_editor, data_selector


@st.experimental_fragment
def get_input_element(label: str, value, key: str):
    input_value = None
    match value:
        case bool(value):
            input_value = st.checkbox(label=label, value=value, key=key)
        case str(value) if value.endswith((".tsv", ".csv", ".xlsx")):
            input_value, show_data = data_selector(label, value, key)
            if show_data & isinstance(st.session_state ["data" + key], pd.DataFrame):
                data_editor(st.session_state ["data" + key])
        case str(value):
            input_value = st.text_input(label=label, value=value, key=key)
        case int(value):
            input_value = st.number_input(label=label, value=value, key=key)
        case float(value) if "e" in str(value).lower():
            input_value = st.text_input(label=label, value=value, key=key)
        case float(value):
            input_value = st.number_input(
                label=label,
                value=value,
                key=key,
                step=10 ** -len(str(value).split(".")[-1]),  # infer significant decimals
                format="%f",
            )
        case value if type(value) == list or type(value) == type(None):
            # empty endpoints default to list
            input_value = st_tags(
                label=label,
                value=value,
                key=key,
            )
    return input_value


def get_nested_tabs(config: dict, parent_key: str = ""):
    """Iteratively creates nested Streamlit tabs from a dictionary structure and replaces endpoint
    values (leaf nodes) from the dictionary with type specific streamlit-inputs.

    Parameters
    ----------
    config : dict
        ...
    parent_key : str, optional
        unique id, by default ""
    """
    items = []
    for key, value in config.items():
        # check for leaf nodes = endpoints
        if not isinstance(value, dict):
            unique_element_key = "?".join((parent_key, key))
            # link type-specific input
            config[key] = get_input_element(key, value, unique_element_key)
        else:
            items.append((key, value))

    if items:
        tabs = st.tabs([key for key, _ in items])
        for tab, (key, value) in enumerate(items):
            key_name = "?".join((parent_key, key))
            with tabs[tab]:
                get_nested_tabs(value, key_name)


def load_yaml(config):
    try:
        config = yaml.load(config, Loader=yaml.SafeLoader)
        return config
    except yaml.YAMLError as e:
        st.error(f"Error parsing config YAML: {e}")
        st.stop()


def config_editor(dir_path, config_viewer, disabled):
    # handle config
    st.session_state["dir_path"] = dir_path
    conf_path = Path(dir_path) / "config" / "config.yaml"
    if not conf_path.exists():
        st.error("No config file found!")
    else:
        # with st.container(border=True):
        st.divider()
        match config_viewer:
            case x if x == "Form":
                config = load_yaml(conf_path.read_text())
                get_nested_tabs(config)
                config = yaml.dump(config, sort_keys=False)
            case x if x == "Text Editor":
                config = st_ace(conf_path.read_text(), language="yaml")
        with open(conf_path, "w") as f:
            f.write(config)
        store = st.button("Store", disabled=disabled)
    return store
