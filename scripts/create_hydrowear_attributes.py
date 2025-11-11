"""
Script to create CCV attributes (colors and sizing) from HydroWear CSV data.

This script:
1. Reads a HydroWear CSV file using LocalFileClient
2. Extracts unique Dutch color values from the 'colour_nl' column
3. Extracts unique size values from the 'sizes' column
4. Creates two attributes in CCV Shop via the API:
   - "Kleuren" (Colors) with Dutch color values
   - "Maten" (Sizes) with size values
"""
import logging
import os
from typing import Set

from syncly.clients.local import LocalFileClient
from syncly.clients.ccv.client import CCVClient
from syncly.helpers import xlsx_bytes_to_list
from syncly.adapters.hydrowear.helpers import parse_product_row
from syncly.adapters.hydrowear.models import ProductRow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_unique_colors(rows: list[ProductRow]) -> Set[str]:
    """Extract unique Dutch color values from product rows."""
    colors: Set[str] = set()

    for row in rows:
        colour_nl = row.get('colour_nl')
        if colour_nl and str(colour_nl).strip():
            colors.add(str(colour_nl).strip())

    logger.info(f"Found {len(colors)} unique colors: {sorted(colors)}")
    return colors


def extract_unique_sizes(rows: list[ProductRow]) -> Set[str]:
    """Extract unique size values from product rows."""
    sizes: Set[str] = set()

    for row in rows:
        size = row.get('sizes')
        if size and str(size).strip():
            sizes.add(str(size).strip())

    logger.info(f"Found {len(sizes)} unique sizes: {sorted(sizes)}")
    return sizes


def read_csv_file(file_path: str) -> list[ProductRow]:
    """Read and parse CSV file into ProductRow objects."""
    logger.info(f"Reading CSV file: {file_path}")

    with LocalFileClient(file_path) as client:
        csv_bytes = client.read()
        product_data = xlsx_bytes_to_list(csv_bytes, include_header=False)

        rows = [parse_product_row(product) for product in product_data]
        logger.info(f"Parsed {len(rows)} rows from CSV")

        return rows


def create_color_attribute(ccv_client: CCVClient, colors: Set[str]) -> None:
    """Create color attribute and add all color values."""
    logger.info("Creating color attribute 'Kleuren'")

    # Create the attribute
    color_attr_body = {
        "type": "option_menu",
        "name": "Kleuren (Hydrowear)",
    }

    result = ccv_client.attributes.create_attribute(color_attr_body)

    if result.data:
        attribute_id = result.data.get('id')
        logger.info(f"Color attribute created with ID: {attribute_id}")

        # Add color values
        for color in sorted(colors):
            logger.info(f"Adding color value: {color}")
            value_body = {
                "name": color,
                "default_price": 0
            }
            ccv_client.attributes.crate_attribute_value(str(attribute_id), value_body)

        logger.info(f"Added {len(colors)} color values to attribute")
    else:
        logger.error("Failed to create color attribute")


def create_sizing_attribute(ccv_client: CCVClient, sizes: Set[str]) -> None:
    """Create sizing attribute and add all size values."""
    logger.info("Creating sizing attribute 'Maten'")

    # Create the attribute
    sizing_attr_body = {
        "type": "option_menu",
        "name": "Maten (Hydrowear)",
    }

    result = ccv_client.attributes.create_attribute(sizing_attr_body)

    if result.data:
        attribute_id = result.data.get('id')
        logger.info(f"Sizing attribute created with ID: {attribute_id}")

        # Add size values
        for size in sorted(sizes):
            logger.info(f"Adding size value: {size}")
            value_body = {
                "name": size,
                "default_price": 0
            }
            ccv_client.attributes.crate_attribute_value(str(attribute_id), value_body)

        logger.info(f"Added {len(sizes)} size values to attribute")
    else:
        logger.error("Failed to create sizing attribute")


def main(csv_file_path: str):
    """
    Main function to create CCV attributes from HydroWear CSV.

    Args:
        csv_file_path: Path to the HydroWear CSV file
    """
    logger.info("Starting attribute creation process")

    # Step 1: Read and parse CSV
    rows = read_csv_file(csv_file_path)

    # Step 2: Extract unique values
    colors = extract_unique_colors(rows)
    sizes = extract_unique_sizes(rows)

    # Step 3: Initialize CCV client
    ccv_public_key = os.getenv('CCV_PUBLIC_KEY')
    ccv_secret_key = os.getenv('CCV_SECRET_KEY')
    ccv_base_url = os.getenv('CCV_BASE_URL')

    if not all([ccv_public_key, ccv_secret_key, ccv_base_url]):
        raise ValueError("Missing CCV credentials. Ensure CCV_PUBLIC_KEY, CCV_SECRET_KEY, and CCV_BASE_URL are set.")

    logger.info(f"Initializing CCV client for {ccv_base_url}")
    ccv_client = CCVClient(
        public_key=ccv_public_key,
        secret_key=ccv_secret_key,
        base_url=ccv_base_url
    )

    # Step 4: Create attributes
    create_color_attribute(ccv_client, colors)
    create_sizing_attribute(ccv_client, sizes)

    logger.info("Attribute creation process completed successfully")


if __name__ == "__main__":
    CSV_FILE_PATH = "hydrowear2025.xlsx"

    main(CSV_FILE_PATH)
