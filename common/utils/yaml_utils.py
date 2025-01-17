import yaml
import re


class CustomSafeLoader(yaml.SafeLoader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_constructor("tag:yaml.org,2002:float", self.scientificfloat_as_string)

    def scientificfloat_as_string(self, _, node):
        value = self.construct_scalar(node)
        # Check if the value looks like a float in scientific notation
        if re.match(r"^\d+(\.\d+)?[eE][-+]?\d+$", value):
            return value
        return float(value)


class CustomSafeDumper(yaml.SafeDumper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_representer(str, self.scientificfloat_from_string_as_float)

    def scientificfloat_from_string_as_float(self, _, value):
        if re.match(r"^\d+(\.\d+)?[eE][-+]?\d+scn$", value):
            return self.represent_scalar(
                "tag:yaml.org,2002:float", value[:-3]
            )  # Represent as float directly
        return self.represent_scalar("tag:yaml.org,2002:str", value)
