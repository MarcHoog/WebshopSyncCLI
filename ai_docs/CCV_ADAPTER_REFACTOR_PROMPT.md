# CCV Adapter Refactoring Prompt

## Objective
Refactor the CCV adapter (`syncly/adapters/ccv.py`) to follow clean architecture principles. Unlike the third-party adapters (Perfion, HydroWear, Mascot), this is a **destination adapter** that loads data FROM the CCV Shop API. The refactoring will focus on improving type safety, extracting constants, and enhancing maintainability while preserving its distinct purpose.

---

## Current State Analysis

### Adapter Type: Destination Adapter
This adapter extends `diffsync.Adapter` (not `ThirdPartyAdapter`) and loads existing data from the CCV Shop API for synchronization purposes. It reads:
- Brands
- Packages
- Categories
- Attributes and Attribute Values
- Products
- Product-to-Category mappings
- Attribute Values-to-Product mappings
- Product Photos

### Problems in Current Implementation

**File: `syncly/adapters/ccv.py`**

1. **Missing Type Hints**
   - No return types on methods (lines 68, 86, 104, 125, 162, 224, 249, 278, 309)
   - Missing parameter type hints in some places

2. **Magic Numbers**
   - `sleep(0.2)` hardcoded rate limiting (lines 260, 288)
   - `per_page=100` hardcoded (line 290)

3. **Poor Error Messages**
   - Typo: "lickily" should be "likely" (line 221)
   - Generic error messages without context in some places

4. **No Architecture Files**
   - No `constants.py` for rate limiting and pagination values
   - No `models.py` for TypedDict definitions of API responses
   - No `helpers.py` (may not be needed for this adapter)

5. **Repeated Patterns**
   - Similar `get_or_instantiate` patterns across methods
   - Similar item extraction patterns: `cast(dict, result.data).get("items") or []`

6. **No Module Documentation**
   - Missing module-level docstring explaining adapter purpose

---

## Target Architecture

Create a modular structure while respecting the adapter's unique role:

```
syncly/adapters/ccv/
├── __init__.py       # CCVShopAdapter class - orchestration
├── models.py         # TypedDict definitions for API responses
└── constants.py      # Rate limiting, pagination, and other constants
```

**Note:** `helpers.py` may not be necessary for this adapter as it doesn't perform complex data transformations like the source adapters.

---

## Required Implementation Steps

### STEP 1: Create `constants.py`

Extract configuration values and magic numbers:

```python
"""Constants for CCV Shop adapter."""

# Rate limiting
API_RATE_LIMIT_DELAY = 0.2  # Seconds to wait between API calls to avoid hitting limits

# Pagination
DEFAULT_PHOTOS_PER_PAGE = 100
LOAD_ALL_PAGES = -1  # Special value to load all pages
```

---

### STEP 2: Create `models.py`

Define TypedDicts for API response structures:

```python
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
```

---

### STEP 3: Refactor `__init__.py`

#### 3.1 Add Module-Level Docstring

```python
"""
CCV Shop Destination Adapter

This adapter loads existing data from the CCV Shop API for synchronization purposes.
It is a destination adapter that reads the current state of the CCV Shop to compare
against source data from third-party adapters.

Data Loaded:
1. Brands - All brands in the shop
2. Packages - All package types
3. Categories - All product categories
4. Attributes - All product attributes and their values
5. Products - All products under the root category
6. Product-to-Category mappings
7. Attribute Values-to-Product mappings
8. Product Photos

The adapter uses DiffSync to track changes and synchronize between source and destination.
"""
```

#### 3.2 Update Imports

```python
import logging
from time import sleep
from typing import cast, Tuple, Dict, List, Optional

from diffsync import Adapter
from diffsync.enum import DiffSyncModelFlags

from ..helpers import base64_image_from_url, normalize_string
from ..settings import Settings
from ..clients.ccv.client import CCVClient
from ..models.ccv_shop import (
    CCVProduct,
    CCVCategory,
    CCVPackage,
    CCVCategoryToDevice,
    CCVAttribute,
    CCVAttributeValue,
    CCVAttributeValueToProduct,
    CCVProductPhoto,
    CCVBrand,
)
from .constants import API_RATE_LIMIT_DELAY, DEFAULT_PHOTOS_PER_PAGE, LOAD_ALL_PAGES
from .models import (
    BrandItem,
    PackageItem,
    CategoryItem,
    AttributeItem,
    AttributeValueItem,
    ProductItem,
    ProductToCategoryItem,
    AttributeValueToProductItem,
    ProductPhotoItem,
    APIResponse,
)

logger = logging.getLogger(__name__)
```

#### 3.3 Add Complete Type Hints

Add return types to all methods:

```python
class CCVShopAdapter(Adapter):
    """DiffSync Adapter using requests to communicate to CCVShop."""

    product = CCVProduct
    brand = CCVBrand
    category = CCVCategory
    package = CCVPackage
    category_to_device = CCVCategoryToDevice
    attribute = CCVAttribute
    attribute_value = CCVAttributeValue
    attribute_value_to_product = CCVAttributeValueToProduct
    product_photo = CCVProductPhoto

    top_level = ["product"]

    category_map: Dict[int, CCVCategory] = {}
    product_map: Dict[int, CCVProduct] = {}
    package_map: Dict[int, CCVPackage] = {}
    brand_map: Dict[int, CCVBrand] = {}
    attribute_map: Dict[int, CCVAttribute] = {}

    def __str__(self) -> str:
        return "CCVShopAdapter"

    def __init__(
        self,
        *args,
        settings: Settings,
        client: CCVClient,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        if not settings.ccv_shop.root_category:
            raise ValueError("ccv_shop.root_category is not set in settings")

        self.settings = settings
        self.conn = client
        self.root_category: Optional[CCVCategory] = None
```

#### 3.4 Add Type Hints to All Methods

```python
    def load_brands(self) -> None:
        """Load all brands from CCVShop."""
        brands = self.conn.brands.get_brands(total_pages=LOAD_ALL_PAGES)
        brand_items: List[BrandItem] = cast(dict, brands.data).get("items") or []

        for b in brand_items:
            brand, _ = cast(
                Tuple[CCVBrand, bool],
                self.get_or_instantiate(
                    self.brand,
                    {"name": normalize_string(b.get("name", ""))},
                    {"id": b.get("id")},
                ),
            )

            self.brand_map[brand.id] = brand
            brand.model_flags = DiffSyncModelFlags.IGNORE

    def load_packages(self) -> None:
        """Load all packages from CCVShop."""
        packages = self.conn.packages.get_packages(total_pages=LOAD_ALL_PAGES)
        package_items: List[PackageItem] = cast(dict, packages.data).get("items") or []

        for p in package_items:
            package, _ = cast(
                Tuple[CCVPackage, bool],
                self.get_or_instantiate(
                    self.package,
                    {"name": normalize_string(p.get("name", ""))},
                    {"id": p.get("id")},
                ),
            )

            self.package_map[package.id] = package
            package.model_flags = DiffSyncModelFlags.IGNORE

    def load_categories(self) -> None:
        """Load all categories from CCVShop and identify root category."""
        categories = self.conn.categories.get_categories(total_pages=LOAD_ALL_PAGES)
        category_items: List[CategoryItem] = cast(dict, categories.data).get("items") or []

        for c in category_items:
            if c.get("name", "").strip().lower():
                category, _ = cast(
                    Tuple[CCVCategory, bool],
                    self.get_or_instantiate(
                        self.category,
                        {"name": c.get("name")},
                        {"id": c.get("id")},
                    ),
                )

                if category.name == self.settings.ccv_shop.root_category:
                    self.root_category = category

                self.category_map[category.id] = category
                category.model_flags = DiffSyncModelFlags.IGNORE

    def load_attributes(self) -> None:
        """Load all attributes and their values from CCVShop."""
        attributes = self.conn.attributes.get_attributes(total_pages=LOAD_ALL_PAGES)
        attribute_items: List[AttributeItem] = cast(dict, attributes.data).get("items") or []

        for attr in attribute_items:
            attribute, _ = cast(
                Tuple[CCVAttribute, bool],
                self.get_or_instantiate(
                    self.attribute,
                    {"name": normalize_string(attr.get("name"))},
                    {"id": attr.get("id")},
                ),
            )
            self.attribute_map[attribute.id] = attribute
            attribute.model_flags = DiffSyncModelFlags.IGNORE

            attribute_values = self.conn.attributes.get_attribute_values(
                f"{attribute.id}"
            )
            value_items: List[AttributeValueItem] = cast(dict, attribute_values.data).get("items") or []

            for val in value_items:
                value, created = cast(
                    Tuple[CCVAttributeValue, bool],
                    self.get_or_instantiate(
                        self.attribute_value,
                        {
                            "attribute": attribute.name,
                            "value": normalize_string(val["name"]),
                        },
                        {
                            "id": val["id"],
                        },
                    ),
                )

                if created:
                    attribute.add_child(value)

    def load_products(self) -> None:
        """Load all products from the root category."""
        if not self.root_category:
            raise ValueError(
                f"Root category of name {self.settings.ccv_shop.root_category} is not defined"
            )

        logger.info(
            f"Gathering products from root category: {self.root_category.name} | {self.root_category.id}"
        )

        products = self.conn.product.get_products_by_categories(
            f"{self.root_category.id}", total_pages=LOAD_ALL_PAGES
        )
        product_items: List[ProductItem] = cast(dict, products.data).get("items") or []

        for item in product_items:
            name = item.get("name", "")
            product_number = item.get("productnumber", "")

            logger.debug(f"Processing: {product_number}: {name}")

            package = self.package_map.get(item["package"]["id"])
            if not package:
                raise ValueError(
                    f"Package with id {item['package']['id']} cannot be found in package map"
                )

            brand = self.brand_map.get(item["brand"]["id"])
            if not brand:
                raise ValueError(
                    f"Brand with id {item['brand']['id']} cannot be found in brand map"
                )

            try:
                product, _ = cast(
                    Tuple[CCVProduct, bool],
                    self.get_or_instantiate(
                        self.product,
                        {
                            "productnumber": product_number,
                        },
                        {
                            "name": name,
                            "id": item["id"],
                            "package": normalize_string(package.name),
                            "description": item["description"],
                            "price": item["price"],
                            "brand": normalize_string(brand.name),
                            "page_title": item["page_title"],
                            "meta_description": item["meta_description"],
                            "meta_keywords": item["meta_keywords"],
                        },
                    ),
                )
                self.product_map[product.id] = product

            except KeyError as err:
                logger.error(
                    f"KeyError while processing product {product_number}: {err}. "
                    f"Likely missing required fields in API response."
                )

    def load_products_to_category(self) -> None:
        """Load all product-to-category mappings."""
        for cat_id, cat in self.category_map.items():
            prod_to_cat = self.conn.product_to_category.get_product_to_category(
                id=cat_id, total_pages=LOAD_ALL_PAGES
            )
            prod_to_cat_items: List[ProductToCategoryItem] = cast(dict, prod_to_cat.data).get("items") or []

            for item in prod_to_cat_items:
                product = self.product_map.get(item.get("product_id"))
                if product:
                    cat_to_dev, _ = self.get_or_instantiate(
                        CCVCategoryToDevice,
                        {
                            "category_name": cat.name,
                            "productnumber": product.productnumber,
                        },
                        {
                            "id": item["id"],
                            "category_id": cat.id,
                            "product_id": product.id,
                        },
                    )

                    product.add_child(cat_to_dev)

    def load_attribute_values_to_product(self) -> None:
        """Load all attribute values attached to products."""
        products = cast(List[CCVProduct], self.get_all(self.product))

        if not products:
            logger.warning(
                "No products have been loaded in the adapter. If this is expected, "
                "it's not a problem. If not, you might have loaded your objects in the wrong order."
            )
            return

        for product in products:
            sleep(API_RATE_LIMIT_DELAY)

            result = self.conn.product_to_attribute.get_product_to_attribute_values(
                f"{product.id}"
            )
            attribute_items: List[AttributeValueToProductItem] = cast(dict, result.data).get("items") or []

            for item in attribute_items:
                attribute_value_to_product, _ = self.get_or_instantiate(
                    self.attribute_value_to_product,
                    {
                        "productnumber": product.productnumber,
                        "attribute": normalize_string(item["optionname"]),
                        "value": normalize_string(item["optionvalue_name"]),
                    },
                    {"id": item["id"]},
                )

                product.add_child(attribute_value_to_product)

    def load_product_photos(self) -> None:
        """Load all product photos."""
        products = cast(List[CCVProduct], self.get_all(self.product))

        if not products:
            logger.warning(
                "No products have been loaded in the adapter. If this is expected, "
                "it's not a problem. If not, you might have loaded your objects in the wrong order."
            )
            return

        for product in products:
            sleep(API_RATE_LIMIT_DELAY)

            result = self.conn.photos.get_photos(
                per_page=DEFAULT_PHOTOS_PER_PAGE,
                total_pages=LOAD_ALL_PAGES,
                id=f"{product.id}"
            )
            photo_items: List[ProductPhotoItem] = cast(dict, result.data).get("items") or []

            for item in photo_items:
                product_photo, _ = self.get_or_instantiate(
                    self.product_photo,
                    {
                        "productnumber": product.productnumber,
                        "alttext": item["alttext"],
                        "file_type": item["deeplink"].split(".")[-1],
                    },
                    {
                        "id": item["id"],
                        "source": base64_image_from_url(item["deeplink"]),
                    },
                )

                product.add_child(product_photo)

    def load(self) -> None:
        """Load all models by calling other methods in the correct order."""
        self.load_packages()
        self.load_brands()
        self.load_categories()
        self.load_attributes()
        self.load_products()
        self.load_products_to_category()
        self.load_attribute_values_to_product()
        self.load_product_photos()
```

---

## Validation Checklist

After refactoring, verify:

### Architecture
- [ ] Directory structure created: `syncly/adapters/ccv/`
- [ ] Three files present: `__init__.py`, `models.py`, `constants.py`
- [ ] Module-level docstring added to `__init__.py`

### Constants (`constants.py`)
- [ ] `API_RATE_LIMIT_DELAY` constant defined
- [ ] `DEFAULT_PHOTOS_PER_PAGE` constant defined
- [ ] `LOAD_ALL_PAGES` constant defined
- [ ] No magic numbers remain in other files

### Models (`models.py`)
- [ ] TypedDict for each API response type
- [ ] Fields documented with comments where helpful
- [ ] All used API response structures covered

### Adapter Class (`__init__.py`)
- [ ] Complete type hints on all methods (return types)
- [ ] Complete type hints on all parameters
- [ ] Type hints on class attributes (maps)
- [ ] Improved error messages (fixed typo, added context)
- [ ] Constants used instead of magic numbers
- [ ] Type annotations on extracted items from API responses
- [ ] Docstrings updated for clarity

### Quality
- [ ] All files compile without errors
- [ ] No magic numbers in main logic
- [ ] Error messages include context
- [ ] All imports organized properly

---

## Key Differences from Third-Party Adapters

1. **No Helper Functions Needed**: This adapter doesn't transform data extensively; it mostly loads existing data as-is
2. **DiffSync Pattern**: Uses `get_or_instantiate` and child relationships specific to DiffSync
3. **Map Building**: Builds maps for cross-referencing entities (brand_map, package_map, etc.)
4. **Rate Limiting**: Includes `sleep()` calls to avoid hitting API limits
5. **Dependency Order**: `load()` method calls other methods in a specific order due to dependencies

---

## Success Criteria

The refactoring is complete when:

1. ✅ **All methods have complete type hints** - Return types and parameter types
2. ✅ **No magic numbers** - All extracted to constants
3. ✅ **TypedDicts for API responses** - Clear structure documentation
4. ✅ **Improved error messages** - Fixed typo, added context
5. ✅ **Module documentation** - Clear explanation of adapter purpose
6. ✅ **Files compile successfully** - No syntax errors
7. ✅ **Consistent with DiffSync patterns** - Preserves adapter functionality

---

## Testing the Refactor

After implementation, verify with:

```bash
# Check syntax
python3 -m py_compile syncly/adapters/ccv/__init__.py
python3 -m py_compile syncly/adapters/ccv/constants.py
python3 -m py_compile syncly/adapters/ccv/models.py

# List structure
ls -la syncly/adapters/ccv/

# Expected output:
# ccv/
# ├── __init__.py
# ├── constants.py
# └── models.py
```

---

## Additional Notes

### Rate Limiting Strategy

The adapter includes `sleep(API_RATE_LIMIT_DELAY)` in methods that iterate over products:
- `load_attribute_values_to_product()`
- `load_product_photos()`

This prevents hitting CCV Shop API rate limits when processing many products.

### Error Handling Improvements

**Original Error:**
```python
except KeyError:
    logger.error(
        "KeyError while processing product, lickily missing a certain fields"
    )
```

**Improved Error:**
```python
except KeyError as err:
    logger.error(
        f"KeyError while processing product {product_number}: {err}. "
        f"Likely missing required fields in API response."
    )
```

---

## Final Structure Overview

**Before (Single File):**
```
syncly/adapters/ccv.py
- 320 lines
- Missing type hints
- Magic numbers inline
- Typo in error message
```

**After (Module with 3 Files):**
```
syncly/adapters/ccv/
├── __init__.py       # ~340 lines with complete type hints
├── models.py         # ~90 lines with TypedDicts
└── constants.py      # ~8 lines with constants
```

**Total:** ~438 lines (was 320), but significantly more type-safe, maintainable, and well-documented.
