import io
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import polars as pl


@dataclass
class Address:
    owner: str
    entity_type: type["Entity"]
    categories: list[str]
    name: str

    @classmethod
    def from_str(cls, value: str):
        from common.data.entities import _entity_types

        owner, entity, *categories, name = value.split("/")
        entity = _entity_types[entity]
        return cls(owner=owner, entity_type=entity, categories=categories, name=name)

    def __str__(self):
        return f"{self.owner}/{self.entity_type.__name__.lower()}/{'/'.join(self.categories)}/{self.name}"


@dataclass
class Entity(ABC):
    address: Address
    desc: str

    def __post_init__(self):
        if self.address.entity_type != self.__class__:
            raise ValueError(f"Address type must be '{self.__class__.__name__}'")

    @abstractmethod
    def show(self): ...

    @classmethod
    @abstractmethod
    def load(cls, data_store: "DataStore", address: Address): ...

    def __str__(self):
        return str(self.address)

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.address == other.address


class FileType(Enum):
    DATA = "data"
    META = "meta"


@dataclass(slots=True)
class DataStore(ABC):
    @abstractmethod
    def clean(self, address: Address): ...

    @abstractmethod
    def load_sheet(self, address: Address, sheet_name: str) -> pl.DataFrame: ...

    @abstractmethod
    def has_sheet(self, address: Address, sheet_name: str) -> bool: ...

    @abstractmethod
    def load_desc(self, address: Address) -> str: ...

    @abstractmethod
    def load_file(
        self, address: Address, file_path: str, file_type: FileType
    ) -> io.IOBase: ...

    @abstractmethod
    def has_file(
        self, address: Address, file_path: str, file_type: FileType
    ) -> bool: ...

    @abstractmethod
    def list_files(self, address: Address, file_type: FileType) -> pl.DataFrame: ...

    @abstractmethod
    def store_file(
        self, address: Address, file: io.IOBase, file_path: str, file_type: FileType
    ): ...

    @abstractmethod
    def store_desc(self, address: Address, desc: str): ...

    @abstractmethod
    def store_sheet(self, address: Address, sheet: pl.DataFrame, sheet_name: str): ...

    @abstractmethod
    def entities(
        self,
        entity_type: type[Entity],
        search_term: str | None = None,
        only_owned_by: str | None = None,
    ) -> list[Entity]: ...

    @abstractmethod
    def has_entity(self, address: Address): ...
