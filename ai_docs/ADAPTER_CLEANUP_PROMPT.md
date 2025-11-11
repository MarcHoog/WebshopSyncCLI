# Third-Party Adapter Architecture Guide - AI Instructions

## Objective
Refactor a third-party adapter to follow clean architecture principles: separation of concerns, testability, and maintainability. Transform messy inline code into well-organized, self-documenting modules.

---

## Architecture Principles

### 1. **Separation of Concerns**
- **Orchestration** (adapter class) coordinates high-level flow
- **Transformation** (helpers) performs data manipulation
- **Configuration** (constants) holds all magic values
- **Structure** (models) defines data shapes

### 2. **Single Responsibility**
Each function does ONE thing:
- Extracts a value → one function
- Transforms a value → one function
- Validates a value → one function
- Builds a composite → one function that calls others

### 3. **No Magic Values**
If it's hardcoded, it must be a named constant:
- Strings like `"kartonnen doos"` → `DEFAULT_PACKAGE`
- Numbers like `317` → `META_DESCRIPTION_MAX_LENGTH`
- Repeated field names → consider constants too

### 4. **Type Safety**
Every function signature must be complete:
```python
def function_name(param: Type) -> ReturnType:
```

### 5. **Simple Docstrings**
Single-line summaries only:
```python
"""Does X and returns Y."""
```

### 6. **Safe Defaults**
Every helper handles None/empty gracefully:
```python
if not value:
    return default_value
```

---

## Target File Structure

```
adapter_name/
├── __init__.py       # Adapter class - orchestration ONLY
├── models.py         # TypedDict definitions & enums
├── helpers.py        # Pure functions - data transformation
└── constants.py      # All magic strings and numbers
```

**Key Rule:** Look at a file and know its purpose in 3 seconds.

---

## Step-by-Step Instructions

### STEP 1: Create constants.py

Extract ALL magic strings and numbers to a new file `constants.py`.

```python
"""Constants for [AdapterName] adapter."""

# Product defaults
DEFAULT_PACKAGE = "kartonnen doos"

# SEO limits
META_DESCRIPTION_MAX_LENGTH = 317
```

**Action:** Scan the code for any hardcoded strings or numbers. Move them to constants.py with descriptive names.

---

### STEP 2: Create/Update helpers.py

Extract ALL data transformation logic from the adapter class into pure helper functions.

#### Pattern Recognition: What to Extract?

Scan the existing code for these patterns and extract each into a helper:

**Pattern 1: Data Parsing**
If you see: loops converting raw data to ProductRow
```python
# In _get_products()
for product in product_data:
    product_row: ProductRow = {}
    for i, field in enumerate(ProductRow.__annotations__):
        # ... mapping logic
```
Extract to: `parse_product_row(product: List[Any]) -> ProductRow`

**Pattern 2: String Building**
If you see: concatenating strings, joining parts
```python
name = f"{brand} {row.get('article_name')} {row.get('model')}"
```
Extract to: `_build_name(row: ProductRow, brand: str) -> str`

**Pattern 3: Value Extraction with Defaults**
If you see: getting values with fallbacks, type conversion, error handling
```python
price = row.get("price")
if price is None:
    price = 0.0
else:
    price = float(price)
```
Extract to: `_get_price(row: ProductRow) -> float`

**Pattern 4: Conditional Transformations**
If you see: if/else logic that transforms data
```python
if row.get("description"):
    desc = row.get("description").strip()
else:
    desc = ""
```
Extract to: `_build_description(row: ProductRow) -> str`

**Pattern 5: Truncation/Formatting**
If you see: string slicing, length checks, formatting
```python
meta = row.get("text", "")[:317] + "..."
```
Extract to: `_build_meta_description(row: ProductRow) -> str`

**Pattern 6: Business Logic Validation**
If you see: filtering conditions, stock checks, exclusion rules
```python
if row.get("stock") == "green" and row.get("reorder") == 1:
    # process
```
Extract to: `_is_stocked(row: ProductRow) -> bool`

**Pattern 7: List/Array Building**
If you see: building lists from row data
```python
categories = []
if row.get("main_cat"):
    categories.append(row.get("main_cat"))
if row.get("sub_cat"):
    categories.append(row.get("sub_cat"))
```
Extract to: `_get_categories(row: ProductRow) -> List[str]`

#### Helper Function Template

Every helper should follow this pattern:

```python
def _helper_name(row: ProductRow, *other_params) -> ReturnType:
    """Single-line description of what this does."""
    # 1. Extract raw value(s)
    raw_value = row.get("field_name")

    # 2. Handle None/empty case
    if not raw_value:
        return default_value

    # 3. Transform/validate
    try:
        transformed = some_transformation(raw_value)
        return transformed
    except Exception:
        logger.warning(f"Failed to transform {raw_value}")
        return default_value
```

#### Key Requirements

✅ **Do Extract:**
- Any data transformation
- Any string building/formatting
- Any value extraction with fallbacks
- Any business validation logic
- Any type conversions

❌ **Don't Extract:**
- Simple assignments: `x = row.get("field")`
- Direct method calls with no logic: `normalize_string(brand)`
- Single-use operations with no complexity

**Quality Checklist:**
- [ ] Import constants from constants.py
- [ ] All functions have single-line docstrings
- [ ] All functions have complete type hints
- [ ] All functions handle None/empty inputs
- [ ] All functions are pure (no side effects)
- [ ] No business logic remains in __init__.py

---

### STEP 3: Add Module-Level Docstring to __init__.py

Add this at the very top of __init__.py:

```python
"""
[AdapterName] Third-Party Adapter

This adapter processes product data from [Source] and converts
them into ThirdPartyProduct instances for synchronization with the CCV shop.

Data Flow:
1. Read data file from connection
2. Parse rows into ProductRow TypedDict
3. Filter and validate products
4. Transform to ThirdPartyProduct format
5. Add variants (colors, sizes, images)
"""
```

---

### STEP 4: Organize Imports in __init__.py

Structure imports clearly:

```python
import logging
from pydantic import ValidationError
from typing import List, Any, Generator, Tuple, cast

from syncly.helpers import (
    csv_bytes_to_list,
    wrap_style,
    normalize_string,
    append_if_not_exists,
    pretty_validation_error
)
from ..third_party import ThirdPartyAdapter
from .models import ProductRow
from .helpers import (
    parse_product_row,
    _build_name,
    _build_description,
    _build_meta_description,
    _build_page_title,
    _get_price,
    _get_categories
)
from .constants import DEFAULT_PACKAGE
from ...models.third_party import ThirdPartyProduct

logger = logging.getLogger(__name__)
```

---

### STEP 5: Update Adapter Class Docstring

```python
class AdapterNameAdapter(ThirdPartyAdapter):
    """
    Adapter for processing [Source] product data.

    This adapter reads [file type] files containing product information
    and transforms them into standardized ThirdPartyProduct objects.
    """
```

---

### STEP 6: Simplify _get_products() Method

Refactor to use parse_product_row helper:

**Before:**
```python
def _get_products(self) -> Generator[ProductRow, Any, Any]:
    assert self.conn

    with self.conn as file:
        product_data = csv_bytes_to_list(file.read(), include_header=False)
        for product in product_data:
            product_row: ProductRow = {}
            for i, field in enumerate(ProductRow.__annotations__):
                if i < len(product):
                    product_row[field] = product[i]
                else:
                    product_row[field] = None
            yield product_row
```

**After:**
```python
def _get_products(self) -> Generator[ProductRow, Any, Any]:
    """Parse CSV file and yield ProductRow dictionaries."""
    assert self.conn, "Connection must be established before reading products"

    with self.conn as file:
        product_data = csv_bytes_to_list(file.read(), include_header=False)
        for product in product_data:
            yield parse_product_row(product)
```

---

### STEP 7: Extract Private Methods in Adapter Class

Break down the load_products() method into smaller, focused methods. Each method should represent ONE logical step.

#### Extraction Pattern: Identify Logical Steps

Look at load_products() and identify distinct operations:

**Step 1: Filtering** - Should this product be processed?
→ Extract to filtering method

**Step 2: ID Building** - What identifies this product uniquely?
→ Extract to ID builder method

**Step 3: Attribute Building** - What are all the product attributes?
→ Extract to attribute builder method

**Step 4: Product Creation** - Create/get product instance
→ Extract to creation method with error handling

**Step 5: Variant Addition** - Add colors, sizes, images
→ Extract to variant method

#### Method Templates

**A. Filtering Method**
If you see: conditions that skip products
```python
# In load_products()
if not p.get('article_number'):
    continue
if p.get('excluded'):
    continue
```
Extract to:
```python
def _should_process_product(self, row: ProductRow) -> bool:
    """Check if product should be processed based on business rules."""
    if not row.get('article_number'):
        logger.debug("Skipping product without article number")
        return False

    # Add other business rules
    return True
```

**B. ID Builder Method**
If you see: dictionary with identifier fields
```python
ids = {"productnumber": f"{p.get('article_number')}"}
```
Extract to:
```python
def _build_product_ids(self, row: ProductRow) -> dict:
    """Extract product identification fields."""
    return {
        "productnumber": str(row.get('article_number', ''))
    }
```

**C. Attribute Builder Method**
If you see: large attrs dictionary in get_or_instantiate()
```python
attrs = {
    "name": ...,
    "price": ...,
    # 10 more fields with inline transformations
}
```
Extract to:
```python
def _build_product_attrs(self, row: ProductRow, brand: str) -> dict:
    """Build product attributes dictionary from row data."""
    return {
        "name": _build_name(row, brand),
        "package": DEFAULT_PACKAGE,
        "description": wrap_style(_build_description(row)),
        "price": _get_price(row),
        "category": _get_categories(row),
        "brand": brand,
        # Use helper functions for ALL transformations
    }
```

**D. Creation Method**
If you see: try-except around get_or_instantiate()
```python
try:
    product, _ = cast(..., self.get_or_instantiate(...))
except ValidationError as err:
    # error handling
```
Extract to:
```python
def _create_product(self, row: ProductRow, brand: str) -> ThirdPartyProduct:
    """Create or retrieve a product from a data row."""
    try:
        product, _ = cast(
            Tuple[ThirdPartyProduct, bool],
            self.get_or_instantiate(
                model=self.product,
                ids=self._build_product_ids(row),
                attrs=self._build_product_attrs(row, brand)
            )
        )
        return product
    except ValidationError as err:
        # Add context to error
        article_num = row.get('article_number', 'unknown')
        logger.error(f"Failed to create product {article_num}: {err}")
        pretty_validation_error(err)
        raise
```

**E. Variant Method**
If you see: multiple append_if_not_exists() calls
```python
append_if_not_exists(p.get("color"), product.colors)
append_if_not_exists(p.get("size"), product.sizing)
append_if_not_exists((p.get("color"), p.get("image")), product.images)
```
Extract to:
```python
def _add_variants(self, row: ProductRow, product: ThirdPartyProduct) -> None:
    """Add color, size, and image variants to product."""
    # Extract each variant field
    colour = row.get("colour_field")
    size = row.get("size_field")
    image_url = row.get("image_field")

    # Add if exists (safe against None)
    if colour:
        append_if_not_exists(colour, product.colors)

    if size:
        append_if_not_exists(size, product.sizing)

    # Tuples need both values present
    if colour and image_url:
        append_if_not_exists((colour, image_url), product.images)
```

#### Extraction Rules

✅ **Extract if:**
- Logic is more than 3 lines
- Contains error handling
- Builds complex data structures
- Has conditional logic
- Would benefit from separate testing

❌ **Don't extract if:**
- Single line operation
- Just passing through a value
- No complexity to hide

---

### STEP 8: Simplify load_products() to Pure Orchestration

The final load_products() should be clean and high-level:

```python
def load_products(self) -> List[ThirdPartyProduct]:
    """
    Load and process all products from the data source.

    Orchestrates: reading, filtering, creating/updating products, and adding variants.
    """
    brand = normalize_string(self.settings.ccv_shop.brand)

    for row in self._get_products():
        if not self._should_process_product(row):
            continue

        product = self._create_product(row, brand)
        self._add_variants(row, product)

    return cast(List[ThirdPartyProduct], self.get_all(self.product))
```

**Critical:** load_products should have ZERO inline logic. It should only call other methods.

---

## Docstring Rules

**ALWAYS use simple single-line docstrings:**

✅ Good:
```python
def _build_name(row: ProductRow, brand: str) -> str:
    """Construct product name from row data and brand."""
```

❌ Bad (DO NOT DO THIS):
```python
def _build_name(row: ProductRow, brand: str) -> str:
    """
    Construct product name from row data and brand.

    Args:
        row: Product row data
        brand: Brand name

    Returns:
        Formatted product name
    """
```

---

## Architecture Decision: Helper vs Method

**Helpers (in helpers.py):**
- Pure functions (no self parameter)
- Transform data in → data out
- No state, no side effects
- Reusable across adapters
- Examples: _build_name, _get_price, parse_product_row

**Methods (in adapter class):**
- Need access to self.settings or self.product
- Orchestrate multiple operations
- Have side effects (logging, database calls)
- Adapter-specific coordination
- Examples: _create_product, load_products, _get_products

**Rule of Thumb:**
If it touches `self`, it's a method. If it's pure transformation, it's a helper.

---

## Validation Checklist

After completing cleanup, verify these patterns:

### Constants
- [ ] All magic strings moved to constants.py
- [ ] All magic numbers moved to constants.py
- [ ] Constants have descriptive UPPER_CASE names
- [ ] Constants grouped by category with comments

### Helpers (helpers.py)
- [ ] Contains ONLY pure functions (no self parameter)
- [ ] All functions have single-line docstrings
- [ ] All functions have complete type hints
- [ ] All functions handle None/empty inputs safely
- [ ] parse_product_row() exists if data is list-based
- [ ] Build functions exist for complex string construction
- [ ] Get functions exist for value extraction with defaults
- [ ] No hardcoded values (all use constants)

### Adapter Class (__init__.py)
- [ ] Module-level docstring explains Data Flow
- [ ] Class has simplified docstring
- [ ] _get_products() uses parse_product_row if applicable
- [ ] Filtering method exists if products are skipped
- [ ] _build_product_ids() extracts ID logic
- [ ] _build_product_attrs() extracts attribute logic
- [ ] _create_product() exists with contextual error handling
- [ ] Variant method exists if colors/sizes/images are added
- [ ] load_products() is ≤15 lines (pure orchestration)
- [ ] NO inline transformations in load_products()
- [ ] NO dictionaries built inline in load_products()

### Quality
- [ ] All files compile: `python3 -m py_compile file.py`
- [ ] No duplicate logic across helpers
- [ ] Error messages include product identifiers
- [ ] Imports organized: stdlib → third-party → local

---

## File Verification Commands

Run these to verify success:
```bash
# Check syntax
python3 -m py_compile syncly/adapters/adapter_name/__init__.py
python3 -m py_compile syncly/adapters/adapter_name/helpers.py
python3 -m py_compile syncly/adapters/adapter_name/constants.py
python3 -m py_compile syncly/adapters/adapter_name/models.py

# List files
ls -la syncly/adapters/adapter_name/
```

Expected output:
```
adapter_name/
├── __init__.py       (main adapter class)
├── constants.py      (magic values)
├── helpers.py        (pure functions)
└── models.py         (TypedDict)
```

---

## Success Criteria

The cleanup is complete when:

1. **Reading load_products() tells the complete story** - No mental gymnastics needed
2. **Every function does exactly one thing** - No mixed responsibilities
3. **Zero magic values in main logic** - All strings/numbers are named constants
4. **Error messages have context** - Include article numbers or other identifiers
5. **Helpers are independently testable** - Can test without adapter instance
6. **File structure matches template** - 4 files: __init__, models, helpers, constants

---

## Common Pitfalls to Avoid

❌ **Don't do this:**
- Leaving inline logic in load_products()
- Using verbose docstrings with Args/Returns
- Mixing helper functions and class methods in same file
- Forgetting to handle None/empty values in helpers
- Not normalizing brand before using it
- Skipping type hints
- Leaving magic strings in the code

✅ **Do this:**
- Extract every piece of logic into named functions
- Use single-line docstrings
- Keep helpers.py pure (no class methods)
- Always check for None/empty and provide defaults
- Normalize brand once at top of load_products()
- Add complete type hints everywhere
- Name all constants descriptively

---

## Transformation Example: Before vs After

### Before (Messy):
Problems:
- Magic string "kartonnen doos" inline
- 10+ field transformations inline in attrs dict
- No filtering logic extracted
- Error handling without context
- No separation of concerns
- Hard to test individual pieces

```python
def load_products(self):
    brand = self.settings.ccv_shop.brand
    for p in self._get_products():
        try:
            product, _ = cast(Tuple[ThirdPartyProduct, bool], self.get_or_instantiate(
                model=self.product,
                ids={"productnumber": f"{p.get('id_field')}"},
                attrs={
                    "name": f"{brand} {p.get('name')}",  # Inline transformation
                    "package": "kartonnen doos",  # Magic string
                    "description": wrap_style(p.get("desc", "")),
                    "price": float(p.get("price", 0.0)),  # Unsafe conversion
                    "category": [p.get("cat")] if p.get("cat") else [],
                    "brand": brand.lower().strip(),
                    "page_title": f"{brand} {p.get('name')}",  # Duplicate logic
                    "meta_description": p.get("desc", "")[:317] + "..."  # Magic number
                }
            ))
        except ValidationError as err:
            pretty_validation_error(err)  # No context
            raise err

        append_if_not_exists(p.get("color"), product.colors)
        append_if_not_exists(p.get("size"), product.sizing)
```

### After (Clean):
Benefits:
- Constants extracted (DEFAULT_PACKAGE, META_DESCRIPTION_MAX_LENGTH)
- All transformations in named helpers
- Clear filtering step
- Contextual error handling
- Each piece independently testable
- load_products() tells the complete story in 10 lines

```python
def load_products(self) -> List[ThirdPartyProduct]:
    """
    Load and process all products from the data source.

    Orchestrates: reading, filtering, creating/updating products, and adding variants.
    """
    brand = normalize_string(self.settings.ccv_shop.brand)

    for row in self._get_products():
        if not self._should_process_product(row):
            continue

        product = self._create_product(row, brand)
        self._add_variants(row, product)

    return cast(List[ThirdPartyProduct], self.get_all(self.product))
```

Supporting methods (adapter class):
```python
def _build_product_attrs(self, row: ProductRow, brand: str) -> dict:
    """Build product attributes dictionary from row data."""
    return {
        "name": _build_name(row, brand),          # Helper function
        "package": DEFAULT_PACKAGE,                # Named constant
        "description": wrap_style(_build_description(row)),
        "price": _get_price(row),                  # Safe conversion
        "category": _get_categories(row),          # Extracted logic
        "brand": brand,                            # Already normalized
        "page_title": _build_page_title(row, brand),
        "meta_description": _build_meta_description(row)
    }
```

Supporting helpers (helpers.py):
```python
def _get_price(row: ProductRow) -> float:
    """Extract and validate price from product row, defaults to 0.0 if invalid."""
    raw = row.get("price_field")
    if raw is None or raw == "":
        return 0.0
    try:
        return to_float(str(raw))
    except Exception:
        logger.warning(f"Failed to parse price {raw}")
        return 0.0
```

---

## Common Pitfalls and Solutions

### Pitfall 1: Mixing Orchestration and Transformation
❌ **Bad:**
```python
def load_products(self):
    for row in self._get_products():
        # Building name inline
        name = f"{brand} {row.get('article_name')} {row.get('model')}"
        product = self.get_or_instantiate(...)
```

✅ **Good:**
```python
def load_products(self):
    for row in self._get_products():
        product = self._create_product(row, brand)
        # _create_product calls _build_name() helper
```

### Pitfall 2: Not Handling None Values
❌ **Bad:**
```python
def _get_price(row: ProductRow) -> float:
    return float(row.get("price"))  # Crashes if None
```

✅ **Good:**
```python
def _get_price(row: ProductRow) -> float:
    raw = row.get("price")
    if raw is None or raw == "":
        return 0.0
    try:
        return to_float(str(raw))
    except Exception:
        logger.warning(f"Failed to parse price {raw}")
        return 0.0
```

### Pitfall 3: Magic Values in Multiple Places
❌ **Bad:**
```python
# In helpers.py
desc = text[:317] + "..."

# In __init__.py
meta = description[:317] + "..."
```

✅ **Good:**
```python
# In constants.py
META_DESCRIPTION_MAX_LENGTH = 317

# In helpers.py
desc = text[:META_DESCRIPTION_MAX_LENGTH] + "..."
```

### Pitfall 4: Complex Logic Without Extraction
❌ **Bad:**
```python
def load_products(self):
    for row in self._get_products():
        if row.get("stock") == "green" and int(row.get("reorder", 0)) == 1:
            # 30 more lines of inline logic
```

✅ **Good:**
```python
def load_products(self):
    for row in self._get_products():
        if not self._should_process_product(row):
            continue
        product = self._create_product(row, brand)
        self._add_variants(row, product)
```

### Pitfall 5: Methods That Should Be Helpers
❌ **Bad:**
```python
# In adapter class
def _build_name(self, row: ProductRow, brand: str) -> str:
    return f"{brand} {row.get('name')}"
    # Doesn't use self, should be a helper!
```

✅ **Good:**
```python
# In helpers.py
def _build_name(row: ProductRow, brand: str) -> str:
    """Construct product name from row data and brand."""
    return f"{brand} {row.get('name')}"
```

---

## Adapter-Specific Considerations

Every adapter is different. Adjust based on:

1. **Data Source Type**
   - CSV files → parse_product_row() pattern
   - XLSX files → same pattern, different parser
   - API responses → direct dict access, different parsing

2. **Business Rules**
   - Stock checking → _is_stocked() helper
   - Exclusion rules → _is_excluded() helper
   - Price calculations → _calculate_price() helper

3. **Field Complexity**
   - Multiple name parts → _build_name() helper
   - Nested categories → _get_categories() helper
   - Complex descriptions → _build_description() helper

**Key Point:** Check the existing ProductRow model in models.py to understand available fields, then create helpers that transform those fields into the required output format.

---

## Final Notes

This is a **refactoring task**, not a rewrite:
- Keep the same functionality
- Don't change business logic
- Don't modify models.py structure unless necessary
- Only reorganize and extract existing code

**Success Criteria:**
- Can understand load_products() in 10 seconds
- Each function is testable in isolation
- No magic values anywhere
- Error messages give useful context

**The Goal:** Make the code so clear that comments are unnecessary. The structure itself should tell the story.
