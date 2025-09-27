from enum import Enum
from typing import TypedDict, Optional, List


class ProductRow(TypedDict, total=False):
    ean_number: str
    db_number: str
    commodity_code: str
    country_of_origin: str
    nobb_number: str
    article_quality_color_number: str
    article_quality_number: str
    article_number: str
    quality_number: str
    color_number: str
    color: str
    color_image_link: str
    product_name_old: str
    product_type: str
    product_categories: str
    brand: str
    collection: str
    eu_size: str
    eu_size_part1: str
    eu_size_part2: str
    uk_size: str
    uk_size_part1: str
    uk_size_part2: str
    us_size: str
    us_size_part1: str
    us_size_part2: str
    price: str
    currency: str
    hip_circumference: Optional[str]
    inseam_length: Optional[str]
    waist_circumference: Optional[str]
    chest_circumference: Optional[str]
    neck_circumference: Optional[str]
    head_circumference: Optional[str]
    weight: Optional[str]
    kg: Optional[str]
    volume: Optional[str]
    l: Optional[str]
    package_length_mm: Optional[str]
    package_width_mm: Optional[str]
    package_height_mm: Optional[str]
    loading_quantity: Optional[str]
    stock_extra_large: Optional[str]
    new_color: Optional[str]
    clearance_sale: Optional[str]
    limited_edition: Optional[str]
    color_note: Optional[str]
    in_stock_on: Optional[str]
    quality: Optional[str]
    quality_note: Optional[str]
    quality_weight: Optional[str]
    washing_symbol_name: Optional[str]
    washing_symbol_image: Optional[str]
    industrial_maintenance_category: Optional[str]
    technical_text: Optional[str]
    usp_text: str
    pictogram_name: Optional[str]
    pictogram_text: Optional[str]
    pictogram_image: Optional[str]
    notes: Optional[str]
    certification: Optional[str]
    certification_image: Optional[str]
    technology_name: Optional[str]
    technology_image: Optional[str]
    person_name: Optional[str]
    person_image: Optional[str]
    industry_name: Optional[str]
    industry_icon: Optional[str]
    logo_note: Optional[str]
    hi_vis_logo_zone: Optional[str]
    logo_position: Optional[str]
    related_products: Optional[str]
    alternative_products: Optional[str]
    doc: Optional[str]
    product_image_400px: Optional[str]
    product_image_1000px: Optional[str]
    product_image_180px: Optional[str]
    youtube_code: Optional[str]
    product_url: Optional[str]
    qr_code: Optional[str]
    product_pdf: Optional[str]
    producttype_attributes: Optional[str]
    highlighted_info: Optional[str]
    segments: Optional[str]
    variant_woman_man: Optional[str]
    fitting_accessories: Optional[str]
    fr_size: Optional[str]
    fr_size_part1: Optional[str]
    fr_size_part2: Optional[str]
    range_subnames: Optional[str]
    raw_materials_processing: Optional[str]
    production: Optional[str]
    transport_packaging: Optional[str]
    unspsc: Optional[str]
    product_accessories: Optional[str]
    lca: Optional[str]
    stock_status: Optional[str]
    reorder_status: Optional[int]

class StockFlag(str, Enum):
    GREEN = "g"
    YELLOW = "y"

FIELDS: List[str] = list(ProductRow.__annotations__.keys())
