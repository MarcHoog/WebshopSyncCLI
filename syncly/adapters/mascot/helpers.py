"""
Helper functions for Mascot adapter data transformation.
"""

import logging
from typing import List, Any, Dict

from .models import ProductRow, StockFlag
from .constants import META_DESCRIPTION_MAX_LENGTH
from ...settings import Settings
from ...helpers import (
    csv_bytes_to_list,
    normalize_string,
    to_float,
)

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


def build_name(row: ProductRow, brand_normalized: str) -> str:
    """Construct product name from row data and brand."""
    parts = [brand_normalized.capitalize(), row.get("article_quality_number")]
    if row.get("product_name_old"):
        pn_old = row["product_name_old"]  # type: ignore
        pn_old_parts = pn_old.split(" ")
        pn_old = " ".join(pn_old_parts[1:])
        parts.append(pn_old)

    parts.append(row.get("product_type"))
    return " ".join(str(p) for p in parts if p)


def build_description(row: ProductRow) -> str:
    """Format product description from USP text and technical text."""
    items = [
        item.strip() for item in str(row.get("usp_text", "")).split(";") if item.strip()
    ]
    list_items = "\n  ".join(f"<li>{item}</li>" for item in items)
    formated_usp_text = f"<ul>\n  {list_items}\n</ul>"
    technical_text = row.get("technical_text", "")

    return f"""
        {technical_text}
        <br>
        <br>
        <br>
        <br>
        {formated_usp_text}
    """


def build_meta_description(row: ProductRow) -> str:
    """Build SEO meta description from technical text, truncated with ellipsis."""
    technical_text = row.get("technical_text", "") or ""
    if len(technical_text) >= META_DESCRIPTION_MAX_LENGTH:
        technical_text = technical_text[:META_DESCRIPTION_MAX_LENGTH]

    return f"{technical_text}..."


def get_price(row: ProductRow) -> float:
    """Extract and validate price from product row, defaults to 0.0 if invalid."""
    raw = row.get("price")
    if raw is None or raw == "":
        return 0.0
    try:
        return to_float(str(raw))
    except Exception:
        logger.warning("Failed to parse price %r; defaulting to 0.0", raw)
        return 0.0


def is_stocked(row: ProductRow) -> bool:
    """Check if product is in stock based on stock status and reorder status."""
    flag = f"{row.get('stock_status', '')}".strip().lower()
    if flag in {StockFlag.GREEN.value, StockFlag.YELLOW.value}:
        try:
            return int(row.get("reorder_status") or 0) == 1
        except (TypeError, ValueError):
            return False
    return False


def create_availability_mapping(csv_bytes: bytes) -> Dict[str, Dict[str, Any]]:
    """Parse availability CSV and create mapping from EAN number to stock data."""
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


def is_excluded(row: ProductRow, settings: Settings) -> bool:
    """Check if product type is in the excluded list from settings."""
    excluded = [
        normalize_string(product_type)
        for product_type in settings.mascot.excluded_product_types
    ]
    if normalize_string(str(row.get("product_type"))) in excluded:
        return True

    return False


def calculate_base_prices(product_data: List[List[Any]]) -> Dict[str, float]:
    """Calculate base prices for all products, returning mapping of article_number -> minimum price."""
    price_mapping: Dict[str, float] = {}

    for product in product_data:
        row = parse_product_row(product)
        article_number = row.get("article_number")
        price = row.get("price")

        if not article_number:
            continue

        if price is None or price == "":
            continue

        try:
            price_float = to_float(str(price))
        except (TypeError, ValueError):
            logger.warning(f"Invalid price {price} for article {article_number}, skipping")
            continue

        # Store minimum price for each article_number
        if article_number not in price_mapping or price_float < price_mapping[article_number]:
            price_mapping[article_number] = price_float

    return price_mapping


def get_base_price(row: ProductRow, price_mapping: Dict[str, float]) -> float:
    """Extract base price from price mapping using article_number as key, defaults to 0.0 if not found."""
    article_number = row.get("article_number")
    if not article_number:
        return 0.0

    return price_mapping.get(article_number, 0.0)


def calculate_variant_price(variant_price: float, base_price: float) -> float:
    """Calculate price differential between variant and base price."""
    if variant_price <= 0 or base_price < 0:
        return 0.0

    differential = round(variant_price - base_price, 2)
    logger.info(
        f"Calculated price differential {differential} for variant {variant_price} and base {base_price}"
    )
    return max(0.0, differential)
