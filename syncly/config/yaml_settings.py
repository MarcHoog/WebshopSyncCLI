from typing import List, Dict, Optional
from pydantic import BaseModel
import yaml

class CCVShopGeneral(BaseModel):
    root_category: str = ""
    base_url: str = ""
    color_category: str = ""
    sizing_category: str = ""

class CCVShopSettings(BaseModel):
    general: CCVShopGeneral

class PerfionGeneral(BaseModel):
    brand: str = ""
    included_categories: List[str] = []
    excluded_products: List[str] = []
    aditional_categories: List[str] = []


class PerfionMapping(BaseModel):
    color: Dict[str, str] = {}
    category: Dict[str, str] = {}
    size: Dict[str, str] = {}

class PerfionSettings(BaseModel):
    general: PerfionGeneral
    mapping: PerfionMapping


class SynclySettings(BaseModel):
    _instance: Optional["SynclySettings"] = None

    ccv_shop: CCVShopSettings
    perfion: PerfionSettings



    @classmethod
    def from_yaml(cls, path: str) -> "SynclySettings":
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        cls._instance = cls(**data.get("settings", {}))
        return cls._instance

    @classmethod
    def get_instance(cls) -> "SynclySettings":
        if cls._instance is None:
            raise RuntimeError("SynclySettings has not been initialized. Call from_yaml() first.")
        return cls._instance
