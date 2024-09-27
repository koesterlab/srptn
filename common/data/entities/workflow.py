from dataclasses import dataclass


@dataclass
class Workflow:
    url: str
    tag: str | None
    branch: str | None
