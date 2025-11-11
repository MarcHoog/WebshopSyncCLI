"""
Helper functions for HydroWear adapter data transformation.
"""

import logging
from typing import List, Any, Dict

from .models import ProductRow
from .constants import META_DESCRIPTION_MAX_LENGTH

logger = logging.getLogger(__name__)


def parse_product_row(product: List[Any]) -> ProductRow:
    """Convert a list of product values into a ProductRow dictionary."""
    product_row: ProductRow = {}
    for i, field in enumerate(ProductRow.__annotations__):
        if i < len(product):
            product_row[field] = product[i]
        else:
            product_row[field] = None
    return product_row


def calculate_base_prices(product_data: List[List[Any]]) -> Dict[str, float]:
    """Calculate base prices for all products, returning mapping of model -> minimum price."""
    price_mapping: Dict[str, float] = {}

    for product in product_data:
        row = parse_product_row(product)
        model = row.get("model")
        price = row.get("gross_price")

        if not model:
            continue

        if price is None:
            continue

        try:
            price_float = price
        except (TypeError, ValueError):
            logger.warning(f"Invalid price {price} for model {model}, skipping")
            continue

        # Store minimum price for each model
        if model not in price_mapping or price_float < price_mapping[model]:
            price_mapping[model] = price_float

    return price_mapping


def build_name(row: ProductRow) -> str:
    """Construct product name from row data and brand."""
    return f"{row.get('article_name_nl')} ({row.get('model')})"


def build_page_title(row: ProductRow) -> str:
    """Build page title for SEO."""
    return build_name(row)


def build_description(row: ProductRow) -> str:
    """Format product description from article description."""
    description = row.get("article_description_nl", "")
    if not description:
        return ""

    return str(description).strip()


def build_meta_description(row: ProductRow) -> str:
    """Build SEO meta description from article description, truncated with ellipsis."""
    description = row.get("article_description_nl")
    if not description:
        return ""

    description_text = str(description).strip()

    if len(description_text) >= META_DESCRIPTION_MAX_LENGTH:
        description_text = description_text[:META_DESCRIPTION_MAX_LENGTH]

    return f"{description_text}..."


def get_base_price(row: ProductRow, price_mapping: Dict[str, float]) -> float:
    """Extract base price from price mapping using model as key, defaults to 0.0 if not found."""
    model = row.get("model")
    if not model:
        return 0.0

    return price_mapping.get(model, 0.0)


def get_price(row: ProductRow) -> float:
    """Extract raw price from product row, defaults to 0.0 if invalid."""
    raw = row.get("gross_price")
    if raw is None:
        return 0.0

    try:
        return float(raw)
    except (TypeError, ValueError):
        logger.warning(f"Invalid price {raw} for product, defaulting to 0.0")
        return 0.0


def calculate_variant_price(variant_price: float, base_price: float) -> float:
    """Calculate price differential between variant and base price."""
    if variant_price <= 0 or base_price < 0:
        return 0.0

    differential = round(variant_price - base_price, 2)
    logging.info(
        f"Calculated price differential {differential} for variant {variant_price} and base {base_price}"
    )
    return max(0.0, differential)


def get_categories(row: ProductRow) -> list[str]:
    """Extract categories from product row."""
    return []
