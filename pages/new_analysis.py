from pathlib import Path
from common.components.descriptions import desc_editor
from common.components.categories import category_editor
from common.components.entities import entity_selector
from common.components.workflows import workflow_editor, workflow_selector
from common.components.config_editor import config_editor

from common.data import Address
from common.data.entities.analysis import Analysis
from common.data.fs import FSDataStore
from common.data.entities.dataset import Dataset
import streamlit as st

owner = "koesterlab"
data_store = FSDataStore()

categories = category_editor()
analysis_name = st.text_input("Analysis name")

address = Address(owner, Analysis, categories=categories, name=analysis_name)
if data_store.has_entity(address):
    st.error(f"Analysis {address} already exists")
    st.stop()

desc = desc_editor()

datasets = entity_selector(data_store, Dataset)

workflow = workflow_selector()

if workflow is not None:
    with workflow_editor(workflow) as tmp_deployment:
        config_viewer = st.selectbox(
            "How would you like to edit the workflow configuration file",
            ("Form", "Text Editor"),
        )
        with st.form("config-editor-form"):
            config_editor(tmp_deployment, config_viewer)
            store = st.form_submit_button(
                "Store", disabled=(not desc) | (not analysis_name)
            )
            if store:
                Analysis(
                    address=address,
                    desc=desc,
                    datasets=datasets,
                    workflow=workflow,
                ).store(data_store, Path(tmp_deployment))
                st.success(f"Stored analysis {address}")
