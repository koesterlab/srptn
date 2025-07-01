import polars as pl
import streamlit as st

from srptn.common.components.categories import category_editor
from srptn.common.components.descriptions import desc_editor
from srptn.common.data import Address
from srptn.common.data.entities.dataset import Dataset
from srptn.common.data.fs import FSDataStore
from srptn.common.utils.polars_utils import load_data_table

owner = "koesterlab"
data_store = FSDataStore()

categories = category_editor("new_dataset-meta")
dataset_name = st.text_input("Dataset name")

address = Address(owner, Dataset, categories=categories, name=dataset_name)
if data_store.has_entity(address):
    st.error(f"Dataset {address} already exists")
    st.stop()

desc = desc_editor("new_dataset-meta")

files = st.file_uploader("Files", accept_multiple_files=True)
files_number = len(files) if files else 0
multi_file = files_number > 1
sheet = st.file_uploader("Sample Sheet") if multi_file else None
sheet_table = None

if sheet and files:
    sheet_table = load_data_table(sheet)

    sheet_table = sheet_table.with_columns([pl.col(pl.Utf8).str.strip_chars()])

    st.text("Sample sheet")
    st.dataframe(sheet_table)

    for f in files:
        if not sheet_table.select(pl.any_horizontal((pl.all() == f.name).any())).item():
            st.error(f"Uploaded file {f.name} not found in sample sheet")
            st.stop()

meta_files = st.file_uploader("Metadata files", accept_multiple_files=True)

store = st.button(
    "Store",
    disabled=not desc or not files or (multi_file and sheet is None),
)

if store:
    Dataset(
        address=address,
        desc=desc,
        sheet=sheet_table,
        data_files=files,
        meta_files=meta_files,
    ).store(data_store)
    st.success(f"Stored {files_number} files in {address}")
