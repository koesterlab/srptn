
from common.components.entities import entity_browser

from common.data.fs import FSDataStore


owner = "koesterlab"
data = FSDataStore()

entity_browser(data, "projects", owner)