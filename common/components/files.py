import pandas as pd
from humanfriendly import format_size
import streamlit as st

def file_browser(files: pd.DataFrame):
    files = files.copy()
    files["size"] = files["size"].apply(format_size)

    st.dataframe(files)