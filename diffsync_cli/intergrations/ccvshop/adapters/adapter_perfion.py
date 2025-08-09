import logging
import threading

from typing import Optional, cast, Tuple, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
from diffsync import Adapter
from requests.exceptions import RequestException
from diffsync import DiffSyncModel

from diffsync_cli.clients.perfion.client import PerfionClient
from diffsync_cli.config import ConfigSettings, load_yaml_config_file
from diffsync_cli.intergrations.ccvshop.models.base import (
    CategoryToDevice,
    AttributeValueToProduct,
    ProductPhoto,
)
from diffsync_cli.constants import DUTCH_SIZING, DUTCH_COLORS
from diffsync_cli.intergrations.ccvshop.models.perfion import (
    PerfionProduct
)
from diffsync_cli.utils import normalize_string, base64_image_from_url, append_if_not_exists

logger = logging.getLogger(__name__)



CONFIG_FILE_NAMESPACE = "diffsync_cli.config.perfion"

class PerfionAdapter(Adapter):
    """
    Perfion Adapter for DiffSync.

    This adapter integrates Perfion product data into the DiffSync framework.

    Attributes:
        product: The product model.
        category_to_device: The category-to-device model.
        attribute_value_to_product: The attribute-value-to-product model.
        product_photo: The product photo model.
        top_level: List of top-level models.
        sizing_mapping: Mapping for product sizing.
        color_mapping: Mapping for product colors.
        category_mapping: Mapping for product categories.
    """

    _lock = threading.Lock()

    product = PerfionProduct
    category_to_device = CategoryToDevice
    attribute_value_to_product = AttributeValueToProduct
    product_photo = ProductPhoto

    top_level = ["product"]

    sizing_mapping: Dict[str, Any] = load_yaml_config_file(CONFIG_FILE_NAMESPACE, "sizing.yaml").get("mapping", {})  # Maps sizes
    color_mapping: Dict[str, Any] = load_yaml_config_file(CONFIG_FILE_NAMESPACE, "color.yaml").get("mapping", {})  # Maps colors
    category_mapping: Dict[str, Any] = load_yaml_config_file(CONFIG_FILE_NAMESPACE, "category.yaml").get("mapping", {})  # Maps categories


    def __init__(self, *args, cfg: Optional[ConfigSettings] = None, client: PerfionClient, **kwargs):
        """
        Initialize the PerfionAdapter.

        Args:
            *args: Variable length argument list.
            cfg (Optional[ConfigSettings]): Configuration settings for the adapter.
            client (PerfionClient): Perfion client instance for API communication.
            **kwargs: Arbitrary keyword arguments.

        Raises:
            ValueError: If the CCVSHOP_ROOT_CATEGORY environment variable is not set.
        """
        super().__init__(*args, **kwargs)

        if not cfg:
            cfg = ConfigSettings()
            cfg.load_env_vars(["PERFION"])

        if not cfg.verify("CCVSHOP_ROOT_CATEGORY", "PERFION_CUSTOMER_NAME"):
            raise ValueError("CCVSHOP_ROOT_CATEGORY or/and PERFION_CUSTOMER_NAME is not set as an environment variable")

        self.cfg = cfg
        self.conn = client


    def process_product_category(self, product: PerfionProduct):

        root_category, _ = self.get_or_instantiate(
            self.category_to_device,
            {
                "category_name": self.cfg.get("CCVSHOP_ROOT_CATEGORY"),
                "productnumber": product.productnumber,
            }
        )
        self.add_child(product, root_category)

        if mapped_name := self.category_mapping.get(product.category):
            mapped_category, _ = self.get_or_instantiate(
                self.category_to_device,
                {
                    "category_name": mapped_name,
                    "productnumber": product.productnumber,
                }
            )
            self.add_child(product, mapped_category)
        else:
            logger.warning(f"Matching product category not found for: {product.category}")

    def process_product_attr(self, product: PerfionProduct):

        for x in [
            (self.sizing_mapping, product.sizing, DUTCH_SIZING),
            (self.color_mapping, product.colors, DUTCH_COLORS),
        ]:

            for attr in x[1]:
                value = x[0].get(attr)
                if not value:
                    logger.warning(f"Attribute {attr} cannot be mapped, skipping this attribute")
                else:
                    attr_value, created = self.get_or_instantiate(
                        self.attribute_value_to_product,
                        {
                            "productnumber": product.productnumber,
                            "attribute": x[2],
                            "value": normalize_string(value)
                        }
                    )
                    if created:
                        product.add_child(attr_value)

    def process_product_img(self, product: PerfionProduct):
        for color, url in product.images:
            if self.color_mapping.get(color):
                try:
                    b64_img = base64_image_from_url(url)
                except RequestException:
                    logger.error(f"Failed to fetch image from URL: {url}")
                    continue
                else:
                    product_photo, created = self.get_or_instantiate(
                        self.product_photo,
                        {
                            "productnumber": product.productnumber,
                            "file_type": "png",
                            "alttext": url
                        },
                        {"source": b64_img}
                    )

                    if created:
                        self.add_child(product, product_photo)
            else:
                logger.warning(f"Color {color} cannot be mapped, skipping this Image")



    def load_products(self):
        """
        Load products from the Perfion API and process their data.

        This method retrieves product data, creates product instances, and associates
        them with categories, attributes, and photos.

        Raises:
            RequestException: If an error occurs while fetching product images.
        """
        customer_name = self.cfg.get("PERFION_CUSTOMER_NAME")
        categories = [c.strip() for c in self.cfg.get("PERFION_CATEGORIES").split(',')]

        try:
            result = self.conn.get_products()
        except RequestException:
            logger.error("Something went wrong trying to conact perfion, unable to connect to...")
            exit(1)

        logger.info("Remote Data Loaded...")

        for product_data in result.data:
            if categories and product_data["Category"] not in categories:
                continue


            product, _ = cast(Tuple[PerfionProduct, bool], self.get_or_instantiate(
                model=self.product,
                ids= {
                    "productnumber": product_data.get("ItemNumber", "")},
                attrs= {
                    "name":f"{customer_name} {product_data.get('ItemName', '')}",
                    "package": "kartonnen doos",
                    "price": product_data.get("ERPGrossPrice1", 0.0),
                    "description":product_data.get("Description"),
                    "category": product_data["Category"]
                },
            ))

            append_if_not_exists(product_data.get("ERPColor"), product.colors)
            append_if_not_exists(product_data.get("TSizeNewDW"), product.sizing)
            append_if_not_exists((product_data.get("ERPColor"), product_data.get("BaseProductImageUrl")), product.images)

        return cast(List[PerfionProduct], self.get_all(self.product))

    def add_child(self, parent: DiffSyncModel, child: DiffSyncModel):
        """
        Helper Function to be able to add child objects safely while multithreading
        """
        with self._lock:
            return parent.add_child(child)

    def process_single_product(self, product):
        """
        Process a single product's categories, attributes, and images.
        """
        logger.info(f"Processing: {product.productnumber}: {product.name}")
        self.process_product_category(product)
        self.process_product_attr(product)
        self.process_product_img(product)

    def load(self):
        """
        Load all data into the DiffSync framework.

        This method serves as the entry point for loading products and their associated
        data into the adapter.
        """
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(self.process_single_product, self.load_products())
