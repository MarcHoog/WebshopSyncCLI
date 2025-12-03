"""
Elten Third-Party Adapter

This adapter processes product data from Elten CSV files and converts
them into ThirdPartyProduct instances for synchronization with the CCV shop.

Data Flow:
1. Read CSV file from connection
2. Parse rows into ProductRow TypedDict
3. Filter and validate products
4. Transform to ThirdPartyProduct format
5. Add variants (sizes) based on size ranges
"""

import json
import logging
from typing import Any, Generator, List, Tuple, cast

from pydantic import ValidationError

from syncly.helpers import (
    append_if_not_exists,
    base64_image_from_file_contain,
    csv_bytes_to_list,
    normalize_string,
    pretty_validation_error,
    wrap_style,
)

from ...clients.local import LocalFileClient
from ...models.third_party import ThirdPartyProduct
from ..third_party import ThirdPartyAdapter
from .constants import DEFAULT_PACKAGE
from .helpers import (
    build_description,
    build_meta_description,
    build_name,
    build_page_title,
    build_technical_specs,
    calculate_base_prices,
    calculate_variant_price,
    get_base_price,
    get_brand_from_article_group,
    get_categories,
    get_price,
    parse_product_row,
    parse_size_range,
)
from .models import ProductRow

logger = logging.getLogger(__name__)


class EltenAdapter(ThirdPartyAdapter):
    """
    Adapter for processing Elten product data.

    This adapter reads CSV files containing Elten product information
    and transforms them into standardized ThirdPartyProduct objects.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.image_mode = "contain"
        self.conn: LocalFileClient = self.conn
        self.price_mapping: dict[str, float] = {}
        self.pictures_folder_path: str | None = None

    def __str__(self) -> str:
        return "EltenAdapter"

    def get_product_data(self) -> Generator[ProductRow, Any, Any]:
        """Parse CSV file, calculate base prices, and yield ProductRow dictionaries."""
        assert self.conn, "Connection must be established before reading products"

        with self.conn as file:
            # Elten CSV appears to be tab-separated based on the sample data
            product_data = csv_bytes_to_list(
                file.read(), include_header=False, seperator=";", encoding="utf-8"
            )
            self.price_mapping = calculate_base_prices(product_data)
            for product in product_data:
                yield parse_product_row(product)

    def should_process_product(self, row: ProductRow) -> bool:
        """Check if product should be processed based on business rules."""
        print(json.dumps(row, indent=4))
        if not row.get("manufacturer_article_nr"):
            logger.debug("Skipping product without article number")
            return False

        if not row.get("manufacturer_article_name"):
            logger.debug("Skipping product without article name")
            return False

        # Skip products without pricing
        if not row.get("list_price"):
            logger.debug(
                f"Skipping product {row.get('manufacturer_article_nr')} without price"
            )
            return False

        return True

    def build_product_ids(self, row: ProductRow) -> dict[str, str]:
        """Extract product identification fields."""
        # Use manufacturer article number as the unique identifier
        return {"productnumber": str(row.get("manufacturer_article_nr", ""))}

    def build_product_attrs(self, row: ProductRow, brand: str) -> dict[str, Any]:
        """Build product attributes dictionary from row data."""
        description = build_description(row)
        technical_specs = build_technical_specs(row)

        # Combine description with technical specs
        full_description = description
        if technical_specs:
            if full_description:
                full_description = f"{full_description}\n\n<h3>Technical Specifications</h3>\n{technical_specs}"
            else:
                full_description = (
                    f"<h3>Technical Specifications</h3>\n{technical_specs}"
                )

        return {
            "name": build_name(row),
            "package": DEFAULT_PACKAGE,
            "description": wrap_style(full_description),
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
            article_num = row.get("manufacturer_article_nr", "unknown")
            logger.error(f"Failed to create product {article_num}: {err}")
            pretty_validation_error(err)
            raise err

    def add_size_variant(self, row: ProductRow, product: ThirdPartyProduct) -> None:
        """
        Add size variant to product.

        Elten products have individual size entries in the CSV, so each row
        represents a specific size variant.
        """
        size = row.get("manufacturer_article_size")
        if not size:
            logger.debug(
                f"No size found for product {product.productnumber}, skipping variant"
            )
            return

        # Normalize size string
        size = normalize_string(str(size))

        # Calculate price differential from base price
        variant_price = calculate_variant_price(get_price(row), product.price)

        logger.debug(
            f"Adding size {size} variant with price differential {variant_price} "
            f"to product {product.productnumber}"
        )

        append_if_not_exists((size, variant_price), product.sizing)

    def add_variants(self, row: ProductRow, product: ThirdPartyProduct) -> None:
        """Add size variants to product."""
        self.add_size_variant(row, product)

    def add_image_from_media(self, row: ProductRow, product: ThirdPartyProduct) -> None:
        """
        Add product image from the media field if available.

        Images are stored in a local folder and referenced by filename in the CSV.
        Only adds the image once per product (not per size variant).
        """
        if not self.pictures_folder_path:
            logger.debug("No pictures folder path configured, skipping image")
            return

        media_filename = row.get("media")
        if not media_filename:
            logger.debug(f"No media filename for product {product.productnumber}, skipping image")
            return

        # Build the full path to the image file
        import os
        image_path = os.path.join(self.pictures_folder_path, media_filename)

        # Check if the file exists
        if not os.path.exists(image_path):
            logger.warning(f"Image file not found: {image_path}")
            return

        # Add the image path to the product's images list
        # Using empty string for color since Elten products don't have color variants
        image_entry = ("", image_path)
        if image_entry not in product.images:
            product.images.append(image_entry)
            logger.debug(f"Added image {media_filename} to product {product.productnumber}")

    def process_images(self, product: ThirdPartyProduct, mode: str = "crop"):
        """
        Override to process images from local files instead of URLs.

        Process and add images to the product from local file paths.
        """
        image_height = self.settings.ccv_shop.image_height
        image_width = self.settings.ccv_shop.image_width

        for color, file_path in product.images:
            if not self.color_mapping.get(color) and color:
                logger.warning(
                    f"Color {color} cannot be mapped, This image might be for a product that cannot be orderd"
                )
            try:
                if mode == "contain":
                    b64_img = base64_image_from_file_contain(
                        file_path, (image_width, image_height)
                    )
                else:
                    # For now, we only support "contain" mode for local files
                    logger.warning(f"Unsupported image mode '{mode}', using 'contain' instead")
                    b64_img = base64_image_from_file_contain(
                        file_path, (image_width, image_height)
                    )

            except Exception as e:
                logger.error(f"Failed to process image from file: {file_path}. Error: {e}")
                continue

            product_photo, created = self.get_or_instantiate(
                self.product_photo,
                {
                    "productnumber": product.productnumber,
                    "file_type": "png",
                    "alttext": file_path,
                },
                {"source": b64_img},
            )
            if created:
                self.add_child(product, product_photo)

    def load_products(self) -> List[ThirdPartyProduct]:
        """
        Load and process all products from the data source.

        Orchestrates: reading, filtering, creating/updating products, adding variants, and images.
        """
        for row in self.get_product_data():
            if not self.should_process_product(row):
                continue

            # Extract brand from the manufacturer_article_group field
            brand = get_brand_from_article_group(row)
            product = self.create_product(row, brand)
            self.add_variants(row, product)
            self.add_image_from_media(row, product)

        return cast(List[ThirdPartyProduct], self.get_all(self.product))
