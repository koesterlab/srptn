import streamlit as st

from common.components.categories import category_editor
from common.components.descriptions import desc_editor
from common.components.entities import entity_selector
from common.components.ui_components import persistent_text_input
from common.components.workflows import workflow_editor, workflow_selector
from common.data import Address
from common.data.entities.analysis import Analysis, WorkflowManager
from common.data.entities.dataset import Dataset
from common.data.fs import FSDataStore

owner = "koesterlab"
data_store = FSDataStore()

categories = category_editor("workflow-meta")

analysis_name = persistent_text_input(
    "Analysis name",
    "workflow-meta-name",
    "Enter name",
)

address = Address(owner, Analysis, categories=categories, name=analysis_name)
if data_store.has_entity(address):
    st.error(f"Analysis {address} already exists")
    st.stop()

desc = desc_editor("workflow-meta")

datasets = entity_selector(data_store, Dataset, "workflow-meta-datasets")

if not categories or not analysis_name:
    st.stop()

workflow_manager = workflow_selector(address, data_store)


def store_analysis(
    address: Address,
    desc: str,
    datasets: list[Dataset],
    workflow_manager: WorkflowManager,
    data_store: data_store,
) -> None:
    """Store the analysis."""
    valid = True
    if st.session_state.get("workflow-config-form-valid"):
        invalid_fields = [
            key
            for key, value in st.session_state.get("workflow-config-form-valid").items()
            if value is False
        ]
        if invalid_fields:
            invalid_fields_str = ", ".join(invalid_fields)
            st.error(
                f"""The following field
                {"s are" if len(invalid_fields) > 1 else " is"}
                incorrect: {invalid_fields_str}""",
            )
            valid = False
    if valid:
        Analysis(
            address=address,
            desc=desc,
            datasets=datasets,
            workflow_manager=workflow_manager,
        ).store(data_store)
        st.success(f"Stored analysis {address}")


if workflow_manager is not None:
    workflow_editor(workflow_manager)
    st.button(
        "Store",
        disabled=(not desc) | (not analysis_name),
        on_click=store_analysis,
        args=(
            address,
            desc,
            datasets,
            workflow_manager,
            data_store,
        ),
    )
