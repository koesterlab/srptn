from srptn.common.components.entities import entity_browser
from srptn.common.data.fs import FSDataStore

owner = "koesterlab"
data = FSDataStore()
entity_type = "dataset"

entity_browser(data, entity_type, owner)
