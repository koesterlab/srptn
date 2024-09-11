from pathlib import Path
from dataclasses import dataclass, field
from typing import List
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Config:
    singleton: Config = field(init=False, default=None)


    workdir: Path

    @classmethod
    def __new__(cls):
        if cls.singleton is None:
            cls.singleton = Config.from_json(os.environ.get("SRPTN_CONFIG"))
        return cls.singleton
