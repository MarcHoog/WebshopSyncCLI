import logging
import json
import os
from typing import Optional
from diffsync import Adapter
from diffsync_cli.config import ConfigSettings
from diffsync_cli.intergrations.ccvshop.models.base import Product, CategoryToDevice, AttributeValueToProduct
from diffsync_cli.utils import normalize_string

logger = logging.getLogger(__name__)

class MockAdapter(Adapter):
    """DiffSync Adapter using requests to communicate to CCVShop"""

    product = Product
    category_to_device = CategoryToDevice
    attribute_value_to_product = AttributeValueToProduct

    top_level = ["product"]

    def __init__(self, *args, cfg: Optional[ConfigSettings]= None, mock_file_path: Optional[str] = None, **kwargs,):
        super().__init__(*args, **kwargs)

        if not cfg:
            cfg = ConfigSettings()
            cfg.load_env_vars(["MOCK"])

        if not mock_file_path:
            mock_file_path = cfg.get("MOCK_FILE_PATH")

        self.cfg = cfg

        if not mock_file_path:
            raise ValueError("Expected `MOCK_FILE_PATH` to exist in config")

        self.mock_file_path = mock_file_path

    def setup(self):
       if not os.path.exists(self.mock_file_path):
           raise ValueError(f"Mock file path {self.mock_file_path} does not exist")

    def load_products_from_json(self):
        with open(self.mock_file_path, "r") as f:
            data = json.load(f)
            for product_data in data:
                product = self.product(
                    name=product_data.get("name", ""),
                    productnumber=product_data.get("article_number", ""),
                    package=product_data.get("package", "Kartonnen doos").strip().lower(),
                )
                self.add(product)

                for category_name in product_data.get("categories", []):
                    category, _ = self.get_or_instantiate(
                        CategoryToDevice,
                        {
                            "category_name": category_name,
                            "productnumber": product.productnumber,
                        },
                    )
                    product.add_child(category)


                for propertie, values in product_data.get("properties", {}).items():

                    for value in values:
                        attr_to_prod, _  = self.get_or_instantiate(
                            self.attribute_value_to_product,
                            {
                                "productnumber": product.productnumber,
                                "attribute": normalize_string(propertie),
                                "value": normalize_string(value),
                            },
                        )

                        product.add_child(attr_to_prod)











    def load(self):
        """Load all models by calling other methods"""

        self.load_products_from_json()
