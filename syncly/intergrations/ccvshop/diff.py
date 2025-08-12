import logging

from typing import Dict, Any
from collections import defaultdict
from diffsync.diff import Diff
from syncly.constants import DUTCH_COLORS, DUTCH_SIZING
from syncly.config import SynclySettings

from syncly.utils import normalize_string

logger = logging.getLogger(__name__)

class AttributeOrderingDiff(Diff):


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
        # Build a value → index map for O(1) lookups
        index_of = {value: idx for idx, value in enumerate(reference_order)}

        # Prepare a fixed-length list to slot items into
        result = [None] * len(reference_order)

        for child in children:
            val = child.keys.get("value")
            pos = index_of.get(val)
            if pos is None:
                logger.warning("Unknown value %r, appending to end", val)
                result.append(child)
            else:
                result[pos] = child

        # Filter out empty slots and return
        return [item for item in result if item]

    @classmethod
    def order_children_attribute_value_to_product(cls, children: Dict[Any, Any]):
        """
        Group `children` by their 'attribute' key, then reorder the
        'lettermaatvoering' group according to our sizing mapping.
        """

        settings = SynclySettings.get_instance()
        sizing_mapping = settings.perfion.mapping.size
        color_mapping = settings.perfion.mapping.color

        attribute_groups: Dict[str, list] = defaultdict(list)
        for child in children.values():
            attr_name = child.keys.get("attribute", "")
            attribute_groups[attr_name].append(child)

        for x in [(DUTCH_SIZING, sizing_mapping), (DUTCH_COLORS, color_mapping)]:
            letter_group = attribute_groups.get(x[0], [])
            reference = [normalize_string(x) for x in x[1].values()]
            attribute_groups[x[0]] = cls._order_attributes(
                reference,
                letter_group
            )

        for childs in attribute_groups.values():
            for child in childs:
                yield child

    # @classmethod
    # def order_children_attribute_product_photo(cls, children: Dict[Any, Any]):
