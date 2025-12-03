"""Helper functions for Perfion adapter data transformation."""

import logging
from typing import List, Dict, Any

from .models import ProductRow
from .constants import META_DESCRIPTION_MAX_LENGTH

logger = logging.getLogger(__name__)


def build_name(row: ProductRow, brand: str) -> str:
    """Construct product name from row data and brand."""
    item_name = row.get("ItemName", "")
    return f"{brand} {item_name}"


def build_page_title(row: ProductRow, brand: str) -> str:
    """Build page title for SEO including brand, name, and item number."""
    item_name = row.get("ItemName", "")
    item_number = row.get("ItemNumber", "")
    return f"{brand} {item_name} ({item_number})"


def build_description(row: ProductRow) -> str:
    """Format product description, handling None values."""
    description = row.get("Description")
    if not description:
        return ""

    return str(description).strip()


def build_meta_description(row: ProductRow) -> str:
    """Build SEO meta description, truncated with ellipsis."""
    description = row.get("Description", "")
    if not description:
        return ""

    # Strip HTML tags (e.g., <p>)
    description_text = str(description).strip().strip("<p>").strip()

    if len(description_text) >= META_DESCRIPTION_MAX_LENGTH:
        description_text = description_text[:META_DESCRIPTION_MAX_LENGTH]

    return f"{description_text}..."


def get_price(row: ProductRow) -> float:
    """Extract and validate price from product row, defaults to 0.0 if invalid."""
    raw = row.get("ERPGrossPrice1")
    if raw is None:
        return 0.0

    try:
        return float(raw)
    except (TypeError, ValueError):
        logger.warning(f"Invalid price {raw} for product, defaulting to 0.0")
        return 0.0


def get_categories(row: ProductRow) -> list[str]:
    """Extract categories from product row."""
    category = row.get("Category")
    if not category:
        return []

    return [str(category)]


def calculate_base_prices(product_data: List[ProductRow]) -> Dict[str, float]:
    """
    Calculate base prices for all products, returning mapping of ItemNumber -> minimum price.

    Since Perfion API returns one row per variant (color/size combination),
    we need to find the minimum price across all variants of the same product.
    """
    price_mapping: Dict[str, float] = {}

    for row in product_data:
        item_number = row.get("ItemNumber")
        price = get_price(row)

        if not item_number:
            continue

        if price <= 0:
            continue

        # Store minimum price for each item_number
        if item_number not in price_mapping or price < price_mapping[item_number]:
            price_mapping[item_number] = price
            logger.debug(f"Updated base price for {item_number}: {price}")

    return price_mapping


def get_base_price(row: ProductRow, price_mapping: Dict[str, float]) -> float:
    """Extract base price from price mapping using ItemNumber as key, defaults to 0.0 if not found."""
    item_number = row.get("ItemNumber")
    if not item_number:
        return 0.0

    return price_mapping.get(item_number, 0.0)


def calculate_variant_price(variant_price: float, base_price: float) -> float:
    """
    Calculate price differential between variant and base price.

    Returns the difference, which will be 0.0 for the cheapest variant.
    """
    if variant_price <= 0 or base_price <= 0:
        return 0.0

    differential = round(variant_price - base_price, 2)
    return max(0.0, differential)
