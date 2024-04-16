import streamlit as st
from streamlit_tags import st_tags
from streamlit_ace import st_ace
from pathlib import Path
import yaml


def get_input_element(t: str, v, k: str):
    match v:
        case bool(x):
            return st.checkbox(label=f"{t}", value=x, key=k)
        case str(x):
            return st.text_input(label=f"{t}", value=x, key=k)
        case int(x):
            return st.number_input(label=f"{t}", value=x, key=k)
        case float(x) if "e" in str(x).lower():
            return st.text_input(label=f"{t}", value=x, key=k)
        case float(x):
            return st.number_input(
                label=f"{t}",
                value=x,
                key=k,
                step=10 ** -len(str(x).split(".")[-1]),  # infer significant decimals
                format="%f",
            )
        case list(x):
            return st_tags(
                label=f"{t}",
                value=x,
                key=k,
            )


def get_nested_tabs(config: dict, parent_key: str = ""):
    """Iteratively creates nested Streamlit tabs from a dictionary structure and replaces endpoint values (leaf nodes) from the dictionary with type specific streamlit-inputs.

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


def config_editor(dir_path, config_viewer):
    # handle config
    conf_path = Path(dir_path) / "config" / "config.yaml"
    if not conf_path.exists():
        st.error("No config file found!")
    else:
        match config_viewer:
            case x if x == "Form":
                config = load_yaml(conf_path.read_text())
                get_nested_tabs(config)
                config = yaml.dump(config, sort_keys=False)
            case x if x == "Text Editor":
                config = st_ace(conf_path.read_text(), language="yaml")
        with open(conf_path, "w") as f:
            f.write(config)
