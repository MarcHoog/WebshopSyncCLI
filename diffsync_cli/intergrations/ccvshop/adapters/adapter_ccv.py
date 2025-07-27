import logging
from typing import cast, Optional, Tuple, Dict
from diffsync import Adapter
from diffsync_cli.config import ConfigSettings
from diffsync_cli.clients.ccv.client import CCVClient
from diffsync_cli.intergrations.ccvshop.models.ccv_shop import  (CCVProduct, CCVCategory, CCVPackage, CCVCategoryToDevice, CCVAttribute, CCVAttributeValue, CCVAttributeValueToProduct)
from diffsync_cli.utils import normalize_string
from diffsync.enum import DiffSyncModelFlags

logger = logging.getLogger(__name__)

class CCVShopAdapter(Adapter):
    """DiffSync Adapter using requests to communicate to CCVShop"""

    product = CCVProduct
    category = CCVCategory
    package = CCVPackage
    category_to_device = CCVCategoryToDevice
    attribute = CCVAttribute
    attribute_value = CCVAttributeValue
    attribute_value_to_product = CCVAttributeValueToProduct

    top_level = ["product"]

    category_map = {}
    product_map: Dict[int, CCVProduct] = {}
    package_map = {}
    attribute_map: Dict[int, CCVAttribute] = {}

    # The Primary Category is the category that is used as the root category for all products.
    root_category = None

    def __init__(self, *args, cfg: Optional[ConfigSettings]= None, client: Optional[CCVClient] = None, **kwargs,):
        super().__init__(*args, **kwargs)

        if not cfg:
            cfg = ConfigSettings()
            cfg.load_env_vars(["CCVSHOP"])

        if not client:
            raise ValueError("Improperly configured settings for communicating to CcvShop. Please validate accuracy.")

        self.cfg = cfg
        self.conn = client

    def load_packages(self):
        """Setup the package for CCVShop"""
        packages = self.conn.packages.get_packages(total_pages=-1)
        package_items = cast(dict, packages.data).get("items") or []

        for p in package_items:
            name = p.get("name", "").strip().lower()
            package, _ = cast(Tuple[CCVPackage, bool], self.get_or_instantiate(
                self.package,
                {"name":  name},
                {"id": p.get("id")  },
            ))

            self.package_map[package.id] = package
            package.model_flags = DiffSyncModelFlags.IGNORE

    def load_categories(self):

        if not self.cfg.verify("CCVSHOP_ROOT_CATEGORY"):
            raise ValueError("CCVSHOP_ROOT_CATEGORY is not set")

        categories = self.conn.categories.get_categories(total_pages=-1)
        category_items = cast(dict, categories.data).get("items") or []

        for c in category_items:
            if c.get("name", "").strip().lower():
                category, _ = cast(Tuple[CCVCategory, bool], self.get_or_instantiate(
                    self.category,
                    {"name": c.get("name")},
                    {"id": c.get("id")  },
                ))

                if category.name == self.cfg.get("CCVSHOP_ROOT_CATEGORY"):
                    self.root_category = category

                self.category_map[category.id] = category
                category.model_flags = DiffSyncModelFlags.IGNORE

    def load_attributes(self):

        attributes = self.conn.attributes.get_attributes(total_pages=-1)
        attribute_items = cast(dict, attributes.data).get("items") or []
        for attr in attribute_items:
            attribute, _ = cast(Tuple[CCVAttribute, bool], self.get_or_instantiate(
                self.attribute,
                {"name": normalize_string(attr.get("name"))},
                {"id": attr.get("id")},
            ))
            self.attribute_map[attribute.id] = attribute
            attribute.model_flags = DiffSyncModelFlags.IGNORE

            attribute_values = self.conn.attributes.get_attribute_values(f"{attribute.id}")
            value_items = cast(dict, attribute_values.data).get("items") or []
            for val in value_items:
               value, created = cast(Tuple[CCVAttributeValue, bool], self.get_or_instantiate(
                   self.attribute_value,
                   {
                       "attribute": attribute.name,
                       "value": normalize_string(val["name"]),
                   },
                   {
                       "id": val["id"],
                   }
               ))

               if created:
                   attribute.add_child(value)


    def load_products(self):
        """Load all articles by calling other methods"""

        if not self.root_category:
            raise ValueError(f"Root category of name {self.cfg.get('CCVSHOP_ROOT_CATEGORY')} is not defined")

        logger.info(f"Gathering products from root category: {self.root_category.name} | {self.root_category.id}")
        products = self.conn.product.get_products_by_categories(f"{self.root_category.id}", total_pages=-1)
        product_items = cast(dict, products.data).get("items") or []

        for item in product_items:
            package = self.package_map.get(item["package"]["id"])
            if not package:
                raise ValueError(f"Package with id {item.get('package_id')} is cannot be found in package map")

            product, _ = cast(Tuple[CCVProduct, bool], self.get_or_instantiate(
                self.product,
                {
                    "productnumber": item["productnumber"],
                },
                {
                "name": item["name"],
                "id": item["id"],
                "package": package.name
                },
            ))

            self.product_map[product.id] = product


    def load_products_to_category(self):
        """Load all products to category by calling other methods"""
        for cat_id, cat in self.category_map.items():
            prod_to_cat = self.conn.product_to_category.get_product_to_category(id=cat_id, total_pages=-1)
            prod_to_cat_items = cast(dict, prod_to_cat.data).get("items") or []
            for item in prod_to_cat_items:
                prod = self.product_map.get(item.get("product_id"))
                if prod:
                    cat_to_dev, _ = self.get_or_instantiate(
                        CCVCategoryToDevice,
                        {
                            "category_name": cat.name,
                            "productnumber": prod.productnumber,
                        },
                        {
                            "id": item["id"],
                            "category_id": cat.id,
                            "product_id": prod.id,
                        },
                    )

                    prod.add_child(cat_to_dev)

                else:
                    logger.info("Skipping product with ID: %s", item.get("product_id"))


    def load_attribute_values_to_product(self):
        """Loads in all the attribute Values that are attached to a product"""

        products =  cast(list[CCVProduct], self.get_all(self.product))
        if not products:
            logger.warning("No products have been loaded in the adapter, if this is expected it's not a problem if not you might have loaded in your objects in the wrong order")
            return

        for product in products:
            result = self.conn.product_to_attribute.get_product_to_attribute_values(f"{product.id}")
            attribute_items = cast(dict, result.data).get("items") or []
            for item in attribute_items:
                attribute_value_to_product, _ = self.get_or_instantiate(
                    self.attribute_value_to_product,
                    {
                        "productnumber": product.productnumber,
                        "attribute": normalize_string(item['optionname']),
                        "value": normalize_string(item["optionvalue_name"])
                    },
                    {
                        "id": item["id"]
                    }
                )

                product.add_child(attribute_value_to_product)


    def load(self):
        """Load all models by calling other methods"""
        self.load_packages()
        self.load_categories()
        self.load_attributes()
        self.load_products()
        self.load_products_to_category()
        self.load_attribute_values_to_product()
