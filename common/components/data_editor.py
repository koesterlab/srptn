import streamlit as st
import pandas as pd

def data_editor(data, key, num_rows="fixed"):
    key = f"{key}_schema"
    schema = st.session_state[key] if key in st.session_state else pd.DataFrame({"column": [], "type": []}, dtype=str)
    schema = st.data_editor(schema, num_rows=num_rows, column_config={
        "type": st.column_config.SelectboxColumn(
            "column type",
            help="The type of the column",
            
            required=True,
        )
    })
    st.session_state[key] = schema
    return st.data_editor(data, num_rows=num_rows)