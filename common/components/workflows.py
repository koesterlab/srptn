import tempfile
from pathlib import Path

import streamlit as st
from snakedeploy.deploy import WorkflowDeployer

from common.components.config_editor import ace_config_editor, config_editor
from common.components.ui_components import persistend_text_input
from common.data.entities.workflow import Workflow


def workflow_selector() -> Workflow | None:
    """
    Create workflow selector widget in Streamlit with persistent text inputs.

    Returns
    -------
    Workflow or None
        The selected workflow or None if the input is incomplete.
    """

    if "workflow-url" in st.session_state:
        changed = [
            st.session_state["workflow-url"],
            st.session_state["workflow-tag"],
            st.session_state["workflow-branch"],
        ]
    else:
        changed = [""] * 3

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

    # upon change of any of the inputs above -> clear session_state of the config
    if url != changed[0] or tag != changed[1] or branch != changed[2]:
        for key in st.session_state.keys():
            if key.startswith("workflow_config-"):
                del st.session_state[key]

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
            st.stop()
        st.divider()
        if config_viewer == "Form":
            config = config_editor(conf_path, wd)
        else:
            config = ace_config_editor(conf_path, wd)
            pass
        with open(conf_path, "w") as f:
            f.write(config)
    return tmpdir
