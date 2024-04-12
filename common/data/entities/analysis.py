from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List

import pandas as pd
import yaml
import streamlit as st

from common.data import Address, DataStore, Entity, FileType
from common.data.entities.dataset import Dataset
from common.data.entities.workflow import Workflow


@dataclass
class Analysis(Entity):
    datasets: List[Dataset]
    workflow: Workflow

    def show(self):
        st.header(self.address, divider=True)
        st.markdown(self.desc)

    @classmethod
    def load(cls, data_store: DataStore, address: Address):
        desc = data_store.load_desc(address)
        sheets = {
            f.name: pd.read_parquet(
                data_store.load_file(address, f.name, FileType.DATA)
            )
            for f in data_store.list_files(address, FileType.META).itertuples()
            if f.endswith(".parquet")
        }
        if data_store.has_file(address, "config.yaml", FileType.META):
            config = yaml.load(
                data_store.load_file(address, "config.yaml", FileType.DATA),
                Loader=yaml.SafeLoader,
            )
        else:
            config = None

        return cls(address, desc, sheets, config)

    def store(self, data_store: DataStore, tmp_deployment_path: Path):
        data_store.clean(self.address)
        data_store.store_desc(self.address, self.desc)
        for path_obj in tmp_deployment_path.rglob("*"):
            if path_obj.is_file():
                data_store.store_file(
                    self.address,
                    open(path_obj, "br"),
                    str(path_obj.relative_to(tmp_deployment_path)),
                    FileType.DATA,
                )
