import logging

from typing import cast, Tuple, List
from requests.exceptions import RequestException
from syncly.intergrations.ccvshop.models.third_party import ThirdPartyProduct
from syncly.helpers import normalize_string, append_if_not_exists, wrap_style
from syncly.intergrations.ccvshop.adapters.adapter_third_party import ThirdPartyAdapter

logger = logging.getLogger(__name__)


class PerfionAdapter(ThirdPartyAdapter):

    def __str__(self):
        return "PerfionAdapter"

    def _get_products(self):
        assert self.conn

        included_categories = self.settings.perfion.included_categories
        excluded_products = self.settings.perfion.excluded_products

        try:
            result = self.conn.get_products()
        except RequestException:
            logger.error("Something went wrong trying to conact perfion, unable to connect to...")
            exit(1)

        _return = []

        for product_data in result.data:
            if included_categories and product_data["Category"] not in included_categories:
                logger.info(f"Skipping product {product_data.get('ItemNumber')} not in included categories: {included_categories}")
                continue
            if product_data.get("ItemNumber") in excluded_products:
                logger.info(f"Skipping excluded product: {product_data.get('ItemNumber')}")
                continue

            _return.append(product_data)
            yield product_data

        return _return


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


        brand = self.settings.ccv_shop.brand

        for product_data in self._get_products():

            product, _ = cast(Tuple[ThirdPartyProduct, bool], self.get_or_instantiate(
                model=self.product,
                ids= {
                    "productnumber": product_data.get('ItemNumber', '')},
                attrs= {
                    "name":f"{brand} {product_data.get('ItemName', '')}",
                    "package": "kartonnen doos",
                    "price": product_data.get('ERPGrossPrice1', 0.0),
                    "description": wrap_style(product_data.get('Description')),
                    "category": [product_data['Category']],
                    "brand": normalize_string(brand),

                    "page_title": f"{brand} {product_data.get('ItemName', '')} ({product_data.get('ItemNumber', '')})",
                    "meta_description": parse_meta_description(product_data.get('Description', '')),
                },
            ))

            append_if_not_exists(product_data.get("ERPColor"), product.colors)
            append_if_not_exists(product_data.get("TSizeNewDW"), product.sizing)
            append_if_not_exists((product_data.get("ERPColor"), product_data.get("BaseProductImageUrl")), product.images)

        return cast(List[ThirdPartyProduct], self.get_all(self.product))
