# Perfion Adapter Refactoring Prompt

## Objective
Refactor the Perfion adapter (`syncly/adapters/perfion.py`) to follow clean architecture principles demonstrated in the HydroWear and Mascot adapters. Transform the current monolithic implementation into a well-organized, maintainable, and testable adapter.

---

## Current State Analysis

### Problems in Current Implementation

**File: `syncly/adapters/perfion.py`**

1. **Magic Values Inline**
   - `"kartonnen doos"` hardcoded (line 72)
   - `317` magic number for meta description truncation (line 57)

2. **No Separation of Concerns**
   - All logic mixed in `load_products()` method
   - Inline function `parse_meta_description()` inside `load_products()` (lines 53-59)
   - No helper functions for data transformation
   - Direct attribute building inside `get_or_instantiate()` call

3. **Missing Architecture Components**
   - No `constants.py` file
   - No `helpers.py` file
   - No `models.py` file with ProductRow TypedDict
   - No module-level docstring

4. **Incomplete Type Hints**
   - Missing return types on methods (lines 14, 17, 45)
   - No type hints on parameters

5. **Poor Error Handling**
   - Generic error catching without context (line 26)
   - No validation error handling for product creation

6. **Inline Business Logic**
   - Category filtering mixed with orchestration (lines 32-37)
   - No extraction of filtering logic into methods
   - No extraction of product creation logic

---

## Target Architecture

Following the patterns from HydroWear and Mascot adapters, create this structure:

```
syncly/adapters/perfion/
├── __init__.py       # Adapter class - orchestration ONLY
├── models.py         # ProductRow TypedDict definition
├── helpers.py        # Pure functions for data transformation
└── constants.py      # Magic strings and numbers
```

---

## Required Implementation Steps

### STEP 1: Create `constants.py`

Extract all magic values:

```python
"""Constants for Perfion adapter."""

# Product defaults
DEFAULT_PACKAGE = "kartonnen doos"

# SEO limits
META_DESCRIPTION_MAX_LENGTH = 317
```

---

### STEP 2: Create `models.py`

Define the ProductRow TypedDict based on fields used in the current implementation:

```python
"""Type definitions for Perfion adapter."""

from typing import TypedDict, Optional, List


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
```

**Note:** Analyze the actual Perfion API response to ensure all fields are captured. Add any additional fields that may be present in the API response.

---

### STEP 3: Create `helpers.py`

Extract all data transformation logic into pure helper functions:

```python
"""Helper functions for Perfion adapter data transformation."""

import logging
from typing import Optional

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
```

---

### STEP 4: Refactor `__init__.py`

Transform the main adapter file to follow the clean architecture pattern.

#### 4.1 Add Module-Level Docstring

```python
"""
Perfion Third-Party Adapter

This adapter processes product data from the Perfion API and converts
them into ThirdPartyProduct instances for synchronization with the CCV shop.

Data Flow:
1. Connect to Perfion API via connection client
2. Fetch product data from API
3. Filter products by included categories and excluded products
4. Transform to ThirdPartyProduct format
5. Add variants (colors, sizes, images)
"""
```

#### 4.2 Organize Imports

```python
import logging
from typing import List, Any, Generator, Tuple, cast
from pydantic import ValidationError
from requests.exceptions import RequestException

from syncly.helpers import (
    normalize_string,
    append_if_not_exists,
    wrap_style,
    pretty_validation_error,
)
from ..third_party import ThirdPartyAdapter
from .models import ProductRow
from .helpers import (
    build_name,
    build_description,
    build_meta_description,
    build_page_title,
    get_price,
    get_categories,
)
from .constants import DEFAULT_PACKAGE
from ...models.third_party import ThirdPartyProduct

logger = logging.getLogger(__name__)
```

#### 4.3 Update Class with Complete Type Hints

```python
class PerfionAdapter(ThirdPartyAdapter):
    """
    Adapter for processing Perfion API product data.

    This adapter connects to the Perfion API to fetch product information
    and transforms them into standardized ThirdPartyProduct objects.
    """

    def __str__(self) -> str:
        return "PerfionAdapter"
```

#### 4.4 Extract Filtering Logic to Methods

Create methods for filtering logic currently inline in `_get_products()`:

```python
    def _should_include_category(self, category: str) -> bool:
        """Check if product category is in included categories list."""
        included_categories = self.settings.perfion.included_categories

        # If no filter specified, include all
        if not included_categories:
            return True

        return category in included_categories

    def _is_product_excluded(self, item_number: str) -> bool:
        """Check if product is in excluded products list."""
        excluded_products = self.settings.perfion.excluded_products
        return item_number in excluded_products

    def should_process_product(self, row: ProductRow) -> bool:
        """Check if product should be processed based on business rules."""
        category = row.get("Category")
        item_number = row.get("ItemNumber")

        if not item_number:
            logger.debug("Skipping product without item number")
            return False

        if not category:
            logger.debug(f"Skipping product {item_number} without category")
            return False

        if not self._should_include_category(category):
            logger.info(
                f"Skipping product {item_number} - category '{category}' not in "
                f"included categories: {self.settings.perfion.included_categories}"
            )
            return False

        if self._is_product_excluded(item_number):
            logger.info(f"Skipping excluded product: {item_number}")
            return False

        return True
```

#### 4.5 Simplify `_get_products()` Method

```python
    def _get_products(self) -> Generator[ProductRow, Any, Any]:
        """Fetch products from Perfion API and yield ProductRow dictionaries."""
        assert self.conn, "Connection must be established before reading products"

        try:
            result = self.conn.get_products()
        except RequestException as err:
            logger.error(f"Failed to contact Perfion API: {err}")
            raise ConnectionError("Unable to connect to Perfion API") from err

        for product_data in result.data:
            # Cast to ProductRow for type safety
            yield product_data  # type: ignore
```

**Note:** Filtering is now handled in `should_process_product()`, not here.

#### 4.6 Extract Product Building Methods

```python
    def build_product_ids(self, row: ProductRow) -> dict[str, str]:
        """Extract product identification fields."""
        return {
            "productnumber": str(row.get("ItemNumber", ""))
        }

    def build_product_attrs(self, row: ProductRow, brand: str) -> dict[str, Any]:
        """Build product attributes dictionary from row data."""
        return {
            "name": build_name(row, brand),
            "package": DEFAULT_PACKAGE,
            "price": get_price(row),
            "description": wrap_style(build_description(row)),
            "category": get_categories(row),
            "brand": normalize_string(brand),
            "page_title": build_page_title(row, brand),
            "meta_description": build_meta_description(row),
        }

    def create_product(self, row: ProductRow, brand: str) -> ThirdPartyProduct:
        """Create or retrieve a product from a data row."""
        try:
            product, _ = cast(
                Tuple[ThirdPartyProduct, bool],
                self.get_or_instantiate(
                    model=self.product,
                    ids=self.build_product_ids(row),
                    attrs=self.build_product_attrs(row, brand),
                ),
            )
            return product

        except ValidationError as err:
            item_number = row.get("ItemNumber", "unknown")
            logger.error(f"Failed to create product {item_number}: {err}")
            pretty_validation_error(err)
            raise
```

#### 4.7 Extract Variant Addition Logic

```python
    def add_variants(self, row: ProductRow, product: ThirdPartyProduct) -> None:
        """Add color, size, and image variants to product."""
        color = row.get("ERPColor")
        if color:
            append_if_not_exists(color, product.colors)

        size = row.get("TSizeNewDW")
        if size:
            append_if_not_exists(size, product.sizing)

        image_url = row.get("BaseProductImageUrl")
        if color and image_url:
            append_if_not_exists((color, image_url), product.images)
```

#### 4.8 Simplify `load_products()` to Pure Orchestration

```python
    def load_products(self) -> List[ThirdPartyProduct]:
        """
        Load and process all products from the Perfion API.

        Orchestrates: fetching, filtering, creating/updating products, and adding variants.
        """
        brand = normalize_string(self.settings.ccv_shop.brand)

        for row in self._get_products():
            if not self.should_process_product(row):
                continue

            product = self.create_product(row, brand)
            self.add_variants(row, product)

        return cast(List[ThirdPartyProduct], self.get_all(self.product))
```

---

## Validation Checklist

After refactoring, verify:

### Architecture
- [ ] Directory structure created: `syncly/adapters/perfion/`
- [ ] Four files present: `__init__.py`, `models.py`, `helpers.py`, `constants.py`
- [ ] Module-level docstring added to `__init__.py`

### Constants (`constants.py`)
- [ ] `DEFAULT_PACKAGE` constant defined
- [ ] `META_DESCRIPTION_MAX_LENGTH` constant defined
- [ ] No magic values remain in other files

### Models (`models.py`)
- [ ] `ProductRow` TypedDict defined with all Perfion API fields
- [ ] Fields marked Optional appropriately
- [ ] `total=False` set for flexibility

### Helpers (`helpers.py`)
- [ ] All helper functions are pure (no `self` parameter)
- [ ] `build_name()` implemented
- [ ] `build_page_title()` implemented
- [ ] `build_description()` implemented
- [ ] `build_meta_description()` implemented with HTML stripping
- [ ] `get_price()` implemented with error handling
- [ ] `get_categories()` implemented
- [ ] All functions have single-line docstrings
- [ ] All functions have complete type hints
- [ ] All functions handle None/empty values safely

### Adapter Class (`__init__.py`)
- [ ] Complete type hints on all methods
- [ ] `should_process_product()` method extracts filtering logic
- [ ] `_should_include_category()` helper method for category filtering
- [ ] `_is_product_excluded()` helper method for exclusion checking
- [ ] `build_product_ids()` method extracts ID logic
- [ ] `build_product_attrs()` method extracts attribute logic
- [ ] `create_product()` method with proper error handling
- [ ] `add_variants()` method extracts variant logic
- [ ] `_get_products()` simplified (no filtering, just fetching)
- [ ] `load_products()` is ≤15 lines (pure orchestration)
- [ ] Error messages include item numbers for context
- [ ] RequestException handling improved with context

### Quality
- [ ] No inline logic in `load_products()`
- [ ] No magic strings or numbers in main logic
- [ ] All imports organized: stdlib → third-party → local
- [ ] Consistent with HydroWear and Mascot patterns

---

## Implementation Notes

### Key Differences from CSV-based Adapters

1. **Data Source**: Perfion uses API (`self.conn.get_products()`) instead of file reading
2. **No `parse_product_row()`**: API returns dict directly, no list-to-dict conversion needed
3. **Error Handling**: Must handle `RequestException` for API calls
4. **Filtering**: Category inclusion/exclusion is a Perfion-specific feature

### Reference Implementations

Use these as templates:
- **HydroWear adapter** (`syncly/adapters/hydrowear/`): CSV-based, shows price mapping pattern
- **Mascot adapter** (`syncly/adapters/mascot/`): XLSX-based, shows availability merging pattern

Both demonstrate:
- Clean separation of concerns
- Proper helper function extraction
- Good error handling with context
- Type-safe implementations

---

## Success Criteria

The refactoring is complete when:

1. ✅ **Reading `load_products()` tells the complete story** - 10-15 lines maximum
2. ✅ **Every function does exactly one thing** - Clear single responsibility
3. ✅ **Zero magic values in main logic** - All extracted to constants
4. ✅ **Error messages have context** - Include item numbers
5. ✅ **Helpers are independently testable** - Pure functions, no adapter dependency
6. ✅ **File structure matches target** - 4 files in proper locations
7. ✅ **Type hints are complete** - All functions fully typed
8. ✅ **Filtering logic is extracted** - Not mixed with data fetching

---

## Testing the Refactor

After implementation, verify with:

```bash
# Check syntax
python3 -m py_compile syncly/adapters/perfion/__init__.py
python3 -m py_compile syncly/adapters/perfion/helpers.py
python3 -m py_compile syncly/adapters/perfion/constants.py
python3 -m py_compile syncly/adapters/perfion/models.py

# List structure
ls -la syncly/adapters/perfion/

# Expected output:
# perfion/
# ├── __init__.py
# ├── constants.py
# ├── helpers.py
# └── models.py
```

---

## Additional Considerations

### Potential API Field Discovery

Since the current implementation directly accesses API response fields, you may need to:

1. **Inspect the actual API response** to ensure `ProductRow` TypedDict captures all fields
2. **Add any missing fields** that appear in the Perfion API but aren't currently used
3. **Document field meanings** if they're not obvious (e.g., what is "TSizeNewDW"?)

### Settings Validation

Current code assumes:
- `self.settings.perfion.included_categories` exists (optional list)
- `self.settings.perfion.excluded_products` exists (list)

Ensure these are properly defined in your settings schema.

### HTML Stripping in Meta Description

The current implementation strips `<p>` tags naively with `.strip("<p>")`. Consider:
- Using a proper HTML parser if descriptions contain complex HTML
- Or document that only simple `<p>` tags are expected

---

## Final Structure Overview

**Before (Single File):**
```
syncly/adapters/perfion.py
- Everything mixed together
- 88 lines with inline logic
```

**After (Module with 4 Files):**
```
syncly/adapters/perfion/
├── __init__.py       # ~100 lines, clean orchestration
├── models.py         # ~15 lines, TypedDict
├── helpers.py        # ~80 lines, pure functions
└── constants.py      # ~5 lines, magic values
```

**Total:** ~200 lines (was 88), but significantly more maintainable, testable, and aligned with project architecture.
