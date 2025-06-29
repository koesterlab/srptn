import io
import shutil
from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree

import polars as pl

from srptn.common.data import Address, DataStore, Entity, FileType


@dataclass(slots=True)
class FSDataStore(DataStore):
    """A file-system-based implementation of the DataStore interface."""

    base_data: Path = Path("datastore/data")
    base_meta: Path = Path("datastore/meta")

    def clean(self, address: Address) -> None:
        """Remove metadata and data files associated with the given address."""
        rmtree(self.files_path(address, FileType.META), ignore_errors=True)
        rmtree(self.files_path(address, FileType.DATA), ignore_errors=True)

    def load_sheet(self, address: Address, sheet_name: str) -> pl.DataFrame:
        """Load a sample sheet as a Polars DataFrame from the given address."""
        return pl.read_parquet(self.sheet_path(address, sheet_name))

    def has_sheet(self, address: Address, sheet_name: str) -> bool:
        """Check if a sample sheet exists for the given address and sheet name."""
        return self.sheet_path(address, sheet_name).exists()

    def load_desc(self, address: Address) -> str:
        """Load and returns the description text for the given address."""
        return self.desc_path(address).read_text()

    def load_file(
        self,
        address: Address,
        file_path: Path,
        file_type: FileType,
    ) -> io.BufferedReader:
        """Load a file of a specific type from the given address."""
        return (self.files_path(address, file_type) / file_path).open("rb")

    def has_file(self, address: Address, file_path: Path, file_type: FileType) -> bool:
        """Check if a file exists for the given address, path, and file type."""
        return (self.files_path(address, file_type) / file_path).exists()

    def list_files(self, address: Address, file_type: FileType) -> pl.DataFrame:
        """List all files of a specific type at the given address."""
        files_dir = self.files_path(address, file_type)
        if files_dir.exists():
            return pl.DataFrame(
                [
                    (f.name, f.stat().st_size)
                    for f in files_dir.iterdir()
                    if f.is_file()
                ],
                schema=["name", "size"],
                orient="row",
            )
        return pl.DataFrame(schema=["name", "size"])

    def store_file(
        self,
        address: Address,
        file: io.IOBase,
        file_path: Path,
        file_type: FileType,
    ) -> None:
        """Store a file of a specific type at the given address."""
        folder = self.files_path(address, file_type)
        file_path = folder / file_path
        file_path.parent.mkdir(exist_ok=True, parents=True)
        with (file_path).open("wb") as f:
            shutil.copyfileobj(file, f)

    def store_desc(self, address: Address, desc: str) -> None:
        """Store the description text for the given address."""
        desc_path = self.desc_path(address)
        desc_path.parent.mkdir(exist_ok=True, parents=True)
        desc_path.write_text(desc)

    def store_sheet(
        self,
        address: Address,
        sheet: pl.DataFrame,
        sheet_name: str,
    ) -> None:
        """Store a sample sheet as a Parquet file at the given address."""
        sheet_path = self.sheet_path(address, sheet_name)
        sheet_path.parent.mkdir(exist_ok=True, parents=True)
        try:
            sheet.write_parquet(sheet_path)
        except Exception as e:
            raise RuntimeError(f"Failed to write sheet to {sheet_path}: {e}") from e

    def entities(
        self,
        entity_type: type[Entity],
        search_term: str | None = None,
        only_owned_by: str | None = None,
    ) -> list[Entity]:
        """Retrieve entities of a specific type, filtered by search term and owner."""
        addr = (
            Address.from_str(str(desc.parent.relative_to(self.base_meta)))
            for desc in self.base_meta.glob("**/desc.md")
        )
        addr = [a for a in addr if a.entity_type == entity_type]

        def take_all(entity: Entity) -> bool:
            return bool(entity)  # new pyright conform placeholder

        if search_term:

            def search_filter_func(entity: Entity) -> bool:
                return search_term in str(entity.address) or search_term in entity.desc

        else:
            search_filter_func = take_all
        if only_owned_by:

            def owned_filter_func(entity: Entity) -> bool:
                return entity.address.owner == only_owned_by

        else:
            owned_filter_func = take_all

        return list(
            filter(
                search_filter_func,
                filter(owned_filter_func, (entity_type.load(self, a) for a in addr)),
            ),
        )

    def has_entity(self, address: Address) -> bool:
        """Check if an entity exists for the given address."""
        return self.desc_path(address).exists()

    @staticmethod
    def as_path(base: Path, address: Address) -> Path:
        """Convert a base path and address into a full path."""
        return base / str(address)

    def desc_path(self, address: Address) -> Path:
        """Return the path to the description file for the given address."""
        return self.files_path(address, FileType.META) / "desc.md"

    def sheet_path(self, address: Address, name: str) -> Path:
        """Return the path to a sheet file for the given address and name."""
        return self.files_path(address, FileType.META) / f"{name}.parquet"

    def files_path(self, address: Address, file_type: FileType) -> Path:
        """Return the path to the files directory for a given address and type."""
        return self.as_path(
            self.base_data if file_type == FileType.DATA else self.base_meta,
            address,
        )
