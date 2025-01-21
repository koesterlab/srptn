from pathlib import Path

import streamlit as st

from common.data import Address, DataStore


def log_selector(data_store: DataStore, address: Address) -> str | None:
    """Display a log file selection interface in a Streamlit application.

    :param data_store: The data store object used to retrieve workflow manager information.
    :param address: The address of the workflow manager whose logs are to be accessed.
    """
    from common.data.entities.analysis import WorkflowManager

    workflow_manager = WorkflowManager.load(data_store, address)
    log_path = workflow_manager.log_path
    if log_path:
        log_file_names = workflow_manager.get_log_names()
        log_file_name = Path(st.selectbox(label="Select Log", options=log_file_names))
        log_file = workflow_manager.get_log(log_file_name)
        with st.container(height=450):
            st.text(log_file)
    st.text("No Logs found.")
