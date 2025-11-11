"""Type definitions for Perfion adapter."""

from typing import TypedDict, Optional


class ProductRow(TypedDict, total=False):
    """Type definition for Perfion product data row."""
    ItemNumber: Optional[str]
    ItemName: Optional[str]
    Category: Optional[str]
    ERPGrossPrice1: Optional[float]
    Description: Optional[str]
    ERPColor: Optional[str]
    TSizeNewDW: Optional[str]
    BaseProductImageUrl: Optional[str]
