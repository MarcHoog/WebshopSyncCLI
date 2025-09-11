from typing import List, Dict, Optional
from pydantic import BaseModel
import yaml

class CCVShopSettings(BaseModel):
    root_category: str = ""
    url: str = ""
    color_category: str = ""
    sizing_category: str = ""
    image_width: int = 550
    image_height: int = 550
    brand: str = ""
    aditional_categories: List[str] = []

class Mapping(BaseModel):
    color: Dict[str, Optional[str]] = {}
    category: Dict[str, Optional[str]] = {}
    size: Dict[str, Optional[str]] = {}

class PerfionSettings(BaseModel):
    url: str = ""
    included_categories: List[str] = []
    excluded_products: List[str] = []

class MascotSettings(BaseModel):
    availability: str = ""
    product_data: str = ""

class SynclySettings(BaseModel):
    _instance: Optional["SynclySettings"] = None

    ccv_shop: CCVShopSettings = CCVShopSettings()
    perfion: PerfionSettings = PerfionSettings()
    mascot: MascotSettings = MascotSettings()
    mapping: Mapping = Mapping()



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
