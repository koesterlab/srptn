import io
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import polars as pl


@dataclass
class Address:
    """Represents an address composed of owner, entity type, categories, and name."""

    owner: str
    entity_type: type["Entity"]
    categories: list[str]
    name: str

    @classmethod
    def from_str(cls, value: str) -> "Address":
        """Parse an address from a string."""
        from common.data.entities import _entity_types

        owner, entity, *categories, name = value.split("/")
        entity = _entity_types[entity]
        return cls(owner=owner, entity_type=entity, categories=categories, name=name)

    @classmethod
    def from_filename(cls, filename: str) -> "Address":
        """Parse an address from a filename."""
        if not filename or "___" not in filename:
            raise ValueError("Invalid filename format")
        return cls.from_str(re.sub(r"___", "/", filename))

    def to_filename(self) -> str:
        """Convert the address to a filename-safe format."""
        if "/" not in str(self):
            raise ValueError("Invalid address format")
        return re.sub(r"/", "___", str(self))

    def __str__(self) -> str:
        """Return the address as a formatted string."""
        return f"{self.owner}/{self.entity_type.__name__.lower()}/{'/'.join(self.categories)}/{self.name}"


@dataclass
class Entity(ABC):
    """Abstract base class for entities with an address and description."""

    address: Address
    desc: str

    def __post_init__(self) -> "Entity":
        """Validate the entity type against the address."""
        if self.address.entity_type != self.__class__:
            raise ValueError(f"Address type must be '{self.__class__.__name__}'")

    @abstractmethod
    def show(self) -> None:
        """Abstract method to display entity information."""
        ...

    @classmethod
    @abstractmethod
    def load(cls, data_store: "DataStore", address: Address) -> None:
        """Abstract method to load an entity from a data store."""
        ...

    def __str__(self) -> str:
        """Return the string representation of the entity."""
        return str(self.address)

    def __eq__(self, other: "Entity") -> bool:
        """Check equality based on class and address."""
        return self.__class__ == other.__class__ and self.address == other.address


class FileType(Enum):
    """Enum representing different file types."""

    DATA = "data"
    META = "meta"


@dataclass(slots=True)
class DataStore(ABC):
    """Abstract base class for data stores."""

    @abstractmethod
    def clean(self, address: Address) -> None:
        """Abstract method to clean data for a given address."""
        ...

    @abstractmethod
    def load_sheet(self, address: Address, sheet_name: str) -> pl.DataFrame:
        """Abstract method to load a sheet from the data store."""
        ...

    @abstractmethod
    def has_sheet(self, address: Address, sheet_name: str) -> bool:
        """Abstract method to check if a sheet exists in the data store."""
        ...

    @abstractmethod
    def load_desc(self, address: Address) -> str:
        """Abstract method to load a description from the data store."""
        ...

    @abstractmethod
    def load_file(
        self,
        address: Address,
        file_path: str,
        file_type: FileType,
    ) -> io.IOBase:
        """Abstract method to load a file from the data store."""
        ...

    @abstractmethod
    def has_file(
        self,
        address: Address,
        file_path: str,
        file_type: FileType,
    ) -> bool:
        """Abstract method to check if a file exists in the data store."""
        ...

    @abstractmethod
    def list_files(self, address: Address, file_type: FileType) -> pl.DataFrame:
        """Abstract method to list files in the data store."""
        ...

    @abstractmethod
    def store_file(
        self,
        address: Address,
        file: io.IOBase,
        file_path: str,
        file_type: FileType,
    ) -> None:
        """Abstract method to store a file in the data store."""
        ...

    @abstractmethod
    def store_desc(self, address: Address, desc: str) -> None:
        """Abstract method to store a description in the data store."""
        ...

    @abstractmethod
    def store_sheet(
        self,
        address: Address,
        sheet: pl.DataFrame,
        sheet_name: str,
    ) -> None:
        """Abstract method to store a sheet in the data store."""
        ...

    @abstractmethod
    def entities(
        self,
        entity_type: type[Entity],
        search_term: str | None = None,
        only_owned_by: str | None = None,
    ) -> list[Entity]:
        """Abstract method to fetch entities from the data store."""
        ...

    @abstractmethod
    def has_entity(self, address: Address) -> None:
        """Abstract method to check if an Entity exists in the data store."""
        ...
