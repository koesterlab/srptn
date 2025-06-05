from srptn.common.components.entities import entity_browser
from srptn.common.data.entities.analysis import Analysis
from srptn.common.data.fs import FSDataStore

owner = "koesterlab"
data = FSDataStore()

entity_browser(data, Analysis, owner)
