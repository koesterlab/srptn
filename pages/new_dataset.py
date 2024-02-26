from pathlib import Path
import pandas as pd
from common.data import Address
from common.data.fs import FSDataStore
from common.data.entities.dataset import Dataset
import streamlit as st

owner = "koesterlab"
data_store = FSDataStore()

categories = []
while not categories or categories[-1]:
    categories.append(st.text_input("Category" if not categories else "Subcategory", key=f"category-{len(categories)}"))
dataset_name = st.text_input("Dataset name")

address = Address(owner, Dataset, categories=categories, name=dataset_name)
if data_store.has_entity(address):
    st.error(f"Dataset {address} already exists")
    st.stop()

col1, col2 = st.columns(2)

with col1:
    desc = st.text_area("Description (markdown format)")

with col2:
    st.caption("Preview")
    st.markdown(desc)

files = st.file_uploader("Files", accept_multiple_files=True)

multi_file = len(files) > 1

if multi_file:
    sheet = st.file_uploader("Sample Sheet")
else:
    sheet = None

if sheet:
    if sheet.name.endswith(".xlsx"):
        sheet = pd.read_excel(sheet, dtype=str)
    elif sheet.name.endswith(".csv"):
        sheet = pd.read_csv(sheet, sep=",", dtype=str)
    elif sheet.name.endswith(".tsv"):
        sheet = pd.read_csv(sheet, sep="\t", dtype=str)
    else:
        st.error(f"Unsupported file format for sample sheet: {Path(sheet.name).suffix}")
        st.stop()

    for name, col in sheet.items():
        sheet[name] = col.str.strip()

    st.text("Sample sheet")
    st.dataframe(sheet)

    for f in files:
        if not any(f.name in col.values for _, col in sheet.items()):
            st.error(f"Uploaded file {f.name} not found in sample sheet")
            st.stop()

meta_files = st.file_uploader("Metadata files", accept_multiple_files=True)

store = st.button("Store", disabled=not desc or not files or (multi_file and sheet is None))

if store:
    Dataset(
        address=address,
        desc=desc,
        sheet=sheet,
        data_files=files,
        meta_files=meta_files,
    ).store(data_store)
    st.success(f"Stored {len(files)} files in {address}")
