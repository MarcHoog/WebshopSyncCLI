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

import logging
from time import sleep
from typing import cast, Tuple, Dict, List, Optional

from diffsync import Adapter
from diffsync.enum import DiffSyncModelFlags

from ...helpers import base64_image_from_url, normalize_string
from ...settings import Settings
from ...clients.ccv.client import CCVClient
from ...models.ccv_shop import (
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
)

logger = logging.getLogger(__name__)


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
