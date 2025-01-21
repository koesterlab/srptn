import streamlit as st

from common.components.ui_components import persistent_multiselect
from common.data import DataStore, Entity


def entity_browser(
    data_store: DataStore,
    entity_type: type[Entity],
    owner: str,
) -> None:
    """Display a browser interface for searching and filtering entities.

    :param data_store: The data store containing entities to browse.
    :param entity_type: The type of entities to browse.
    :param owner: The owner of the entities.
    """
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
    data_store: DataStore,
    entity_type: type[Entity],
    key: str,
) -> list[Entity]:
    """Allow the user to select entities from a list.

    :param data_store: The data store containing entities to select.
    :param entity_type: The type of entities to select.
    :param key: A unique key for storing selection state.
    :return: A list of selected entities.
    """
    entities = data_store.entities(entity_type=entity_type)

    if entities:
        names = [str(entity.address) for entity in entities]
        selected = persistent_multiselect(
            "Select datasets",
            names,
            key,
        )
        entities = [entity for entity in entities if str(entity.address) in selected]
        st.session_state["workflow-meta-datasets-sheets"] = {
            str(entity.address): entity.sheet for entity in entities
        }
        return entities
    st.warning(f"No {entity_type.__name__.lower()} found")
    return []
