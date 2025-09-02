import logging
from syncly.intergrations.ccvshop.models.third_party import ThirdPartyProduct
from syncly.utils import (
    wrap_style,
    xlsx_bytes_to_list,
    csv_bytes_to_list,
    normalize_string,
    append_if_not_exists,
)
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

class MascotAdapter(ThirdPartyAdapter):

    def __str__(self):
        return "MascotAdapter"

    def _get_products(self) -> Union[List[ProductRow], Generator[ProductRow, Any, Any]]: # type: ignore | Product Row is a typed dict IG that's not of a type dict
        assert self.conn

        with self.conn as client:
            files = client.list_files()
            for f in [self.settings.mascot.product_data, self.settings.mascot.availability]:
                if f not in files:
                    raise ValueError(f"Expected file {f} to exist in {files}")

            product_data: List[List[Any]] = xlsx_bytes_to_list(
                client.download_file(self.settings.mascot.product_data),
                include_header=False
            )
            availability_data = {
                x[0]: {
                    "stock_status": x[1],
                    "reorder_status": x[3],
                }
                for x in csv_bytes_to_list(
                    client.download_file(self.settings.mascot.availability),
                    include_header=False, seperator=";"
                )
            }

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

        brand = self.settings.mascot.brand


        for product_data in self._get_products():

            name = f"{product_data['article_quality_number']} {product_data['collection']} {product_data['product_type']}" #type: ignore
            product, _ = cast(Tuple[ThirdPartyProduct, bool], self.get_or_instantiate(
                model=self.product,
                ids= {
                    "producnumber": product_data["article_number"] # type: ignore
                },
                attrs = {
                    "name": name,
                    "package": "kartonnen doos",
                    "price": float(product_data.get('price', 0.0)),
                    "description": wrap_style(product_data.get('usp_text', "")),
                    "category": product_data.get("product_categories"),
                    "brand": normalize_string(brand),

                    "page_title": f"{brand} {name} "
                },
            ))

            append_if_not_exists(product_data.get("color"), product.colors)
            append_if_not_exists(product_data.get("eu_size"), product.sizing)
            append_if_not_exists((product_data.get("color"), product_data.get("product_image_1000px")), product.images)

        return cast(List[ThirdPartyProduct], self.get_all(self.product))
