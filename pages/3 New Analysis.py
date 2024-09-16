from pathlib import Path

import streamlit as st

from common.components.categories import category_editor
from common.components.descriptions import desc_editor
from common.components.entities import entity_selector
from common.components.ui_components import persistend_text_input
from common.components.workflows import workflow_editor, workflow_selector
from common.data import Address
from common.data.entities.analysis import Analysis
from common.data.entities.dataset import Dataset
from common.data.fs import FSDataStore

owner = "koesterlab"
data_store = FSDataStore()

categories = category_editor()
analysis_name = persistend_text_input("Analysis name", "workflow-meta-name")

address = Address(owner, Analysis, categories=categories, name=analysis_name)
if data_store.has_entity(address):
    st.error(f"Analysis {address} already exists")
    st.stop()

desc = desc_editor("workflow-meta")

datasets = entity_selector(data_store, Dataset, "workflow-meta-datasets")

workflow = workflow_selector()

if workflow is not None:
    with workflow_editor(workflow) as tmp_deployment:
        store = st.button("Store", disabled=(not desc) | (not analysis_name))
        if store:
            if st.session_state.get("workflow-config-form-valid"):
                valid = True
                invalid_fields = [
                    key
                    for key, value in st.session_state.get(
                        "workflow-config-form-valid"
                    ).items()
                    if value is False
                ]
                if invalid_fields:
                    invalid_fields_str = ", ".join(invalid_fields)
                    st.error(
                        f'The following field{"s are" if len(invalid_fields) > 1 else " is"} incorrect: {invalid_fields_str}'
                    )
                    valid = False
            if valid:
                Analysis(
                    address=address,
                    desc=desc,
                    datasets=datasets,
                    workflow=workflow,
                ).store(data_store, Path(tmp_deployment))
                st.success(f"Stored analysis {address}")
