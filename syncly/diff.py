import logging

from typing import Dict, Any
from collections import defaultdict
from diffsync.diff import Diff

from .settings import get_settings
from .helpers import normalize_string

logger = logging.getLogger(__name__)


class AttributeOrderingDiff(Diff):
    @staticmethod
    def _order_sizing_attributes(children: list) -> list:
        """Reorder `children` based on their 'value' key, which represents sizes."""

        def parse_size(size: str):
            size = size.strip().upper()

            if size.isdigit():
                return (0, int(size))

            if "-" in size or "/" in size:
                sep = "-" if "-" in size else "/"
                parts = size.split(sep)
                try:
                    nums = [int(p) for p in parts]
                    return (0, nums[0], nums[1] if len(nums) > 1 else 0)
                except ValueError:
                    pass

            if size.startswith("W") and size[1:].isdigit():
                return (1, int(size[1:]))

            if size.startswith("C") and size[1:].isdigit():
                return (2, int(size[1:]))

            # Size Example 90C87 (length C circumference)
            if "C" in size:
                split_sizes = size.split("C")
                try:
                    length = int(split_sizes[0])
                    circumference = int(split_sizes[1])
                    return (4, length, circumference)
                except (ValueError, IndexError):
                    pass

            alpha_order = {
                "2XS": 90,
                "XS": 100,
                "XS/S": 101,
                "S": 102,
                "S-M": 103,
                "M": 104,
                "M/L": 105,
                "L": 106,
                "L-XL": 107,
                "XL": 108,
                "XXL": 109,
                "X/2XL": 110,
                "2XL": 111,
                "2XL-3XL": 112,
                "3XL": 113,
                "3/4XL": 114,
                "3XL-4XL": 115,
                "4XL": 116,
                "4XL-5XL": 117,
                "5XL": 118,
                "6XL": 119,
                "7XL": 120,
                "8XL": 121,
                "ONE": 200,
                "ONESIZE": 200,
            }
            if size in alpha_order:
                return (3, alpha_order[size])

            return (9, 999, size)

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
                #                logger.warning("Unknown value %r, appending to end", val)
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

        settings = get_settings()
        color_mapping = settings.mapping.color

        attribute_groups: Dict[str, list] = defaultdict(list)
        for child in children.values():
            attr_name = child.keys.get("attribute", "")
            attribute_groups[attr_name].append(child)

        # Order the 'kleuren' group
        letter_group = attribute_groups.get(settings.ccv_shop.color_category, [])
        reference = [normalize_string(x) for x in color_mapping.values()]  # type: ignore
        attribute_groups[settings.ccv_shop.color_category] = cls._order_attributes(
            reference, letter_group
        )

        # Order the 'maten' group
        sizing = attribute_groups.get(settings.ccv_shop.sizing_category, [])
        attribute_groups[settings.ccv_shop.sizing_category] = (
            cls._order_sizing_attributes(sizing)
        )

        for childs in attribute_groups.values():
            for child in childs:
                yield child
