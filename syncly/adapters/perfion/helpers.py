"""Helper functions for Perfion adapter data transformation."""

import logging

from .constants import META_DESCRIPTION_MAX_LENGTH
from .models import ProductRow

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
