from typing import List, Type
from common.data import DataStore

import streamlit as st

from common.data import Entity


def entity_browser(data_store: DataStore, entity_type: Type[Entity], owner: str):
    search_term = st.text_input("Search")
    only_owned = st.checkbox("only owned")

    entities = data_store.entities(
        entity_type=entity_type,
        search_term=search_term,
        only_owned_by=owner if only_owned else None,
    )

    if entities:
        for entity in entities:
            entity.show()
    else:
        st.warning(f"No {entity_type.__name__.lower()} found")


def entity_selector(
    data_store: DataStore, entity_type: Type[Entity], key: str
) -> List[Entity]:
    entities = data_store.entities(entity_type=entity_type)

    if entities:
        names = [str(entity.address) for entity in entities]
        selected = st.multiselect("Select dataset", names, key=key)
        entities = [entity for entity in entities if str(entity.address) in selected]
        st.session_state["workflow-meta-datasets-sheets"] = {
            entity.address.name: entity.sheet for entity in entities
        }
        return entities
    else:
        st.warning(f"No {entity_type.__name__.lower()} found")
        return []
