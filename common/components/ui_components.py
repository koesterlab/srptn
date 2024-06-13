import streamlit as st


def toggle_button(label: str, key: str):
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
    unique_key = label.lower() + key
    state = key + "-state"
    if state not in st.session_state:
        st.session_state[state] = False
    st.button(label, key=unique_key, on_click=toggle, args=(state,))
    return st.session_state[state]


def persistend_text_input(label: str, key: str):
    if key not in st.session_state:
        st.session_state[key] = ""
    value = st.text_input(
        label,
        st.session_state[key],
    )
    if value != st.session_state[key]:
        st.session_state[key] = value
    return value


def persistend_text_area(label: str, key: str):
    if key not in st.session_state:
        st.session_state[key] = ""
    value = st.text_area(
        label,
        st.session_state[key],
    )
    if value != st.session_state[key]:
        st.session_state[key] = value
    return value
