import streamlit as st
from streamlit_tags import st_tags


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


def config_editor(config, schema=0):
    get_nested_tabs(config)

    return config
