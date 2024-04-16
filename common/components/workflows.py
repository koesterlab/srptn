from pathlib import Path
import tempfile
from typing import Optional
import streamlit as st
from snakedeploy.deploy import deploy

from common.data.entities.workflow import Workflow


def workflow_selector():
    url = st.text_input(
        "Workflow repository URL (e.g. https://github.com/snakemake-workflows/rna-seq-kallisto-sleuth)"
    )
    tag = st.text_input("Workflow repository tag (optional)")
    branch = st.text_input("Workflow repository branch (optional)")

    if url and (tag or branch):
        return Workflow(url=url, tag=tag, branch=branch)
    else:
        st.info("Please provide a workflow URL and a tag or branch")


def workflow_editor(workflow: Workflow) -> tempfile.TemporaryDirectory:
    tmpdir = tempfile.TemporaryDirectory()
    tmpdir_path = Path(tmpdir.name)

    deploy(
        workflow.url,
        None,
        tag=workflow.tag,
        branch=workflow.branch,
        dest_path=tmpdir_path,
    )

    # handle sample sheets (TODO)
    return tmpdir
