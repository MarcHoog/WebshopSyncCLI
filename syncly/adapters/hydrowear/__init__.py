"""
HydroWear Third-Party Adapter

This adapter processes product data from HydroWear CSV files and converts
them into ThirdPartyProduct instances for synchronization with the CCV shop.

Data Flow:
1. Read CSV file from connection
2. Parse rows into ProductRow TypedDict
3. Filter and validate products
4. Transform to ThirdPartyProduct format
5. Add variants (colors, sizes, images)
"""

import logging
from pydantic import ValidationError
from typing import List, Any, Generator, Tuple, cast

from syncly.helpers import (
    xlsx_bytes_to_list,
    wrap_style,
    normalize_string,
    append_if_not_exists,
    pretty_validation_error,
)
from ..third_party import ThirdPartyAdapter
from .models import ProductRow
from .helpers import (
    parse_product_row,
    calculate_base_prices,
    build_name,
    build_description,
    build_meta_description,
    build_page_title,
    get_base_price,
    get_price,
    calculate_variant_price,
    get_categories,
)
from .constants import DEFAULT_PACKAGE
from ...models.third_party import ThirdPartyProduct
from ...clients.local import LocalFileClient

logger = logging.getLogger(__name__)


class HydroWearAdapter(ThirdPartyAdapter):
    """
    Adapter for processing HydroWear product data.

    This adapter reads CSV files containing HydroWear product information
    and transforms them into standardized ThirdPartyProduct objects.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.image_mode = "contain"
        self.conn: LocalFileClient = self.conn
        self.price_mapping: dict[str, float] = {}

    def __str__(self) -> str:
        return "HydroWearAdapter"

    def get_product_data(self) -> Generator[ProductRow, Any, Any]:
        """Parse CSV file, calculate base prices, and yield ProductRow dictionaries."""
        assert self.conn, "Connection must be established before reading products"

        with self.conn as file:
            product_data = xlsx_bytes_to_list(file.read(), include_header=False)
            self.price_mapping = calculate_base_prices(product_data)
            for product in product_data:
                yield parse_product_row(product)

    def should_process_product(self, row: ProductRow) -> bool:
        """Check if product should be processed based on business rules."""
        if not row.get("article_number"):
            logger.debug("Skipping product without article number")
            return False

        return True

    def build_product_ids(self, row: ProductRow) -> dict[str, str]:
        """Extract product identification fields."""
        return {"productnumber": str(row.get("model", ""))}

    def build_product_attrs(self, row: ProductRow, brand: str) -> dict[str, Any]:
        """Build product attributes dictionary from row data."""
        return {
            "name": build_name(row),
            "package": DEFAULT_PACKAGE,
            "description": wrap_style(build_description(row)),
            "price": get_base_price(row, self.price_mapping),
            "category": get_categories(row),
            "brand": brand,
            "page_title": build_page_title(row),
            "meta_description": build_meta_description(row),
        }

    def create_product(self, row: ProductRow, brand: str) -> ThirdPartyProduct:
        """Create or retrieve a product from a data row."""
        try:
            product, _ = cast(
                Tuple[ThirdPartyProduct, bool],
                self.get_or_instantiate(
                    model=self.product,
                    ids=self.build_product_ids(row),
                    attrs=self.build_product_attrs(row, brand),
                ),
            )
            return product

        except ValidationError as err:
            article_num = row.get("article_number", "unknown")
            logger.error(f"Failed to create product {article_num}: {err}")
            pretty_validation_error(err)
            raise err

    def add_variants(self, row: ProductRow, product: ThirdPartyProduct) -> None:
        """Add color, size, and image variants to product."""
        colour = row.get("colour_nl")
        if colour:
            append_if_not_exists((colour, 0), product.colors)

        size = normalize_string(f"{row.get('sizes')}")
        if size:
            variant_price = calculate_variant_price(get_price(row), product.price)
            logging.info(
                f"Adding size {size} variant with price {variant_price} to product {product.productnumber}"
            )
            append_if_not_exists((size, variant_price), product.sizing)

        image_url = row.get("article_image")
        if colour and image_url:
            append_if_not_exists((colour, image_url), product.images)

    def load_products(self) -> List[ThirdPartyProduct]:
        """
        Load and process all products from the data source.

        Orchestrates: reading, filtering, creating/updating products, and adding variants.
        """
        brand = normalize_string(self.settings.ccv_shop.brand)

        for row in self.get_product_data():
            if not self.should_process_product(row):
                continue

            product = self.create_product(row, brand)
            self.add_variants(row, product)

        return cast(List[ThirdPartyProduct], self.get_all(self.product))
