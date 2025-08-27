import logging
import threading

from typing import cast, Tuple, List
from concurrent.futures import ThreadPoolExecutor
from diffsync import Adapter
from requests.exceptions import RequestException
from diffsync import DiffSyncModel

from syncly.clients.perfion.client import PerfionClient
from syncly.config import EnvSettings, SynclySettings
from syncly.intergrations.ccvshop.models.base import (
    CategoryToDevice,
    AttributeValueToProduct,
    ProductPhoto,
)
from syncly.intergrations.ccvshop.models.perfion import (
    PerfionProduct
)
from syncly.utils import normalize_string, base64_image_from_url, append_if_not_exists, wrap_style

logger = logging.getLogger(__name__)


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

    def __str__(self):
        return "PerfionAdapter"

    def __init__(self, *args, cfg: EnvSettings, settings: SynclySettings, client: PerfionClient, **kwargs):
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

        if not settings.ccv_shop.general.root_category and not settings.perfion.general.brand:
            raise ValueError("ccv_shop.general.root_cateory or perfion.general.brand is not set in settings.yaml")

        self.cfg = cfg
        self.settings = settings
        self.conn = client

        self.sizing_mapping = self.settings.perfion.mapping.size
        self.color_mapping = self.settings.perfion.mapping.color
        self.category_mapping = self.settings.perfion.mapping.category


    def process_categories(self, product: PerfionProduct):
        """
        Process and add all relevant categories to the product.
        """
        categories = [self.settings.ccv_shop.general.root_category]
        if mapped := self.category_mapping.get(product.category):
            categories.append(mapped)
        else:
            logger.warning(f"Matching product category not found for: {product.category}")
        categories.extend(self.settings.perfion.general.aditional_categories)
        for category in categories:
            cat_obj, _ = self.get_or_instantiate(
                self.category_to_device,
                {
                    "category_name": category,
                    "productnumber": product.productnumber,
                }
            )
            self.add_child(product, cat_obj)


    def process_mapped_attributes(self, product, mapping, product_attrs, attribute_name):
        """
        Generalized processing for mapped attributes (e.g., sizing, color).
        """
        for attr in product_attrs:
            value = mapping.get(attr)
            if not value:
                logger.debug(f" No Mapped Attribute {attr} will be used as is")
                value = attr
            attr_value, created = self.get_or_instantiate(
                self.attribute_value_to_product,
                {
                    "productnumber": product.productnumber,
                    "attribute": attribute_name,
                    "value": normalize_string(value)
                }
            )
            if created:
                product.add_child(attr_value)

    def process_images(self, product: PerfionProduct):
        """
        Process and add images to the product.
        """
        image_height = self.settings.perfion.general.image_height
        image_width = self.settings.perfion.general.image_width

        for color, url in product.images:
            if not self.color_mapping.get(color):
                logger.warning(f"Color {color} cannot be mapped, skipping this Image")
                continue
            try:
                b64_img = base64_image_from_url(url, (image_width, image_height))
            except RequestException:
                logger.error(f"Failed to fetch image from URL: {url}")
                continue
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


    def _get_products(self):
        included_categories = self.settings.perfion.general.included_categories
        excluded_products = self.settings.perfion.general.excluded_products

        try:
            result = self.conn.get_products()
        except RequestException:
            logger.error("Something went wrong trying to conact perfion, unable to connect to...")
            exit(1)

        for product_data in result.data:
            if included_categories and product_data["Category"] not in included_categories:
                logger.info(f"Skipping product {product_data.get('ItemNumber')} not in included categories: {included_categories}")
                continue
            if product_data.get("ItemNumber") in excluded_products:
                logger.info(f"Skipping excluded product: {product_data.get('ItemNumber')}")
                continue

            yield product_data


    def load_products(self):
        """
        Load products from the Perfion API and process their data.

        This method retrieves product data, creates product instances, and associates
        them with categories, attributes, and photos.
        """

        def parse_meta_description(string):

            string = string.strip("<p>")
            if len(string) >= 317:
                string = string[:317]

            return f"{string}..."


        brand = self.settings.perfion.general.brand

        for product_data in self._get_products():

            product, _ = cast(Tuple[PerfionProduct, bool], self.get_or_instantiate(
                model=self.product,
                ids= {
                    "productnumber": product_data.get('ItemNumber', '')},
                attrs= {
                    "name":f"{brand} {product_data.get('ItemName', '')}",
                    "package": "kartonnen doos",
                    "price": product_data.get('ERPGrossPrice1', 0.0),
                    "description": wrap_style(product_data.get('Description')),
                    "category": product_data['Category'],
                    "brand": normalize_string(brand),

                    "page_title": f"{brand} {product_data.get('ItemName', '')} ({product_data.get('ItemNumber', '')})",
                    "meta_description": parse_meta_description(product_data.get('Description', '')),
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
        logger.debug(f"Processing: {product.productnumber}: {product.name}")
        self.process_categories(product)
        self.process_mapped_attributes(product, self.sizing_mapping, product.sizing, self.settings.ccv_shop.general.sizing_category)
        self.process_mapped_attributes(product, self.color_mapping, product.colors, self.settings.ccv_shop.general.color_category)
        self.process_images(product)

    def load(self):
        """
        Load all data into the DiffSync framework.

        This method serves as the entry point for loading products and their associated
        data into the adapter.
        """
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(self.process_single_product, self.load_products())
