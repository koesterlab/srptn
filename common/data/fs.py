from dataclasses import dataclass
import io
from pathlib import Path
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
    
    def load_file(self, address: Address, file_name: str, file_type: FileType) -> io.BytesIO:
        return (self.files_path(address, file_type) / file_name).open("rb")
    
    def list_files(self, address: Address, file_type: FileType) -> pd.DataFrame:
        return pd.DataFrame(
            [(f.name, f.stat().st_size) for f in self.files_path(address, file_type).iterdir()],
            columns=["name", "size"]
        )
    
    def store_file(self, address: Address, file: io.BytesIO, file_type: FileType):
        folder = self.files_path(address, file_type)
        folder.mkdir(exist_ok=True, parents=True)
        with (folder / file.name).open("wb") as f:
            f.write(file.getbuffer())

    
    def store_desc(self, address: Address, desc: str):
        desc_path = self.desc_path(address)
        desc_path.parent.mkdir(exist_ok=True, parents=True)
        desc_path.write_text(desc)

    
    def store_sheet(self, address: Address, sheet: pd.DataFrame, sheet_name: str):
        sheet_path = self.sheet_path(address, sheet_name)
        sheet_path.parent.mkdir(exist_ok=True, parents=True)
        sheet.to_parquet(sheet_path, index=False)

    
    def entities(self, entity_type: Type[Entity], search_term: Optional[str], only_owned_by: Optional[str]) -> List[Entity]:
        addr = (Address.from_str(str(desc.parent.relative_to(self.base_meta))) for desc in self.base_meta.glob("**/desc.md"))
        addr = [a for a in addr if a.entity_type == entity_type]
        def take_all(_):
            return True
        if search_term:
            def search_filter_func(dataset):
                return search_term in str(dataset.address) or search_term in dataset.desc
        else:
            search_filter_func = take_all
        if only_owned_by:
            def owned_filter_func(dataset):
                return dataset.address.owner == only_owned_by
        else:
            owned_filter_func = take_all

        return list(filter(search_filter_func, filter(owned_filter_func, (entity_type.load(self, a) for a in addr))))

    
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
        return self.as_path(self.base_data if file_type == FileType.DATA else self.base_meta / "files", address)