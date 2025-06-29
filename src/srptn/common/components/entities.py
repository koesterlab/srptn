import polars as pl
import streamlit as st

from srptn.common.components.ui_components import persistent_multiselect
from srptn.common.data import DataStore, Entity
from srptn.common.data.entities import EntityType
from srptn.common.data.entities.dataset import Dataset


def entity_browser(
    data_store: DataStore,
    entity_type: str,
    owner: str,
) -> None:
    """
    Display a browser interface for searching and filtering entities.

    :param data_store: The data store containing entities to browse.
    :param entity_type: The type of entities to browse.
    :param owner: The owner of the entities.
    """
    search_term = st.text_input("Search")
    only_owned = st.checkbox("only owned")

    entity_type_class = EntityType[entity_type].value
    entities = data_store.entities(
        entity_type=entity_type_class,
        search_term=search_term,
        only_owned_by=owner if only_owned else None,
    )

    if entities:
        for entity in entities:
            entity.show()
    else:
        st.warning(f"No {entity_type_class.__name__.lower()} found")


def entity_selector(
    data_store: DataStore,
    entity_type: str,
    key: str,
) -> list[Entity]:
    """
    Allow the user to select entities from a list.

    :param data_store: The data store containing entities to select.
    :param entity_type: The type of entities to select.
    :param key: A unique key for storing selection state.
    :return: A list of selected entities.
    """
    entity_type_class = EntityType[entity_type].value
    entities = data_store.entities(entity_type=entity_type_class)

    if entities:
        names = [str(entity.address) for entity in entities]
        selected = persistent_multiselect(
            "Select datasets",
            names,
            key,
        )
        entities = [entity for entity in entities if str(entity.address) in selected]
        st.session_state["workflow-meta-datasets-sheets"] = {
            str(entity.address): entity.sheet
            for entity in entities
            if isinstance(entity, Dataset) and isinstance(entity.sheet, pl.DataFrame)
        }

        return entities
    st.warning(f"No {entity_type_class.__name__.lower()} found")
    return []
