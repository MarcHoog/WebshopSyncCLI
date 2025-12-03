"""
Helper functions for Elten adapter data transformation.
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
            value = product[i]
            # Clean empty strings to None
            if value == "" or (isinstance(value, str) and value.strip() == ""):
                product_row[field] = None
            else:
                product_row[field] = value
        else:
            product_row[field] = None
    return product_row


def calculate_base_prices(product_data: List[List[Any]]) -> Dict[str, float]:
    """
    Calculate base prices for all products, returning mapping of article_nr -> minimum price.

    In Elten's case, the base price is determined by the smallest size in each article number.
    """
    price_mapping: Dict[str, float] = {}

    for product in product_data:
        row = parse_product_row(product)
        article_nr = row.get("manufacturer_article_nr")
        list_price = row.get("list_price")

        if not article_nr:
            continue

        if list_price is None:
            continue

        try:
            # Handle both string and float prices
            if isinstance(list_price, str):
                # Remove any whitespace and replace comma with period for European format
                list_price = list_price.strip().replace(",", ".")
            price_float = float(list_price)
        except (TypeError, ValueError):
            logger.warning(f"Invalid price {list_price} for article {article_nr}, skipping")
            continue

        # Store minimum price for each article number (base model)
        if article_nr not in price_mapping or price_float < price_mapping[article_nr]:
            price_mapping[article_nr] = price_float

    return price_mapping


def build_name(row: ProductRow) -> str:
    """Construct product name from row data."""
    article_name = row.get("manufacturer_article_name", "")
    article_nr = row.get("manufacturer_article_nr", "")

    if article_name and article_nr:
        return f"{article_name} ({article_nr})"
    elif article_name:
        return article_name
    elif article_nr:
        return article_nr
    else:
        return "Unknown Product"


def build_page_title(row: ProductRow) -> str:
    """Build page title for SEO."""
    return build_name(row)


def build_description(row: ProductRow) -> str:
    """Format product description from article descriptions."""
    description_1 = row.get("manufacturer_article_description_1", "")
    description_2 = row.get("manufacturer_article_description_2", "")

    # Combine both descriptions if available
    if description_1 and description_2:
        return f"{description_1}\n\n{description_2}".strip()
    elif description_1:
        return str(description_1).strip()
    elif description_2:
        return str(description_2).strip()
    else:
        return ""


def build_meta_description(row: ProductRow) -> str:
    """Build SEO meta description from article description, truncated with ellipsis."""
    description = build_description(row)
    if not description:
        return ""

    description_text = description.strip()

    if len(description_text) >= META_DESCRIPTION_MAX_LENGTH:
        description_text = description_text[:META_DESCRIPTION_MAX_LENGTH]
        return f"{description_text}..."

    return description_text


def get_base_price(row: ProductRow, price_mapping: Dict[str, float]) -> float:
    """Extract base price from price mapping using article number as key, defaults to 0.0 if not found."""
    article_nr = row.get("manufacturer_article_nr")
    if not article_nr:
        return 0.0

    return price_mapping.get(article_nr, 0.0)


def get_price(row: ProductRow) -> float:
    """Extract raw price from product row, defaults to 0.0 if invalid."""
    raw = row.get("list_price")
    if raw is None:
        return 0.0

    try:
        # Handle both string and float prices
        if isinstance(raw, str):
            # Remove any whitespace and replace comma with period for European format
            raw = raw.strip().replace(",", ".")
        return float(raw)
    except (TypeError, ValueError):
        logger.warning(f"Invalid price {raw} for product, defaulting to 0.0")
        return 0.0


def calculate_variant_price(variant_price: float, base_price: float) -> float:
    """Calculate price differential between variant and base price."""
    if variant_price <= 0 or base_price < 0:
        return 0.0

    differential = round(variant_price - base_price, 2)
    logger.debug(
        f"Calculated price differential {differential} for variant {variant_price} and base {base_price}"
    )
    return max(0.0, differential)


def get_categories(row: ProductRow) -> list[str]:
    """Extract categories from product row."""
    categories = []

    # Use manufacturer article group as category if available
    article_group = row.get("manufacturer_article_group")
    if article_group:
        categories.append(article_group)

    return categories


def parse_size_range(size_range: str) -> list[str]:
    """
    Parse size range string (e.g., '36 - 48') into list of sizes.

    Returns individual sizes as strings.
    """
    if not size_range:
        return []

    # Handle range format like "36 - 48"
    if "-" in size_range:
        parts = size_range.split("-")
        if len(parts) == 2:
            try:
                start = int(parts[0].strip())
                end = int(parts[1].strip())
                return [str(size) for size in range(start, end + 1)]
            except (ValueError, TypeError):
                logger.warning(f"Could not parse size range: {size_range}")
                return [size_range]

    # Return as-is if not a range
    return [size_range.strip()]


def get_brand_from_article_group(row: ProductRow) -> str:
    """
    Extract and map brand from manufacturer_article_group field.

    Maps:
    - "JORI Professional" -> "jori"
    - "LOWA Work Collection" -> "Lowa"
    - All ELTEN variants (ELTEN BUSINESS, ELTEN WELLMAXX, Kids by ELTEN, etc.) -> "Elten"

    Defaults to "Elten" if no match found.
    """
    article_group = row.get("manufacturer_article_group", "").strip()

    if not article_group:
        return "Elten"

    # Check for JORI
    if "JORI" in article_group.upper():
        return "jori"

    # Check for LOWA
    if "LOWA" in article_group.upper():
        return "Lowa"

    # Default to Elten (covers all ELTEN variants and Kids by ELTEN)
    return "Elten"


def build_technical_specs(row: ProductRow) -> str:
    """Build technical specifications description from material attributes."""
    specs = []

    # Material specifications
    if row.get("upper_material"):
        specs.append(f"Bovenmateriaal: {row['upper_material']}")
    if row.get("lining_material"):
        specs.append(f"Voering: {row['lining_material']}")
    if row.get("insole"):
        specs.append(f"Binnenzool: {row['insole']}")
    if row.get("sole"):
        specs.append(f"Zool: {row['sole']}")

    # Safety features
    if row.get("toe_cap"):
        specs.append(f"Neus: {row['toe_cap']}")
    if row.get("puncture_protection"):
        specs.append(f"Antiperforatie: {row['puncture_protection']}")

    # Norm/Standard
    if row.get("norm"):
        specs.append(f"Norm: {row['norm']}")

    # Additional info
    if row.get("additional_info_1"):
        specs.append(row["additional_info_1"])
    if row.get("additional_info_2"):
        specs.append(row["additional_info_2"])

    return "\n".join(specs) if specs else ""
