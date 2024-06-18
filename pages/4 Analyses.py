from common.components.entities import entity_browser
from common.data.entities.analysis import Analysis

from common.data.fs import FSDataStore


owner = "koesterlab"
data = FSDataStore()

entity_browser(data, Analysis, owner)
