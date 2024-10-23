import polars as pl
import streamlit as st
from humanfriendly import format_size


def file_browser(files: pl.DataFrame):
    """Display a file browser with file names and formatted sizes.

    :param files: A DataFrame containing file metadata, including columns for "name" and "size".
    """
    files = files.with_columns(
        [
            pl.col("name"),
            pl.col("size")
            .map_elements(format_size, return_dtype=pl.Utf8)
            .alias("size"),
        ]
    )

    st.dataframe(files)
