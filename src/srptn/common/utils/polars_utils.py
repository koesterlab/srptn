from pathlib import Path

import polars as pl
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile


def enforce_typing(data: pl.DataFrame, schema: dict) -> pl.DataFrame:
    """Enforces data types of a Polars DataFrame based on a provided schema.

    :param data: The input DataFrame whose columns need to be typed according
        to the schema.
    :param schema: A dictionary schema containing column names and their
        corresponding types.
    :returns: The DataFrame with columns cast to the specified types as per the schema.
    :raises polars.InvalidOperationError: If a type conversion fails.
    """
    for field, field_info in schema.get("properties", {}).items():
        match field_info["type"]:
            case typing if typing == "string":
                field_type = str
            case typing if typing == "number":
                field_type = float if "." in str(data.select(pl.first(field))) else int
        try:
            # Cast the column to the specified type
            data = data.with_columns(pl.col(field).cast(field_type))
            padding_value = get_type_specific_default(data[field].dtype)
            data = data.with_columns(pl.col(field).fill_null(padding_value))
        except pl.InvalidOperationError:
            st.error(
                f"Failed to translate column '{field}' to match type '{field_type}'",
            )
            st.stop()
    return data


def get_type_specific_default(dtype: pl.datatypes.DataType) -> str | float | int | None:
    """Return the appropriate padding value based on the column's data type.

    :param dtype: The Polars data type of the column.
    :returns: The padding value based on the type.
        - `""` for string columns.
        - `nan` for float columns.
        - `0` for integer columns.
        - None for unsupported data types.
    """
    if dtype in ("String", pl.Utf8):
        return ""
    if dtype in ("Float64", pl.Float64):
        return float("nan")
    if dtype in ("Int64", pl.Int64):
        return 0
    return None


def load_data_table(
    file: UploadedFile | Path,
    source: str = "file",
) -> pl.DataFrame | None:
    """Load a data table from an uploaded file or a file path based on the source.

    :param file: The uploaded file or file path to load the data from.
    :param source: The source of the file - either 'upload' or 'file'.
        Defaults to 'file'.
    :returns: The loaded data table as a Polars DataFrame.
    :raises FileNotFoundError: If the file does not exist when source is 'file'.
    :raises StreamlitError: For unsupported file formats or missing files.
    """

    def read_data(file: UploadedFile | Path, file_type: str) -> pl.DataFrame | None:
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
            f"""Unsupported file format for sample sheet {file.name},
             Use: TSV, CSV or XLSX""",
        )
        st.stop()
        return None

    file_type = file.type if source == "upload" else file.suffix
    if source == "upload":
        return read_data(file, file_type)
    try:
        return read_data(file, file_type)
    except FileNotFoundError:
        st.error(f"File {file.name} does not exist")
        return None


def merge_dataframes(
    data_modified: pl.DataFrame,
    columns_to_add: pl.DataFrame,
    selected: str,
) -> pl.DataFrame:
    """Merge new columns into the existing dataframe and return the updated dataframe."""
    columns_to_add_combined = pl.concat(columns_to_add, how="horizontal").with_columns(
        pl.lit(selected, dtype=pl.String).alias("datasetid"),
    )

    # Ensure all columns match the order of the modified dataframe
    columns_to_add_combined = columns_to_add_combined.with_columns(
        [
            pl.Series(
                col,
                [get_type_specific_default(data_modified[col].dtype)]
                * len(columns_to_add_combined),
            )
            for col in data_modified.columns
            if col not in columns_to_add_combined.columns
        ],
    ).select(data_modified.columns)

    return pl.concat([data_modified, columns_to_add_combined], how="vertical")


def save_data_table(data: pl.DataFrame, path: Path) -> None:
    """Save a data table to a file based on the file extension.

    :param data: The Polars DataFrame to save.
    :param path: The file path where the data should be saved.
    :raises ValueError: If the file extension is unsupported.
    :raises IOError: If there is an issue with file writing
        (e.g., permissions or disk space).
    :raises polars.exceptions.PolarsError: For Polars-specific errors.
    """
    file_extension = path.suffix
    try:
        if file_extension == ".tsv":
            data.write_csv(path, separator="\t")
        elif file_extension == ".csv":
            data.write_csv(path)
        elif file_extension == ".xlsx":
            data.write_excel(path)
        else:
            raise ValueError(
                f"""Unsupported file format: {file_extension}.
                 Supported formats are: TSV, CSV, XLSX""",
            )
    except OSError as os_error:
        raise OSError(
            f"File writing failed due to an I/O error: {os_error}",
        ) from os_error
    except pl.exceptions.PolarsError as polars_error:
        raise pl.exceptions.PolarsError(
            f"Polars encountered an error: {polars_error}",
        ) from polars_error
