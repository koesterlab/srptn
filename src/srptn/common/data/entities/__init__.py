from enum import Enum

from srptn.common.data.entities.analysis import Analysis
from srptn.common.data.entities.dataset import Dataset


class EntityType(Enum):
    """Enum representing different entity types."""

    dataset = Dataset
    analysis = Analysis
