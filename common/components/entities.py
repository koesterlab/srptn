from typing import List, Type
from common.data import DataStore

import streamlit as st

from common.data import Entity

def entity_browser(data_store: DataStore, entity_type: Type[Entity], owner: str):
    search_term = st.text_input("Search")
    only_owned = st.checkbox("only owned")

    entities = data_store.entities(entity_type=entity_type, search_term=search_term, only_owned_by=owner if only_owned else None)

    if entities:
        for entity in entities:
            entity.show()
    else:
        st.warning(f"No {entity_type.__name__.lower()} found")