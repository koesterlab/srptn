from pathlib import Path
from common.components.descriptions import desc_editor
from common.components.categories import category_editor
from common.components.entities import entity_selector
from common.components.workflows import workflow_editor, workflow_selector

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
        store = st.button("Store", disabled=(not desc) | (not analysis_name))
        if store: # TODO More elaborate reporting, f.e. input_names
            if st.session_state.get("valid_config_form"): 
                valid = not False in st.session_state["valid_config_form"].values()
            else:
                valid = True
            if valid:
                Analysis(
                    address=address,
                    desc=desc,
                    datasets=datasets,
                    workflow=workflow,
                ).store(data_store, Path(tmp_deployment))
                st.success(f"Stored analysis {address}")
            else:
                st.error("One or more of the required inputs are not present")
            
