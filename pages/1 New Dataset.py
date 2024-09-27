import polars as pl
import streamlit as st
from common.components.categories import category_editor
from common.components.descriptions import desc_editor
from common.data import Address
from common.data.entities.dataset import Dataset
from common.data.fs import FSDataStore
from common.utils.polars_utils import load_data_table

owner = "koesterlab"
data_store = FSDataStore()

categories = category_editor()
dataset_name = st.text_input("Dataset name")

address = Address(owner, Dataset, categories=categories, name=dataset_name)
if data_store.has_entity(address):
    st.error(f"Dataset {address} already exists")
    st.stop()

desc = desc_editor("new_dataset-meta")

files = st.file_uploader("Files", accept_multiple_files=True)

multi_file = len(files) > 1

sheet = st.file_uploader("Sample Sheet") if multi_file else None

if sheet:
    sheet = load_data_table(sheet, "upload")

    sheet = sheet.select(
        [
            pl.col(name).str.strip_chars()
            if sheet[name].dtype == pl.Utf8
            else pl.col(name)
            for name in sheet.columns
        ]
    )

    st.text("Sample sheet")
    st.dataframe(sheet)

    for f in files:
        if not any(f.name in col.to_numpy() for _, col in sheet.to_dict().items()):
            st.error(f"Uploaded file {f.name} not found in sample sheet")
            st.stop()

meta_files = st.file_uploader("Metadata files", accept_multiple_files=True)

store = st.button(
    "Store", disabled=not desc or not files or (multi_file and sheet is None)
)

if store:
    Dataset(
        address=address,
        desc=desc,
        sheet=sheet,
        data_files=files,
        meta_files=meta_files,
    ).store(data_store)
    st.success(f"Stored {len(files)} files in {address}")
