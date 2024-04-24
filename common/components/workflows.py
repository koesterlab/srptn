from pathlib import Path
import tempfile
from typing import Optional
import streamlit as st
from streamlit_ace import st_ace
from snakedeploy.deploy import WorkflowDeployer
import yaml

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

    with WorkflowDeployer(workflow.url, tmpdir_path, tag=workflow.tag, branch=workflow.branch) as wd:
        wd.deploy(None)

        # handle config
        conf_path = tmpdir_path / "config" / "config.yaml"
        if conf_path.exists():
            config_schema = wd.get_json_schema("config")

            # TODO get schemas for other items as they occur in the config file 
            # (e.g. samples.tsv, units.tsv).
            # Assumption is that the schemas are named the same by convention 
            # (therefore e.g. calling wd.get_json_schema("samples")).
            # This retrieval is needed when the editor for the tables is built.

            config = st_ace(conf_path.read_text(), language="yaml")
            try:
                yaml.load(config, Loader=yaml.SafeLoader)
            except yaml.YAMLError as e:
                st.error(f"Error parsing config YAML: {e}")
                st.stop()
            with open(conf_path, "w") as f:
                f.write(config)

    # handle sample sheets (TODO)
    return tmpdir
