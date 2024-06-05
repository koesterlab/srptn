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
    state = "state" + key
    if state not in st.session_state:
        st.session_state[state] = False
    st.button(label, key=unique_key, on_click=toggle, args=(state,))
    return st.session_state[state]
