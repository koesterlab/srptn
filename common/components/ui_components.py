import streamlit as st


def toggle_button(label: str, key: str) -> bool:
    """
    Minimal wrapper around st.button that mimics a toggle.

    Args:
        label : str
            Button label
        key : str
            Button key

    Returns:
        bool: state
    """

    def toggle(state):
        st.session_state[state] = not st.session_state[state]

    unique_key = f"{key}-{label.lower()}"
    state = key + "-state"
    if state not in st.session_state:
        st.session_state[state] = False
    st.button(label, key=unique_key, on_click=toggle, args=(state,))
    return st.session_state[state]


def persistend_text_input(label: str, key: str) -> str:
    """
    Minimal wrapper around st.text_input that stores its value in the session_state to persist through page changes.

    Parameters
    ----------
    label : str
        The label for the text input widget.
    key : str
        The key to store the text input value in Streamlit's session state.

    Returns
    -------
    str
        The current value of the text input widget.
    """
    if key not in st.session_state:
        st.session_state[key] = ""
    value = st.text_input(
        label,
        st.session_state[key],
    )
    if value != st.session_state[key]:
        st.session_state[key] = value
    return value


def persistend_text_area(label: str, key: str) -> str:
    """
    Create a persistent text area widget in Streamlit.

    Parameters
    ----------
    label : str
        The label for the text area widget.
    key : str
        The key to store the text area value in Streamlit's session state.

    Returns
    -------
    str
        The current value of the text area widget.
    """
    if key not in st.session_state:
        st.session_state[key] = ""
    value = st.text_area(
        label,
        st.session_state[key],
    )
    if value != st.session_state[key]:
        st.session_state[key] = value
    return value
