import logging

from typing import Dict, Any
from collections import defaultdict
from diffsync.diff import Diff
from syncly.config import SynclySettings

from syncly.utils import normalize_string

logger = logging.getLogger(__name__)

class AttributeOrderingDiff(Diff):

    @staticmethod
    def _order_sizing_attributes(children: list) -> list:
        """ Reorder `children` based on their 'value' key, which represents sizes.
        The order is determined by a custom parsing function that handles
        numeric ranges, fractions, and predefined size labels"""
        def parse_size(size: str):
            """ Parse a size string and return a tuple that can be used for sorting.
            The tuple consists of:
            - An integer indicating the type of size (0 for numeric, 1 for alpha)
            - An integer for numeric sizes or a predefined order for alpha sizes
            - The original size string for alpha sizes.
            """
            size = size.strip().upper()

            if "-" in size and not size.startswith("X"):
                parts = size.split("-")
                try:
                    return (0, int(parts[0]), int(parts[1]))
                except ValueError:
                    pass

            if "/" in size:
                num, frac = size.split("/")
                try:
                    return (0, int(num), int(frac))
                except ValueError:
                    pass

            if size.isdigit():
                return (0, int(size))

            alpha_order = {
                "XS": 100, "XS-S": 101, "S": 102, "M": 103, "M-L": 104,
                "L": 105, "XL": 106, "XL-XXL": 107, "XXL": 108,
                "3XL": 109, "3XL-4XL": 110, "4XL": 111,
                "5XL": 112, "6XL": 113, "7XL": 114, "8XL": 115,
                "OneSize": 200,
            }
            return (1, alpha_order.get(size, 999), size)

        return sorted(children, key=lambda child: parse_size(child.keys.get("value")))



    @staticmethod
    def _order_attributes(reference_order: list, children: list) -> list:
        """
        Reorder `children` so their .keys['value'] appear in the same
        sequence as `reference_order`. Extra children are appended.

        Args:
            reference_order (list): Sequence of values defining the new order.
            children (list): List of DiffSync child instances to reorder.

        Returns:
            list: Children reordered to match reference_order.
        """
        index_of = {value: idx for idx, value in enumerate(reference_order)}
        result = [None] * len(reference_order)

        for child in children:
            val = child.keys.get("value")
            pos = index_of.get(val)
            if pos is None:
                logger.warning("Unknown value %r, appending to end", val)
                result.append(child)
            else:
                result[pos] = child

        return [item for item in result if item]

    @classmethod
    def order_children_attribute_value_to_product(cls, children: Dict[Any, Any]):
        """
        Group `children` by their 'attribute' key, then reorder the
        'lettermaatvoering' group according to our sizing mapping.
        """

        settings = SynclySettings.get_instance()
        color_mapping = settings.mapping.color

        attribute_groups: Dict[str, list] = defaultdict(list)
        for child in children.values():
            attr_name = child.keys.get("attribute", "")
            attribute_groups[attr_name].append(child)

        # Order the 'kleuren' group
        letter_group = attribute_groups.get(settings.ccv_shop.color_category, [])
        reference = [normalize_string(x) for x in color_mapping.values()]
        attribute_groups[settings.ccv_shop.color_category] = cls._order_attributes(
            reference,
            letter_group
        )

        # Order the 'maten' group
        sizing = attribute_groups.get(settings.ccv_shop.sizing_category, [])
        attribute_groups[settings.ccv_shop.sizing_category] = cls._order_sizing_attributes(sizing)

        for childs in attribute_groups.values():
            for child in childs:
                yield child
