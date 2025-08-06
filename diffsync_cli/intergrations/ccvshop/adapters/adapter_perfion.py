import logging

from typing import Optional, cast, Tuple, Dict, Any
from diffsync import Adapter
from diffsync_cli.clients.perfion.client import PerfionClient
from diffsync_cli.config import ConfigSettings, load_yaml_config_file
from diffsync_cli.intergrations.ccvshop.models.base import (
    Product,
    CategoryToDevice,
    AttributeValueToProduct,
)
from diffsync_cli.utils import normalize_string

logger = logging.getLogger(__name__)

CONFIG_FILE_NAMESPACE = "diffsync_cli/config/perfion"

class PerfionAdapter(Adapter):
    """Perfion Adapter for diffsync"""

    product = Product
    category_to_device = CategoryToDevice
    attribute_value_to_product = AttributeValueToProduct

    top_level = ["product"]

    sizing_mapping: Dict[str, Any] = load_yaml_config_file(CONFIG_FILE_NAMESPACE, "sizing.yaml").get("mapping", {})
    category_mapping: Dict[str, Any] = load_yaml_config_file(CONFIG_FILE_NAMESPACE, "category.yaml").get("mapping", {})


    def __init__(self, *args, cfg: Optional[ConfigSettings]=None, client: PerfionClient, **kwargs):
        super().__init__(*args, **kwargs)

        if not cfg:
            cfg = ConfigSettings()
            cfg.load_env_vars(["PERFION"])

        if not cfg.verify("CCVSHOP_ROOT_CATEGORY"):
            raise ValueError("PERFION_ROOT_CATEGORY is not set as an environment variable")

        self.cfg = cfg
        self.conn = client

    def load_products(self):
        result = self.conn.get_products()
        for product_data in result.data:
            product, created = cast(Tuple[Product, bool], self.get_or_instantiate(
                model=self.product,
                ids= {
                    "productnumber": product_data.get("itemNumber", "")},
                attrs= {
                    "name":product_data.get("itemName", ""),
                    "package":"Kartonnen Doos".strip().lower(),
                    "description":product_data.get("Description")
                },
            ))

            if created:
                root_category, _ = self.get_or_instantiate(
                    self.category_to_device,
                    {
                        "category_name": self.cfg.get("CCVSHOP_ROOT_CATEGORY"),
                        "productnumbe": product.productnumber,
                    }
                )
                product.add_child(root_category)

                if mapped_name := self.category_mapping.get(product_data.get("Category")):
                    mapped_category, _ = self.get_or_instantiate(
                        self.category_to_device,
                        {
                            "category_name": mapped_name,
                            "productnumbe": product.productnumber,
                        }
                    )
                    product.add_child(mapped_category)
                else:
                    logger.warning(f"Cannot find matching product category for {product_data.get("Category")}")

            sizing = self.sizing_mapping.get(product_data.get("TSizeNewDW"))
            if not sizing:
                logger.warning(f"Cannot find matching product sizing for size {sizing}")
            else:
                size, created = self.get_or_instantiate(
                    self.attribute_value_to_product,
                    {
                        "productnumber": product.productnumber,
                        "attribute": "Lettermaatvoering",
                        "value": normalize_string(sizing)
                    }
                )

                if created:
                    product.add_child(size)


    def load(self):
        self.load_products()
