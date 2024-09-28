import io
from dataclasses import dataclass

import polars as pl
import streamlit as st

from common.components.files import file_browser
from common.data import Address, DataStore, Entity, FileType


@dataclass
class Dataset(Entity):
    sheet: pl.DataFrame | None
    data_files: list[io.BytesIO] | None = None
    meta_files: list[io.BytesIO] | None = None
    _data_store: DataStore | None = None

    def show(self):
        st.header(self.address, divider=True)
        st.markdown(self.desc)
        if self.sheet is not None:
            st.subheader("Sample Sheet")
            st.dataframe(self.sheet)

        meta_files = self.list_files(FileType.META)
        if not meta_files.is_empty:
            st.subheader("Meta Files")
            for name in meta_files["name"]:
                st.download_button(
                    name,
                    self._data_store.load_file(self.address, name, FileType.META),
                    file_name=name,
                )

        files = self.list_files(FileType.DATA)

        st.subheader("Files")
        file_browser(files)

    @classmethod
    def load(cls, data_store: DataStore, address: Address):
        sheet_name = "sheet"
        if data_store.has_sheet(address, sheet_name):
            sheet = data_store.load_sheet(address, sheet_name)
        else:
            sheet = None

        return cls(
            address, data_store.load_desc(address), sheet, _data_store=data_store
        )

    def store(self, data_store: DataStore):
        data_store.clean(self.address)
        data_store.store_desc(self.address, self.desc)
        data_store.store_sheet(self.address, self.sheet, "sheet")
        for file in self.data_files:
            data_store.store_file(
                self.address, file, file.name, file_type=FileType.DATA
            )
        for file in self.meta_files:
            data_store.store_file(
                self.address, file, file.name, file_type=FileType.META
            )

    def list_files(self, file_type: FileType):
        return self._data_store.list_files(self.address, file_type=file_type)
