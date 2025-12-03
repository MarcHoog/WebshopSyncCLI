"""
Perfion Third-Party Adapter

This adapter processes product data from the Perfion API and converts
them into ThirdPartyProduct instances for synchronization with the CCV shop.

Data Flow:
1. Connect to Perfion API via connection client
2. Fetch product data from API
3. Filter products by included categories and excluded products
4. Transform to ThirdPartyProduct format
5. Add variants (colors, sizes, images)
"""

import logging
from typing import List, Any, Generator, Tuple, cast
from pydantic import ValidationError
from requests.exceptions import RequestException

from syncly.helpers import (
    normalize_string,
    append_if_not_exists,
    wrap_style,
    pretty_validation_error,
)
from ..third_party import ThirdPartyAdapter
from .models import ProductRow
from .helpers import (
    build_name,
    build_description,
    build_meta_description,
    build_page_title,
    get_price,
    get_categories,
    calculate_base_prices,
    get_base_price,
    calculate_variant_price,
)
from .constants import DEFAULT_PACKAGE
from ...models.third_party import ThirdPartyProduct

logger = logging.getLogger(__name__)


class PerfionAdapter(ThirdPartyAdapter):
    """
    Adapter for processing Perfion API product data.

    This adapter connects to the Perfion API to fetch product information
    and transforms them into standardized ThirdPartyProduct objects.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.price_mapping: dict[str, float] = {}

    def __str__(self) -> str:
        return "PerfionAdapter"

    def _should_include_category(self, category: str) -> bool:
        """Check if product category is in included categories list."""
        included_categories = self.settings.perfion.included_categories

        # If no filter specified, include all
        if not included_categories:
            return True

        return category in included_categories

    def _is_product_excluded(self, item_number: str) -> bool:
        """Check if product is in excluded products list."""
        excluded_products = self.settings.perfion.excluded_products
        return item_number in excluded_products

    def should_process_product(self, row: ProductRow) -> bool:
        """Check if product should be processed based on business rules."""
        category = row.get("Category")
        item_number = row.get("ItemNumber")

        if not item_number:
            logger.debug("Skipping product without item number")
            return False

        if not category:
            logger.debug(f"Skipping product {item_number} without category")
            return False

        if not self._should_include_category(category):
            logger.info(
                f"Skipping product {item_number} - category '{category}' not in "
                f"included categories: {self.settings.perfion.included_categories}"
            )
            return False

        if self._is_product_excluded(item_number):
            logger.info(f"Skipping excluded product: {item_number}")
            return False

        return True

    def _get_products(self) -> Generator[ProductRow, Any, Any]:
        """
        Fetch products from Perfion API and yield ProductRow dictionaries.

        First fetches all products to calculate base prices (minimum price per ItemNumber),
        then yields each row for processing.
        """
        assert self.conn, "Connection must be established before reading products"

        try:
            result = self.conn.get_products()
        except RequestException as err:
            logger.error(f"Failed to contact Perfion API: {err}")
            raise ConnectionError("Unable to connect to Perfion API") from err

        # Convert to list to allow two passes
        product_data = list(result.data)

        # Calculate base prices (minimum price per ItemNumber) before processing
        self.price_mapping = calculate_base_prices(product_data)  # type: ignore
        logger.info(f"Calculated base prices for {len(self.price_mapping)} products")

        for product_row in product_data:
            # Yield product data as ProductRow
            yield product_row  # type: ignore

    def build_product_ids(self, row: ProductRow) -> dict[str, str]:
        """Extract product identification fields."""
        return {
            "productnumber": str(row.get("ItemNumber", ""))
        }

    def build_product_attrs(self, row: ProductRow, brand: str) -> dict[str, Any]:
        """Build product attributes dictionary from row data."""
        return {
            "name": build_name(row, brand),
            "package": DEFAULT_PACKAGE,
            "price": get_base_price(row, self.price_mapping),
            "description": wrap_style(build_description(row)),
            "category": get_categories(row),
            "brand": normalize_string(brand),
            "page_title": build_page_title(row, brand),
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
            item_number = row.get("ItemNumber", "unknown")
            logger.error(f"Failed to create product {item_number}: {err}")
            pretty_validation_error(err)
            raise

    def add_variants(self, row: ProductRow, product: ThirdPartyProduct) -> None:
        """
        Add color, size, and image variants to product with price differentials.

        Colors typically have no price differential, but sizes may vary in price.
        """
        color = row.get("ERPColor")
        if color:
            # Colors always have 0 price differential (same price for all colors)
            append_if_not_exists((color, 0.0), product.colors)
            logger.debug(f"Added color '{color}' to product {product.productnumber}")

        size = row.get("TSizeNewDW")
        if size:
            # Calculate price differential for this size variant
            variant_price = get_price(row)
            size_price_diff = calculate_variant_price(variant_price, product.price)

            logger.debug(
                f"Adding size '{size}' variant with price differential {size_price_diff} "
                f"(variant: {variant_price}, base: {product.price}) to product {product.productnumber}"
            )

            append_if_not_exists((size, size_price_diff), product.sizing)

        image_url = row.get("BaseProductImageUrl")
        if color and image_url:
            append_if_not_exists((color, image_url), product.images)
            logger.debug(f"Added image for color '{color}' to product {product.productnumber}")

    def load_products(self) -> List[ThirdPartyProduct]:
        """
        Load and process all products from the Perfion API.

        Orchestrates: fetching, filtering, creating/updating products, and adding variants.
        """
        brand = normalize_string(self.settings.ccv_shop.brand)

        for row in self._get_products():
            if not self.should_process_product(row):
                continue

            product = self.create_product(row, brand)
            self.add_variants(row, product)

        return cast(List[ThirdPartyProduct], self.get_all(self.product))
