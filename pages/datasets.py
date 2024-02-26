
from common.components.entities import entity_browser
from common.data.entities.dataset import Dataset

from common.data.fs import FSDataStore


owner = "koesterlab"
data = FSDataStore()

entity_browser(data, Dataset, owner)