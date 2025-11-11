# Third-Party Adapter Cleanup Strategy

## Overview
This guide provides a systematic approach to cleaning up and improving third-party adapter implementations for better readability, maintainability, and consistency.

## Core Principles

1. **Separation of Concerns**: Business logic should be extracted into helper functions
2. **Single Responsibility**: Each function should do one thing well
3. **Explicit is Better**: Use constants instead of magic strings/numbers
4. **Fail Safely**: Always handle edge cases and provide sensible defaults
5. **Type Safety**: Use type hints everywhere possible
6. **Documentation**: Every public function should have a docstring

---

## Cleanup Checklist

### 1. **Extract Constants**
Move all magic strings and numbers to module-level constants.

**Before:**
```python
attrs = {
    "package": "kartonnen doos",
    "category": [],
}
```

**After:**
```python
# At top of module
DEFAULT_PACKAGE = "kartonnen doos"
META_DESCRIPTION_MAX_LENGTH = 317

# In function
attrs = {
    "package": DEFAULT_PACKAGE,
    "category": [],
}
```

---

### 2. **Create Helper Functions**

Break down complex logic into small, testable helper functions.

#### Required Helpers:
- `_build_name(row, brand)` - Construct product names
- `_build_description(row)` - Format product descriptions
- `_build_meta_description(row)` - Create SEO meta descriptions
- `_get_price(row)` - Safely parse and validate prices
- `_should_include_product(row, settings)` - Filter logic

**Template:**
```python
def _get_price(pd: ProductRow) -> float:
    """
    Extract and validate price from product row.

    Args:
        pd: Product row data

    Returns:
        Price as float, or 0.0 if invalid/missing
    """
    raw = pd.get("price_field")
    if raw is None or raw == "":
        return 0.0
    try:
        return to_float(str(raw))
    except Exception:
        logger.warning("Failed to parse price %r; defaulting to 0.0", raw)
        return 0.0
```

---

### 3. **Improve Type Hints**

Add explicit type hints to all functions.

**Before:**
```python
def load_products(self):
    ...
```

**After:**
```python
def load_products(self) -> List[ThirdPartyProduct]:
    """Load and process all products from the data source."""
    ...
```

---

### 4. **Simplify Main Logic**

The `load_products` method should be high-level and readable.

**Before:**
```python
def load_products(self):
    brand = self.settings.ccv_shop.brand
    for p in self._get_products():
        try:
            product, _ = cast(Tuple[ThirdPartyProduct, bool], self.get_or_instantiate(
                model=self.product,
                ids={"productnumber": f"{p.get('article_number')}"},
                attrs={
                    "name": p.get('article_name_nl'),
                    "package": "kartonnen doos",
                    "description": wrap_style(p.get("article_description_nl", "")),
                    # ... more inline logic
                }
            ))
        except ValidationError as err:
            pretty_validation_error(err)
            raise err
        # ... more logic
```

**After:**
```python
def load_products(self) -> List[ThirdPartyProduct]:
    """Load and process all products from the data source."""
    brand = normalize_string(self.settings.ccv_shop.brand)

    for row in self._get_products():
        if not self._should_process_product(row):
            continue

        product = self._create_product(row, brand)
        self._add_variants(row, product)

    return cast(List[ThirdPartyProduct], self.get_all(self.product))
```

---

### 5. **Extract Product Creation**

Move product instantiation to a dedicated method.

```python
def _create_product(self, row: ProductRow, brand: str) -> ThirdPartyProduct:
    """
    Create or retrieve a product from a data row.

    Args:
        row: Raw product data
        brand: Normalized brand name

    Returns:
        ThirdPartyProduct instance

    Raises:
        ValidationError: If product data is invalid
    """
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
        logger.error(f"Validation failed for product {row.get('article_number')}")
        pretty_validation_error(err)
        raise
```

---

### 6. **Build Attributes Separately**

Extract attribute building to its own method.

```python
def _build_product_attrs(self, row: ProductRow, brand: str) -> dict:
    """
    Build product attributes dictionary from row data.

    Args:
        row: Raw product data
        brand: Normalized brand name

    Returns:
        Dictionary of product attributes
    """
    return {
        "name": _build_name(row, brand),
        "package": DEFAULT_PACKAGE,
        "description": wrap_style(_build_description(row)),
        "price": _get_price(row),
        "category": self._get_categories(row),
        "brand": brand,
        "page_title": _build_page_title(row, brand),
        "meta_description": _build_meta_description(row)
    }

def _build_product_ids(self, row: ProductRow) -> dict:
    """Extract product identification fields."""
    return {
        "productnumber": str(row.get('article_number', ''))
    }
```

---

### 7. **Extract Variant Addition**

Move color/size/image logic to a separate method.

```python
def _add_variants(self, row: ProductRow, product: ThirdPartyProduct) -> None:
    """
    Add color, size, and image variants to product.

    Args:
        row: Raw product data
        product: Product to add variants to
    """
    append_if_not_exists(row.get("colour_nl"), product.colors)
    append_if_not_exists(row.get("sizes"), product.sizing)

    # Add image with color association
    image_tuple = (row.get("colour_nl"), row.get("article_image"))
    if all(image_tuple):  # Only add if both values exist
        append_if_not_exists(image_tuple, product.images)
```

---

### 8. **Add Product Filtering**

Create a method to determine if a product should be processed.

```python
def _should_process_product(self, row: ProductRow) -> bool:
    """
    Check if product should be processed based on business rules.

    Args:
        row: Raw product data

    Returns:
        True if product should be processed
    """
    # Example filtering logic
    if not row.get('article_number'):
        logger.debug("Skipping product without article number")
        return False

    # Add more business rules as needed
    return True
```

---

### 9. **Improve Error Handling**

Add context to errors and handle edge cases.

```python
# Bad
except ValidationError as err:
    pretty_validation_error(err)
    raise err

# Good
except ValidationError as err:
    article_num = row.get('article_number', 'unknown')
    logger.error(f"Failed to create product {article_num}: {err}")
    pretty_validation_error(err)
    raise
```

---

### 10. **Add Module Documentation**

Document the module's purpose at the top.

```python
"""
HydroWear Third-Party Adapter

This adapter processes product data from HydroWear CSV files and converts
them into ThirdPartyProduct instances for synchronization with the CCV shop.

Data Flow:
1. Read CSV file from connection
2. Parse rows into ProductRow TypedDict
3. Filter and validate products
4. Transform to ThirdPartyProduct format
5. Add variants (colors, sizes, images)
"""
```

---

## File Structure

After cleanup, each adapter should have:

```
adapter_name/
├── __init__.py       # Main adapter class (high-level orchestration)
├── models.py         # TypedDict definitions and enums
├── helpers.py        # Pure functions for data transformation
└── constants.py      # (Optional) If many constants
```

---

## Testing Considerations

After cleanup, these functions should be easily testable:

```python
# Each helper can be unit tested
assert _get_price({"gross_price": "12.50"}) == 12.50
assert _get_price({"gross_price": None}) == 0.0
assert _get_price({"gross_price": "invalid"}) == 0.0

# Name building
assert _build_name({"article_name_nl": "Test"}, "Brand") == "Brand Test"
```

---

## Before/After Summary

### Before (Messy):
- Inline logic mixed with orchestration
- Magic strings scattered throughout
- No type hints or documentation
- Hard to test or modify
- Unclear error context

### After (Clean):
- Clear separation of concerns
- Named constants for all magic values
- Complete type hints and docstrings
- Easy to test individual functions
- Helpful error messages with context

---

## Implementation Order

1. ✅ Create constants at module level
2. ✅ Write helper functions in helpers.py
3. ✅ Add type hints to all functions
4. ✅ Extract _build_product_attrs method
5. ✅ Extract _build_product_ids method
6. ✅ Extract _create_product method
7. ✅ Extract _add_variants method
8. ✅ Simplify load_products to orchestration only
9. ✅ Add docstrings everywhere
10. ✅ Add module-level documentation

---

## Maintenance

Run these checks periodically:
- `mypy` for type checking
- `pylint` for code quality
- Manual review of `load_products` - should read like prose
- Check that no magic strings remain in main logic
