from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List

import pandas as pd
import yaml
import streamlit as st

from common.data import Address, DataStore, Entity, FileType



@dataclass
class Analysis(Entity):

    def show(self):
        st.header(self.address, divider=True)
        st.markdown(self.desc)

        # TODO input elements for config

        for name, sheet in self.sheets.items():
            st.caption(name)
            st.data_editor(sheet)

    @classmethod
    def load(cls, data_store: DataStore, address: Address):
        desc = data_store.load_desc(address)
        sheets = {f.name: pd.read_parquet(data_store.load_file(address, f.name, FileType.META)) for f in data_store.list_files(address, FileType.META).itertuples() if f.endswith(".parquet")}
        config = yaml.load(data_store.load_file(address, "config.yaml", FileType.META), Loader=yaml.SafeLoader)

        return cls(
            address, desc, sheets, config
        )

    def store(self, data_store: DataStore, tmp_deployment: TemporaryDirectory):
        data_store.clean(self.address)
        data_store.store_desc(self.address, self.desc)
        for path_obj in Path(tmp_deployment.name).rglob("*"):
            if path_obj.is_file():
                data_store.store_file(self.address, open(path_obj), str(path_obj), FileType.DATA)