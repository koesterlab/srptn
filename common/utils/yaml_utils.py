import re

import yaml


class CustomSafeLoader(yaml.SafeLoader):
    """Custom YAML loader."""

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        """Initialize the custom YAML loader."""
        super().__init__(*args, **kwargs)
        self.add_constructor("tag:yaml.org,2002:float", self.scientificfloat_as_string)

    def scientificfloat_as_string(
        self,
        _: yaml.Loader,
        node: yaml.nodes.Node,
    ) -> str | float:
        """Load scientific floats as strings if in scientific notation."""
        value = self.construct_scalar(node)
        # Check if the value looks like a float in scientific notation
        if re.match(r"^\d+(\.\d+)?[eE][-+]?\d+$", value):
            return value
        return float(value)


class CustomSafeDumper(yaml.SafeDumper):
    """Custom YAML dumper."""

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        """Initialize the custom YAML dumper."""
        super().__init__(*args, **kwargs)
        self.add_representer(str, self.scientificfloat_from_string_as_float)

    def scientificfloat_from_string_as_float(
        self,
        _: yaml.Dumper,
        value: str,
    ) -> yaml.nodes.ScalarNode:
        """Dump scientific float from a string to yaml as float."""
        if re.match(r"^\d+(\.\d+)?[eE][-+]?\d+scn$", value):
            return self.represent_scalar(
                "tag:yaml.org,2002:float",
                value[:-3],  # Remove the custom 'scn' suffix and represent as float
            )
        return self.represent_scalar("tag:yaml.org,2002:str", value)
