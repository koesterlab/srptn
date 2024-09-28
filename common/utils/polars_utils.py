from pathlib import Path

import polars as pl
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile


def enforce_typing(data: pl.DataFrame, schema: dict) -> pl.DataFrame:
    """
    Enforce data types of a polars DataFrame based on a provided schema.

    Parameters
    ----------
    data : polars.DataFrame
        The input DataFrame whose columns need to be typed according to the schema.
    schema : dict
        A dictionary schema, which contains column names and their corresponding types.

    Returns
    -------
    polars.DataFrame
        The DataFrame with columns cast to the specified types as per the schema.

    Raises
    ------
    polars.InvalidOperationError
        If a type conversion fails, an error is displayed, and the program stops.
    """
    for field, field_info in schema.get("properties", {}).items():
        match field_info["type"]:
            case typing if typing == "string":
                field_type = str
            case typing if typing == "number":
                field_type = float if "." in str(data.first(field)) else int
        try:
            # Cast the column to the specified type
            data = data.with_columns(pl.col(field).cast(field_type))
            padding_value = get_type_specific_default(data[field].dtype)
            data = data.with_columns(pl.col(field).fill_null(padding_value))
        except pl.InvalidOperationError:
            st.error(
                f"Failed to translate column '{field}' to match type '{field_type}'"
            )
            st.stop()
    return data


def get_type_specific_default(dtype: pl.datatypes.DataType):
    """
    Return the appropriate padding value based on the column's data type.

    Parameters
    ----------
    dtype : polars.datatypes.DataType
        The Polars data type of the column.

    Returns
    -------
    default_value : str, float, or int
        Returns:
        - `""` if the column is of type `pl.Utf8` (string).
        - `nan` if the column is of type `pl.Float64` (float).
        - `0` if the column is of type `pl.Int64` (integer).
    """
    if dtype == pl.Utf8:
        return ""
    if dtype == pl.Float64:
        return float("nan")
    if dtype == pl.Int64:
        return 0
    return None  # Default case of polars for missing values


def load_data_table(file: UploadedFile | Path, source: str = "file") -> pl.DataFrame:
    """
    Load a data table from an uploaded file or a file path based on the source.

    Parameters
    ----------
    file : UploadedFile or Path
        The uploaded file or file path to load the data from.
    source : str
        The source of the file - either 'upload' or 'file'. Default is 'file'.

    Returns
    -------
    polars.DataFrame
        The loaded data table as a Polars DataFrame.
    """

    def read_data(file, file_type):
        if file_type in ["text/tab-separated-values", ".tsv"]:
            return pl.read_csv(file, separator="\t")
        if file_type in ["text/csv", ".csv"]:
            return pl.read_csv(file)
        if file_type in [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xlsx",
        ]:
            return pl.read_excel(file)
        st.error(
            f"Unsupported file format for sample sheet {file.name}, Use: TSV, CSV or XLSX"
        )
        st.stop()

    file_type = file.type if source == "upload" else file.suffix
    if source == "upload":
        return read_data(file, file_type)
    else:
        try:
            return read_data(file, file_type)
        except FileNotFoundError:
            st.error(f"File {file.name} does not exist")
            return None
