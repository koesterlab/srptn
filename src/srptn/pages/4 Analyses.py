from srptn.common.components.entities import entity_browser
from srptn.common.data.fs import FSDataStore

owner = "koesterlab"
data = FSDataStore()

entity_browser(data, "analysis", owner)
