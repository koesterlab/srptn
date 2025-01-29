import streamlit as st


def update(key: str) -> None:
    """Update session state to facility persistent behavior."""
    st.session_state[f"{key}-value"] = st.session_state[key]


def persistent_multiselect(label: str, names: list, key: str) -> list:
    """Create a multiselect widget in Streamlit that persists its selection state across page reloads.

    :param label: The label for the multiselect widget.
    :param names: A list of options to display in the multiselect.
    :param key: A unique key to store the selection state in Streamlit's session state.
    :return: A list of selected options.
    """
    if f"{key}-value" not in st.session_state:
        st.session_state[f"{key}-value"] = []

    return st.multiselect(
        label,
        names,
        st.session_state[f"{key}-value"],
        key=key,
        on_change=update,
        args=(key,),
    )


def persistent_text_input(label: str, key: str, placeholder: str = "") -> str:
    """Create a persistent text input widget in Streamlit.

    :param label: The label for the text input widget.
    :param key: A unique key to store the text input value in Streamlit's session state.
    :param placeholder: Placeholder text to display in the text input widget (optional).
    :return: The current value of the text input widget.
    """
    if f"{key}-value" not in st.session_state:
        st.session_state[f"{key}-value"] = ""

    return st.text_input(
        label,
        value=st.session_state[f"{key}-value"],
        key=key,
        on_change=update,
        args=(key,),
        placeholder=placeholder,
    )


def persistent_text_area(
    label: str,
    key: str,
    placeholder: str = "",
    helpstr: str = "",
) -> str:
    """Create a persistent text area widget in Streamlit.

    :param label: The label for the text area widget.
    :param key: A unique key to store the text area value in Streamlit's session state.
    :param placeholder: Placeholder text to display in the text area widget (optional).
    :param helpstr: Help text to display alongside the text area widget (optional).
    :return: The current value of the text area widget.
    """
    if f"{key}-value" not in st.session_state:
        st.session_state[f"{key}-value"] = ""

    return st.text_area(
        label,
        value=st.session_state[f"{key}-value"],
        key=key,
        on_change=update,
        args=(key,),
        placeholder=placeholder,
        help=helpstr,
    )


def toggle_button(label: str, key: str, icon: str | None = None) -> bool:
    """Create a toggle button in Streamlit.

    :param label: The label for the button.
    :param key: A unique key to store the toggle state in Streamlit's session state.
    :param icon: An optional icon to display alongside the button.
    :return: The current toggle state (True or False).
    """

    def toggle(state: str) -> None:
        st.session_state[state] = not st.session_state[state]

    unique_key = f"{key}-{label.lower()}"
    state = f"{key}-state"
    if state not in st.session_state:
        st.session_state[state] = False
    st.button(
        label,
        key=unique_key,
        on_click=toggle,
        args=(state,),
        icon=icon,
    )
    return st.session_state[state]
