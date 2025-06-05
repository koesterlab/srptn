import re
from math import isnan

import polars as pl
import streamlit as st


def get_nonan_index(value: pl.Series | list) -> int | None:
    """Find the index of the first non-NaN value in the list.

    :param value: A list of values to search for the first non-NaN value.
    :return: The index of the first non-NaN value in the list, or None if all values
    are NaN.
    """

    def isna(value: any) -> bool:
        return not value or (isinstance(value, float) and isnan(value))

    for idx, v in enumerate(value):
        if not isna(v):
            return idx
    return None


def get_property_type(schema: dict) -> str | None:
    """Determine the property type key in a schema dictionary.

    :param schema: A dictionary representing the schema.
    :return: The key of the property type in the schema, either "properties" or
    "patternProperties",
        or None if neither is found.
    :raises ValueError: If the schema structure is invalid.
    """
    if "properties" in schema:
        return "properties"
    if "patternProperties" in schema:
        return "patternProperties"
    raise ValueError(
        "Wrong schema structure, please use either properties or patternProperties",
    )
    return None


def infer_schema(config: dict) -> dict:
    """Infer a JSON schema from a configuration dictionary.

    :param config: The configuration dictionary to infer the schema from.
    :return: The inferred JSON schema.
    """
    schema = {"type": "object", "properties": {}}
    for key, value in config.items():
        if isinstance(value, dict):
            schema["properties"][key] = infer_schema(value)
        else:
            schema["properties"][key] = infer_type(value)
    return schema


def infer_type(value: pl.Series | list | bool | float | str | None) -> dict:
    """Infer the JSON schema type for a given value.

    :param value: The value for which to infer the type.
    :return: The inferred JSON schema type definition.
    """
    match value:
        case value if isinstance(value, pl.Series):
            if len(value) == 0:
                return {"type": "missing"}
            idx = get_nonan_index(value)
            value_schema = {
                "type": "array",
                "items": infer_type(value[idx])
                if idx is not None
                else {"type": "missing"},
            }
        case value if isinstance(value, list):
            idx = get_nonan_index(value)
            value_schema = {
                "type": "array",
                "items": infer_type(value[idx])
                if idx is not None
                else {"type": "missing"},
            }
        case bool(value):
            value_schema = {"type": "boolean"}
        case int(value):
            value_schema = {"type": "integer"}
        case float(value):
            value_schema = {"type": "number"}
        case str(value):
            value_schema = {"type": "string"}
        case value:
            value_schema = {"type": "missing"}
    return value_schema


def update_schema(schema: dict, config: dict) -> dict:
    """Update a JSON schema based on a config dictionary.

    :param schema: The existing JSON schema to be updated.
    :param config: The config dictionary used to update the schema.
    :return: The updated JSON schema.
    """
    prop_key = get_property_type(schema)
    items = []
    for key, value in config.items():
        if isinstance(value, dict):  # check for leaf nodes = endpoints
            items.append((key, value))
        elif key not in schema[prop_key]:
            schema[prop_key][key] = infer_type(value)
    if items:
        for key, value in items:
            if prop_key == "patternProperties":
                if not re.search(next(iter(schema[prop_key])), key):
                    st.error("Field name does not match schema.")
                updated_key = next(iter(schema[prop_key]))
            else:
                updated_key = key
            new_schema = schema[prop_key].get(updated_key)
            if new_schema is None:
                schema[prop_key][updated_key] = infer_schema(config[updated_key])
                new_schema = schema[prop_key][updated_key]
            update_schema(new_schema, value)
    return schema
