import io
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

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
        from srptn.common.data.entities import EntityType

        owner, entity, *categories, name = value.split("/")
        entity = EntityType[entity].value
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
        return f"""{self.owner}/{self.entity_type.__name__.lower()}/{
            "/".join(self.categories)
        }/{self.name}"""


@dataclass()
class Entity(ABC):
    """Abstract base class for entities with an address and description."""

    address: Address
    desc: str

    def __post_init__(self) -> None:
        """Validate the entity type against the address."""
        if self.address.entity_type != self.__class__:
            raise ValueError(f"Address type must be '{self.__class__.__name__}'")

    @abstractmethod
    def show(self) -> None:
        """Abstract method to display entity information."""
        ...

    @classmethod
    @abstractmethod
    def load(cls, data_store: "DataStore", address: Address) -> "Entity":
        """Abstract method to load an entity from a data store."""
        ...

    def __str__(self) -> str:
        """Return the string representation of the entity."""
        return str(self.address)

    def __eq__(self, other: object) -> bool:
        """Check equality based on class and address."""
        if not isinstance(other, Entity):
            return NotImplemented
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
        file_path: Path,
        file_type: FileType,
    ) -> io.BufferedReader:
        """Abstract method to load a file from the data store."""
        ...

    @abstractmethod
    def has_file(
        self,
        address: Address,
        file_path: Path,
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
        file_path: Path,
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
    def has_entity(self, address: Address) -> bool:
        """Abstract method to check if an Entity exists in the data store."""
        ...

    @staticmethod
    @abstractmethod
    def as_path(base: Path, address: Address) -> Path:
        """Abstract method to convert a base path and address into a full path."""
        ...

    @abstractmethod
    def desc_path(self, address: Address) -> Path:
        """
        Abstract method to return the path to the description file for the address.
        """
        ...

    @abstractmethod
    def sheet_path(self, address: Address, name: str) -> Path:
        """
        Abstract method to return the path to a sheet file for the address and name.
        """
        ...

    @abstractmethod
    def files_path(self, address: Address, file_type: FileType) -> Path:
        """
        Abstract method to return the path to the files dir for a address and type.
        """
        ...
