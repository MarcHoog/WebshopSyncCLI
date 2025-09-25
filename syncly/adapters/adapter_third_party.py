import logging
from requests.exceptions import RequestException
from diffsync import Adapter, DiffSyncModel
from syncly.intergrations.ccvshop.models.third_party import ThirdPartyProduct
from abc import abstractmethod
from syncly.helpers import (
    normalize_string,
    base64_image_from_url,
    base64_image_from_url_contain
)
import threading
from typing import Optional, List, Any, Union, Generator, Type, Dict
from concurrent.futures import ThreadPoolExecutor
from syncly.intergrations.ccvshop.models.base import (
    CategoryToDevice,
    AttributeValueToProduct,
    ProductPhoto,
)

logger = logging.getLogger(__name__)

from syncly.config import SynclySettings

class ThirdPartyAdapter(Adapter):

    _lock = threading.Lock()

    product = ThirdPartyProduct
    category_to_device = CategoryToDevice
    attribute_value_to_product = AttributeValueToProduct
    product_photo = ProductPhoto

    top_level = ["product"]

    def __str__(self) -> str:
        return "ThirdPartyAdapter"

    def __init__(self, *args,
        settings:Optional[SynclySettings] = None,
        client: Optional[Any] = None,
        **kwargs
    ):

        self.settings = settings or SynclySettings()
        self.conn = client
        self.image_mode = 'crop'

        # Commen mappings
        self.sizing_mapping = self.settings.mapping.size
        self.color_mapping = self.settings.mapping.color
        self.category_mapping = self.settings.mapping.category

        super().__init__(*args, **kwargs)

    @abstractmethod
    def _get_products(self) -> Union[List[Type[Dict]], Generator[Type[Dict], Any, Any]]:
        pass

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

    def process_categories(self, product: ThirdPartyProduct):
        """
        Process and add all relevant categories to the product.
        """
        if not self.settings.ccv_shop.root_category:
            raise ValueError("Expected a root category to exists to attach devices to")

        categories = [self.settings.ccv_shop.root_category]
        for cat in product.category:
            if mapped := self.category_mapping.get(cat):
                categories.append(mapped)
            else:
                logger.warning(f"Matching product category not found for: {product.category}")
        categories.extend(self.settings.ccv_shop.aditional_categories)
        for category in categories:
            cat_obj, _ = self.get_or_instantiate(
                self.category_to_device,
                {
                    "category_name": category,
                    "productnumber": product.productnumber,
                }
            )
            self.add_child(product, cat_obj)

    # TODO make this a class for mode
    def process_images(self, product: ThirdPartyProduct, mode: str = 'crop'):
        """
        Process and add images to the product.
        """
        image_height = self.settings.ccv_shop.image_height
        image_width = self.settings.ccv_shop.image_width

        for color, url in product.images:
            if not self.color_mapping.get(color):
                logger.warning(f"Color {color} cannot be mapped, This image might be for a product that cannot be orderd")
            try:

                if mode == 'crop':
                    b64_img = base64_image_from_url(url, (image_width, image_height))
                elif mode == 'contain':
                    b64_img = base64_image_from_url_contain(url,(image_width, image_height))
                else:
                    raise ValueError("Unkown proccesing mode")

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

    @abstractmethod
    def load_products(self) -> List[ThirdPartyProduct]:
        pass

    @abstractmethod
    def process_single_product(self, product: ThirdPartyProduct):
        """
        Process a single product's categories, attributes, and images.
        """
        logger.debug(f"Processing: {product.productnumber}: {product.name}")
        self.process_categories(product)
        self.process_mapped_attributes(product, self.sizing_mapping, product.sizing, self.settings.ccv_shop.sizing_category)
        self.process_mapped_attributes(product, self.color_mapping, product.colors, self.settings.ccv_shop.color_category)
        self.process_images(product, self.image_mode)

    def add_child(self, parent: DiffSyncModel, child: DiffSyncModel):
        """
        Helper Function to be able to add child objects safely while multithreading
        """
        with self._lock:
            return parent.add_child(child)

    def load(self):
        """
        Load all data into the DiffSync framework.

        This method serves as the entry point for loading products and their associated
        data into the adapter.
        """
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(self.process_single_product, self.load_products())
