from pathlib import Path

import polars as pl
import pytest
import yaml

from common.components import schemas


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ([1.1, 1.7], 0),
        ([float("nan"), 1.1], 1),
        (["", "", "test"], 2),
        (["test"], 0),
        (pl.Series("test", ["", "test"], dtype=pl.String), 1),
    ],
)
def test_get_nonan_index(value, expected):
    assert schemas.get_nonan_index(value) == expected


def test_update_schema():
    with Path("testdata/config.yaml").open("r") as f:
        config = yaml.safe_load(f)
    with Path("testdata/config.schema.yaml").open("r") as f:
        schema = yaml.safe_load(f)
    updated_schema = schemas.update_schema(schema, config)
    with Path("testdata/config.schema.updated.yaml").open("r") as f:
        manual_updated_schema = yaml.safe_load(f)
    assert updated_schema == manual_updated_schema


def test_infer_schema():
    with Path("testdata/config.yaml").open("r") as f:
        config = yaml.safe_load(f)
    infered_schema = schemas.infer_schema(config)
    with Path("testdata/config.schema.infered.yaml").open("r") as f:
        manual_infered_schema = yaml.safe_load(f)
    assert infered_schema == manual_infered_schema


@pytest.mark.parametrize(
    ("value", "expected", "itemtype"),
    [
        ("", "string", ""),
        (False, "boolean", ""),
        (1.0, "number", ""),
        (1, "integer", ""),
        ([""], "array", "missing"),
        (["test"], "array", "string"),
        (pl.Series("test", [float("nan")]), "array", "missing"),
        (pl.Series("test", [float("nan"), 1.0]), "array", "number"),
    ],
)
def test_infer_type(value, expected, itemtype):
    typedict = schemas.infer_type(value)
    assert typedict.get("type") == expected
    if typedict.get("type") == "array":
        assert typedict.get("items", dict).get("type") == itemtype
