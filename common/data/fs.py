from dataclasses import dataclass
import io
from pathlib import Path
import shutil
from typing import List, Optional, Type
from common.data import Address, Entity, FileType
from common.data import DataStore
import pandas as pd


@dataclass(slots=True)
class FSDataStore(DataStore):
    base_data: Path = Path("datastore/data")
    base_meta: Path = Path("datastore/meta")

    def clean(self, address: Address):
        self.meta_path(address).unlink(missing_ok=True)
        self.files_path(address, FileType.DATA).unlink(missing_ok=True)

    def load_sheet(self, address: Address, sheet_name: str) -> pd.DataFrame:
        return pd.read_parquet(self.sheet_path(address, sheet_name))

    def has_sheet(self, address: Address, sheet_name: str) -> bool:
        return self.sheet_path(address, sheet_name).exists()

    def load_desc(self, address: Address) -> str:
        return self.desc_path(address).read_text()

    def load_file(
        self, address: Address, file_path: str, file_type: FileType
    ) -> io.IOBase:
        return (self.files_path(address, file_type) / file_path).open("rb")

    def has_file(self, address: Address, file_path: str, file_type: FileType) -> bool:
        return (self.files_path(address, file_type) / file_path).exists()

    def list_files(self, address: Address, file_type: FileType) -> pd.DataFrame:
        files_dir = self.files_path(address, file_type)
        if files_dir.exists():
            return pd.DataFrame(
                [
                    (f.name, f.stat().st_size)
                    for f in files_dir.iterdir()
                    if f.is_file()
                ],
                columns=["name", "size"],
            )
        else:
            return pd.DataFrame(columns=["name", "size"])

    def store_file(
        self, address: Address, file: io.IOBase, file_path: str, file_type: FileType
    ):
        folder = self.files_path(address, file_type)
        file_path = folder / file_path
        file_path.parent.mkdir(exist_ok=True, parents=True)
        with (file_path).open("wb") as f:
            import pdb

            pdb.set_trace()
            shutil.copyfileobj(file, f)

    def store_desc(self, address: Address, desc: str):
        desc_path = self.desc_path(address)
        desc_path.parent.mkdir(exist_ok=True, parents=True)
        desc_path.write_text(desc)

    def store_sheet(self, address: Address, sheet: pd.DataFrame, sheet_name: str):
        sheet_path = self.sheet_path(address, sheet_name)
        sheet_path.parent.mkdir(exist_ok=True, parents=True)
        sheet.to_parquet(sheet_path, index=False)

    def entities(
        self,
        entity_type: Type[Entity],
        search_term: Optional[str] = None,
        only_owned_by: Optional[str] = None,
    ) -> List[Entity]:
        addr = (
            Address.from_str(str(desc.parent.relative_to(self.base_meta)))
            for desc in self.base_meta.glob("**/desc.md")
        )
        addr = [a for a in addr if a.entity_type == entity_type]

        def take_all(_):
            return True

        if search_term:

            def search_filter_func(entity):
                return search_term in str(entity.address) or search_term in entity.desc

        else:
            search_filter_func = take_all
        if only_owned_by:

            def owned_filter_func(entity):
                return entity.address.owner == only_owned_by

        else:
            owned_filter_func = take_all

        return list(
            filter(
                search_filter_func,
                filter(owned_filter_func, (entity_type.load(self, a) for a in addr)),
            )
        )

    def has_entity(self, address: Address):
        return self.desc_path(address).exists()

    @staticmethod
    def as_path(base: Path, address: Address) -> Path:
        return base / str(address)

    def desc_path(self, address: Address) -> Path:
        return self.meta_path(address) / "desc.md"

    def sheet_path(self, address: Address, name: str) -> Path:
        return self.meta_path(address) / f"{name}.parquet"

    def meta_path(self, address: Address) -> Path:
        return self.as_path(self.base_meta, address)

    def files_path(self, address: Address, file_type: FileType) -> Path:
        return self.as_path(
            self.base_data if file_type == FileType.DATA else self.base_meta / "files",
            address,
        )
