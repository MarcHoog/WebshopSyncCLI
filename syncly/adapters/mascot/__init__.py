"""
Mascot Third-Party Adapter

This adapter processes product data from Mascot XLSX files and converts
them into ThirdPartyProduct instances for synchronization with the CCV shop.

Data Flow:
1. Read XLSX files (product data + availability) from FTP connection
2. Parse rows into ProductRow TypedDict
3. Merge availability data with product data
4. Filter products (stock status, exclusions)
5. Transform to ThirdPartyProduct format
6. Add variants (colors, sizes, images)
"""

import logging
from pydantic import ValidationError
from typing import List, Any, Generator, Tuple, cast

from syncly.helpers import (
    wrap_style,
    xlsx_bytes_to_list,
    normalize_string,
    append_if_not_exists,
    pretty_validation_error,
)
from ..third_party import ThirdPartyAdapter
from .models import ProductRow
from .helpers import (
    parse_product_row,
    create_availability_mapping,
    is_excluded,
    build_name,
    build_description,
    build_meta_description,
    calculate_base_prices,
    get_base_price,
    get_price,
    calculate_variant_price,
)
from .constants import DEFAULT_PACKAGE
from ...models.third_party import ThirdPartyProduct


logger = logging.getLogger(__name__)


class MascotAdapter(ThirdPartyAdapter):
    """
    Adapter for processing Mascot product data.

    This adapter reads XLSX files containing Mascot product information
    and transforms them into standardized ThirdPartyProduct objects.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.image_mode = "contain"
        self.price_mapping: dict[str, float] = {}

    def __str__(self) -> str:
        return "MascotAdapter"

    def should_process_product(self, row: ProductRow) -> bool:
        """Check if product should be processed based on exclusion rules."""
        return not is_excluded(row, self.settings)

    def build_product_ids(self, row: ProductRow) -> dict[str, str]:
        """Extract product identification fields."""
        return {"productnumber": str(row.get("article_number", ""))}

    def build_product_attrs(self, row: ProductRow, brand: str) -> dict[str, Any]:
        """Build product attributes dictionary from row data."""
        name = build_name(row, brand)
        return {
            "name": name,
            "package": DEFAULT_PACKAGE,
            "price": get_base_price(row, self.price_mapping),
            "description": wrap_style(build_description(row)),
            "category": [str(row.get("product_type"))],
            "brand": normalize_string(brand),
            "page_title": f"{name} ",
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
            raise

    def add_variants(self, row: ProductRow, product: ThirdPartyProduct) -> None:
        """Add color, size, and image variants to product."""
        color = row.get("color")
        if color:
            # Colors always have 0 price differential
            append_if_not_exists((color, 0.0), product.colors)

        size = row.get("eu_size_part1")
        size_part2 = row.get("eu_size_part2")
        if size:
            if size_part2 and size_part2 != "ONE":
                size = f"{size}{size_part2}"

            # Calculate price differential for this size variant
            variant_price = calculate_variant_price(get_price(row), product.price)
            logger.info(
                f"Adding size {size} variant with price {variant_price} to product {product.productnumber}"
            )
            append_if_not_exists((size, variant_price), product.sizing)

        image_url = row.get("product_image_1000px")
        if color and image_url:
            append_if_not_exists((color, image_url), product.images)

    def _get_products(self) -> Generator[ProductRow, Any, Any]:  # type: ignore
        """Parse XLSX files and yield ProductRow dictionaries with availability data."""
        assert self.conn, "Connection must be established before reading products"

        with self.conn as client:
            files = set(client.list_files())
            required = {
                self.settings.mascot.product_data,
                self.settings.mascot.availability,
            }
            missing = required - files
            if missing:
                raise ValueError(
                    f"Missing files: {sorted(missing)} (found: {sorted(files)})"
                )

            product_data: List[List[Any]] = xlsx_bytes_to_list(
                client.download_file(self.settings.mascot.product_data),
                include_header=False,
            )

            # Calculate base prices before processing products
            self.price_mapping = calculate_base_prices(product_data)

            availability_csv = client.download_file(
                self.settings.mascot.availability,
            )
            availability_data = create_availability_mapping(availability_csv)

            for product in product_data:
                product_row = parse_product_row(product)

                ean = product_row.get("ean_number")
                if not ean:
                    raise ValueError("Missing ean number")

                avail = availability_data.get(ean, {})
                product_row["stock_status"] = avail.get("stock_status")
                product_row["reorder_status"] = avail.get("reorder_status")

                yield product_row

    def load_products(self) -> List[ThirdPartyProduct]:
        """
        Load and process all products from the data source.

        Orchestrates: reading, filtering, creating/updating products, and adding variants.
        """
        brand = normalize_string(self.settings.ccv_shop.brand)

        for row in self._get_products():
            if not self.should_process_product(row):
                continue

            product = self.create_product(row, brand)
            self.add_variants(row, product)

        return cast(List[ThirdPartyProduct], self.get_all(self.product))
