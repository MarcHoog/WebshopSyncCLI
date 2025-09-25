import logging

from pydantic import ValidationError
from syncly.config.yaml_settings import SynclySettings
from syncly.intergrations.ccvshop.models.third_party import ThirdPartyProduct
from syncly.helpers import (
    wrap_style,
    xlsx_bytes_to_list,
    csv_bytes_to_list,
    normalize_string,
    append_if_not_exists,
    to_float,
    pretty_validation_error
)
from enum import Enum
from typing import TypedDict, Optional, List, Any, Union, Generator, Tuple, cast
from syncly.intergrations.ccvshop.adapters.adapter_third_party import ThirdPartyAdapter

logger = logging.getLogger(__name__)


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

def _build_name(pd: ProductRow, brand_normalized: str) -> str:
    parts = [brand_normalized, pd.get("article_quality_number")]
    if pd.get("product_name_old"):
        pn_old = pd["product_name_old"] # type: ignore |
        pn_old_parts = pn_old.split(" ")
        pn_old = " ".join(pn_old_parts[1:])
        parts.append(pn_old)

    parts.append(pd.get("product_type"))
    return " ".join(str(p) for p in parts if p)

def _build_description(pd: ProductRow) -> str:
    items = [item.strip() for item in str(pd.get('usp_text', "")).split(';') if item.strip()]
    list_items = "\n  ".join(f"<li>{item}</li>" for item in items)
    formated_usp_text =  f"<ul>\n  {list_items}\n</ul>"
    technical_text = pd.get('technical_text', "")

    return f"""
        {technical_text}
        <br>
        <br>
        <br>
        <br>
        {formated_usp_text}
    """


def _build_meta_description(pd: ProductRow) -> str:
    technical_text = pd.get('technical_text', "") or ""
    if len(technical_text) >= 317:
        technical_text = technical_text[:317]

    return f"{technical_text}..."



def _get_price(pd: ProductRow) -> float:
    raw = pd.get("price")
    if raw is None or raw == "":
        return 0.0
    try:
        return to_float(str(raw))
    except Exception:
        logger.warning("Failed to parse price %r; defaulting to 0.0", raw)
        return 0.0


def _is_stocked(pd: ProductRow) -> bool:
    flag = f"{pd.get('stock_status', '')}".strip().lower()
    if flag in {StockFlag.GREEN.value, StockFlag.YELLOW.value}:
        try:
            return int(pd.get("reorder_status") or 0) == 1
        except (TypeError, ValueError):
            return False
    return False

def _create_availablity_mapping(csv_bytes) -> Any:
    availability_data = {
        x[0]: {
            "stock_status": x[1],
            "reorder_status": x[3],
        }
        for x in csv_bytes_to_list(
            csv_bytes,
            include_header=False,
            seperator=";",
        )
    }

    return availability_data


def _is_excluded(pd: ProductRow, settings: SynclySettings) -> bool:
    excluded = [normalize_string(set) for set in settings.mascot.excluded_product_types]
    if normalize_string(str(pd.get('product_type'))) in excluded:
        return True

    return False



class MascotAdapter(ThirdPartyAdapter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.image_mode = 'contain'

    def __str__(self):
        return "MascotAdapter"

    def _get_products(self) -> Union[List[ProductRow], Generator[ProductRow, Any, Any]]: # type: ignore | Product Row is a typed dict IG that's not of a type dict
        assert self.conn

        with self.conn as client:
            files = set(client.list_files())
            required = {self.settings.mascot.product_data, self.settings.mascot.availability}
            missing = required - files
            if missing:
                raise ValueError(f"Missing files: {sorted(missing)} (found: {sorted(files)})")

            product_data: List[List[Any]] = xlsx_bytes_to_list(
                client.download_file(self.settings.mascot.product_data),
                include_header=False
            )

            availablity_csv = client.download_file(
                self.settings.mascot.availability,
            )
            availability_data = _create_availablity_mapping(availablity_csv)

            product_rows = []
            for product in product_data:
                product_row: ProductRow = {}
                for i, field in enumerate(ProductRow.__annotations__):
                    if i < len(product):
                        product_row[field] = product[i]
                    else:
                        product_row[field] = None
                avail = availability_data.get(product_row.get('ean_number'), {})
                product_row["stock_status"] = avail.get("stock_status")
                product_row["reorder_status"] = avail.get("reorder_status")
                product_rows.append(product_row)

                yield product_row

        return product_rows

    def load_products(self):

        brand = self.settings.ccv_shop.brand

        for pd in self._get_products():
            if _is_stocked(pd) and not _is_excluded(pd, self.settings):
                name = _build_name(pd, brand)

                try:
                    product, _ = cast(Tuple[ThirdPartyProduct, bool], self.get_or_instantiate(
                        model=self.product,
                        ids= {
                            "productnumber": f"{pd.get('article_number')}"
                        },
                        attrs = {
                            "name": _build_name(pd, brand),
                            "package": "kartonnen doos",
                            "price": _get_price(pd),
                            "description": wrap_style(_build_description(pd)),
                            "category": [str(pd.get('product_type'))],
                            "brand": normalize_string(brand),

                            "page_title": f"{name} ",
                            "meta_description":  _build_meta_description(pd)

                        },
                    ))
                except ValidationError as err:
                    pretty_validation_error(err)
                    raise err

                append_if_not_exists(pd.get("color"), product.colors)
                append_if_not_exists(pd.get("eu_size_part1"), product.sizing)
                append_if_not_exists((pd.get("color"), pd.get("product_image_1000px")), product.images)

        return cast(List[ThirdPartyProduct], self.get_all(self.product))
