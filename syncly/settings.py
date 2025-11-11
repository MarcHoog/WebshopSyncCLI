from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator
import yaml

StrDict = Dict[str, Optional[str]]


class CcvShop(BaseModel):
    root_category: str = ""
    delete_categories: bool = False
    url: str = ""
    color_category: str = ""
    sizing_category: str = ""
    image_width: int = 550
    image_height: int = 550
    brand: str = ""
    additional_categories: List[str] = Field(default_factory=list)

    @field_validator("url")
    def validate_url(cls, v):
        if v and not v.startswith("http"):
            raise ValueError("CCVShop URL must start with http or https")
        return v

class Mapping(BaseModel):
    color: StrDict = Field(default_factory=dict)
    category: StrDict = Field(default_factory=dict)
    size: StrDict = Field(default_factory=dict)

class Perfion(BaseModel):
    url: str = ""
    included_categories: List[str] = Field(default_factory=list)
    excluded_products: List[str] = Field(default_factory=list)

class Mascot(BaseModel):
    availability: str = "" # THe file path to the availabilty csv
    product_data: str = "" # The filePath to the Availiability Product data
    excluded_product_types: List[str] = Field(default_factory=list)

class Settings(BaseModel):
    ccv_shop: CcvShop = Field(default_factory=CcvShop)
    perfion: Perfion = Field(default_factory=Perfion)
    mascot: Mascot = Field(default_factory=Mascot)
    mapping: Mapping = Field(default_factory=Mapping)

    @classmethod
    def from_yaml(cls, path: str) -> "Settings":
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            return cls(**data.get("settings", {}))
        except FileNotFoundError:
            raise RuntimeError(f"YAML file not found: {path}")
        except Exception as e:
            raise RuntimeError(f"Failed to load settings: {e}")

_settings_instance: Optional[Settings] = None

def load_settings(path: str) -> Settings:
    global _settings_instance
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    _settings_instance = Settings(**data.get("settings", {}))
    return _settings_instance

def get_settings() -> Settings:
    if _settings_instance is None:
        raise RuntimeError("Settings not initialized. Call load_settings() first.")
    return _settings_instance
