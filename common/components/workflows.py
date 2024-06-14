from pathlib import Path
import tempfile
from typing import Optional
import streamlit as st
from streamlit_ace import st_ace
from snakedeploy.deploy import WorkflowDeployer

from common.data.entities.workflow import Workflow
from common.components.config_editor import config_editor
from common.components.ui_components import persistend_text_input


st.cache_data
def workflow_selector():
    """
    Create workflow selector widget in Streamlit with persistent text inputs.

    Returns
    -------
    Workflow or None
        The selected workflow or None if the input is incomplete.
    """
    url = persistend_text_input(
        "Workflow repository URL (e.g. https://github.com/snakemake-workflows/rna-seq-kallisto-sleuth)",
        "workflow-url",
    )

    tag = persistend_text_input(
        "Workflow repository tag (optional)",
        "workflow-tag",
    )

    branch = persistend_text_input(
        "Workflow repository branch (optional)",
        "workflow-branch",
    )

    if url and (tag or branch):
        return Workflow(url=url, tag=tag, branch=branch)
    else:
        st.info("Please provide a workflow URL and a tag or branch")


def workflow_editor(workflow: Workflow) -> tempfile.TemporaryDirectory:
    """
    Create and edit workflow configuration.

    Parameters
    ----------
    workflow : Workflow
        The workflow object containing URL, tag, and branch information.

    Returns
    -------
    tempfile.TemporaryDirectory
        The temporary directory where the workflow is deployed.
    """
    tmpdir = tempfile.TemporaryDirectory()
    tmpdir_path = Path(tmpdir.name)

    with WorkflowDeployer(
        workflow.url, tmpdir_path, tag=workflow.tag, branch=workflow.branch
    ) as wd:
        wd.deploy(None)

        st.session_state["workflow_config-dir_path"] = tmpdir_path
        conf_path = tmpdir_path / "config" / "config.yaml"
        config_viewer = st.radio(
            "Configuration editor mode",
            ["Form", "Text Editor"],
            horizontal=True,
        )
        if not conf_path.exists():
            st.error("No config file found!")
        else:
            st.divider()
            if config_viewer == "Form":
                config = config_editor(conf_path, wd)
            else:
                config = st_ace(conf_path.read_text(), language="yaml")
            with open(conf_path, "w") as f:
                f.write(config)
    return tmpdir
