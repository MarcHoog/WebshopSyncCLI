"""Type definitions for CCV Shop adapter API responses."""

from typing import TypedDict, Optional, List, Any


class BrandItem(TypedDict, total=False):
    """CCV Shop brand item from API response."""
    id: int
    name: str


class PackageItem(TypedDict, total=False):
    """CCV Shop package item from API response."""
    id: int
    name: str


class CategoryItem(TypedDict, total=False):
    """CCV Shop category item from API response."""
    id: int
    name: str


class AttributeItem(TypedDict, total=False):
    """CCV Shop attribute item from API response."""
    id: int
    name: str


class AttributeValueItem(TypedDict, total=False):
    """CCV Shop attribute value item from API response."""
    id: int
    name: str


class BrandRef(TypedDict):
    """Brand reference in product response."""
    id: int


class PackageRef(TypedDict):
    """Package reference in product response."""
    id: int


class ProductItem(TypedDict, total=False):
    """CCV Shop product item from API response."""
    id: int
    name: str
    productnumber: str
    description: str
    price: float
    page_title: str
    meta_description: str
    meta_keywords: str
    brand: BrandRef
    package: PackageRef


class ProductToCategoryItem(TypedDict, total=False):
    """Product to category mapping item from API response."""
    id: int
    product_id: int
    category_id: int


class AttributeValueToProductItem(TypedDict, total=False):
    """Attribute value to product mapping from API response."""
    id: int
    optionname: str
    optionvalue_name: str


class ProductPhotoItem(TypedDict, total=False):
    """Product photo item from API response."""
    id: int
    alttext: str
    deeplink: str


class APIResponse(TypedDict):
    """Generic API response wrapper."""
    items: List[Any]
