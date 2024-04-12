from dataclasses import dataclass
from typing import Optional


@dataclass
class Workflow:
    url: str
    tag: Optional[str]
    branch: Optional[str]
