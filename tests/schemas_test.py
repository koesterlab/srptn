from pathlib import Path

from common.components import schemas
from common.components.config_editor import load_yaml


def test_update_schema():
    with Path("testdata/config.yaml").open("r") as f:
        config = load_yaml(f)
    with Path("testdata/config.schema.yaml").open("r") as f:
        schema = load_yaml(f)
    updated_schema = schemas.update_schema(schema, config)
    with Path("testdata/config.schema.updated.yaml").open("r") as f:
        manual_updated_schema = load_yaml(f)
    assert updated_schema == manual_updated_schema


def test_infer_schema():
    with Path("testdata/config.yaml").open("r") as f:
        config = load_yaml(f)
    infered_schema = schemas.infer_schema(config)
    with Path("testdata/config.schema.infered.yaml").open("r") as f:
        manual_infered_schema = load_yaml(f)
    assert infered_schema == manual_infered_schema
