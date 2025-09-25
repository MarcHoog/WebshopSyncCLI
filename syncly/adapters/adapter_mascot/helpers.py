import logging

from pydantic import ValidationError
from syncly.config.yaml_settings import SynclySettings
from syncly.intergrations.ccvshop.models.third_party import ThirdPartyProduct
from syncly.helpers import (
    wrap_style,
    xlsx_bytes_to_list,
    csv_bytes_to_list,
    normalize_string,
    append_if_not_exists,
    to_float,
    pretty_validation_error
)
from enum import Enum
from typing import TypedDict, Optional, List, Any, Union, Generator, Tuple, cast
from syncly.intergrations.ccvshop.adapters.adapter_third_party import ThirdPartyAdapter

logger = logging.getLogger(__name__)

def _build_name(pd: ProductRow, brand_normalized: str) -> str:
    parts = [brand_normalized, pd.get("article_quality_number")]
    if pd.get("product_name_old"):
        pn_old = pd["product_name_old"] # type: ignore |
        pn_old_parts = pn_old.split(" ")
        pn_old = " ".join(pn_old_parts[1:])
        parts.append(pn_old)

    parts.append(pd.get("product_type"))
    return " ".join(str(p) for p in parts if p)

def _build_description(pd: ProductRow) -> str:
    items = [item.strip() for item in str(pd.get('usp_text', "")).split(';') if item.strip()]
    list_items = "\n  ".join(f"<li>{item}</li>" for item in items)
    formated_usp_text =  f"<ul>\n  {list_items}\n</ul>"
    technical_text = pd.get('technical_text', "")

    return f"""
        {technical_text}
        <br>
        <br>
        <br>
        <br>
        {formated_usp_text}
    """


def _build_meta_description(pd: ProductRow) -> str:
    technical_text = pd.get('technical_text', "") or ""
    if len(technical_text) >= 317:
        technical_text = technical_text[:317]

    return f"{technical_text}..."



def _get_price(pd: ProductRow) -> float:
    raw = pd.get("price")
    if raw is None or raw == "":
        return 0.0
    try:
        return to_float(str(raw))
    except Exception:
        logger.warning("Failed to parse price %r; defaulting to 0.0", raw)
        return 0.0


def _is_stocked(pd: ProductRow) -> bool:
    flag = f"{pd.get('stock_status', '')}".strip().lower()
    if flag in {StockFlag.GREEN.value, StockFlag.YELLOW.value}:
        try:
            return int(pd.get("reorder_status") or 0) == 1
        except (TypeError, ValueError):
            return False
    return False

def _create_availablity_mapping(csv_bytes) -> Any:
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


def _is_excluded(pd: ProductRow, settings: SynclySettings) -> bool:
    excluded = [normalize_string(set) for set in settings.mascot.excluded_product_types]
    if normalize_string(str(pd.get('product_type'))) in excluded:
        return True

    return False
