import streamlit as st
from streamlit_ace import st_ace

input_files = st.multiselect(
    "Input files",
    [
        "results/normalized_gene_expressions.csv",
        "results/diffexp_genes.csv",
    ],
)

output_file = st.text_input("Output file")


col1, col2 = st.columns(2)

with col1:
    st.chat_input(placeholder="Describe an analysis step...")

with col2:
    st_ace("", language="python")
