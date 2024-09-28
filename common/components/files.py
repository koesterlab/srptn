import polars as pl
import streamlit as st
from humanfriendly import format_size


def file_browser(files: pl.DataFrame):
    files = files.with_columns(
        [
            pl.col("name"),
            pl.col("size")
            .map_elements(format_size, return_dtype=pl.Utf8)
            .alias("size"),
        ]
    )

    st.dataframe(files)
