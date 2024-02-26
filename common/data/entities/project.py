from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd
import yaml
import streamlit as st

from common.data import Address, DataStore, Entity, FileType



@dataclass
class Project(Entity):
    sheets: Dict[str, pd.DataFrame]
    config: Dict[Any, Any]

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
