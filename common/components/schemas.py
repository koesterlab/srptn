import pandas as pd


def get_property_type(schema):
    if schema.get("properties"):
        prop_key = "properties"
    elif schema.get("patternProperties"):
        prop_key = "patternProperties"
    return prop_key


def infer_schema(config):
    schema = {"type": "object", "properties": {}}
    for key, value in config.items():
        if isinstance(value, dict):
            schema["properties"][key] = infer_schema(value)
        else:
            schema["properties"][key] = infer_type(value)
    return schema


def infer_type(value):
    match value:
        case value if isinstance(value, pd.Series):
            value_schema = {"type": "array", "items": infer_type(value[0])}
        case list(value):
            value_schema = {"type": "array", "items": infer_type(value[0])}
        case bool(value):
            value_schema = {"type": "boolean"}
        case int(value):
            value_schema = {"type": "integer"}
        case float(value):
            value_schema = {"type": "number"}
        case str(value):
            value_schema = {"type": "string"}
        case value if value == None:
            value_schema = {"type": "missing"}
    return value_schema


def update_schema(schema, config):
    prop_key = get_property_type(schema)
    items = []
    for key, value in config.items():
        if isinstance(value, dict):  # check for leaf nodes = endpoints
            items.append((key, value))
        elif key not in schema.get(prop_key).keys():
            print(f'Category "{key}" found in config that has no entry in the schema!')
            schema.get(prop_key)[key] = infer_type(value)
    if items:
        for key, value in items:
            if prop_key == "patternProperties":
                # assert re.search(list(schema.get(prop_key).keys())[0], key) # TODO: Proper Matching
                key = list(schema.get(prop_key).keys())[0]
            new_schema = schema.get(prop_key).get(key)
            if new_schema == None:
                print(
                    f'Category "{key}" found in config that has no entry in the schema!'
                )
                schema.get(prop_key)[key] = infer_schema(config.get(key))
                new_schema = schema.get(prop_key).get(key)
            update_schema(new_schema, value)
    return schema
