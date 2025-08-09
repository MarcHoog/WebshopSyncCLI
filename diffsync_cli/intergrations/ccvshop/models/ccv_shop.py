from typing import TYPE_CHECKING, cast, Optional
from diffsync.exceptions import ObjectNotCreated, ObjectNotFound
from diffsync_cli.intergrations.ccvshop.models.base import (
    Category,
    Product,
    Package,
    CategoryToDevice,
    Attribute,
    AttributeValue,
    AttributeValueToProduct,
    ProductPhoto,

)

import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from diffsync_cli.intergrations.ccvshop.adapters.adapter_ccv import CCVShopAdapter

class CCVPackage(Package):
    """ CCV Shop implementation of the Category model"""

    id: int

class CCVCategory(Category):
    """ CCV Shop implementation of the Category model"""

    id: int

class CCVAttribute(Attribute):

    id: int

class CCVAttributeValue(AttributeValue):

    id: int


class CCVProduct(Product):
    """ CCV Shop implementation of the Product model"""

    id: int

    @classmethod
    def create(cls, adapter: "CCVShopAdapter", ids, attrs): # type: ignore
        """Create a Prodct object in CCV Shop."""
        try:
            package = cast(CCVPackage, adapter.get(CCVPackage, attrs.get("package", "")))
        except ObjectNotFound as e:
            logger.warning(f"Package of {attrs.get('package_name', '')} not found in Loaded Packages skipping creation of Product")
            raise e

        product_payload = {
            "name": attrs["name"],
            "productnumber" : ids["productnumber"],
            "description": attrs["description"],
            "package_id": package.id,
            "price": attrs["price"],


            # TODO: Marc Define these somewhere else in the code
            # Default values that atm we don't sync These should be magic numbers
            # And should be defined somewhere pretier
            "active": False,
            "discount": 0,
            "taxtariff": "normal",
        }

        result = adapter.conn.product.create_product(product_payload)
        data = cast(dict, result.data)
        attrs['id'] = data['id']
        return super().create(adapter, ids, attrs)

    def update(self, attrs):
        """Update implementation of CCV Category"""
        return super().update(attrs)

    def delete(self):
        """Delete implementation of CCV Category"""
        return super().delete()


class CCVCategoryToDevice(CategoryToDevice):
    """ CCV Shop implementation of the Category model"""

    id: Optional[int] = None
    category_id: Optional[int] = None
    product_id: Optional[int] = None

    @classmethod
    def create(cls, adapter: "CCVShopAdapter", ids, attrs): #  type: ignore
        productnumber = ids.get("productnumber", "")
        category_name =  ids.get("category_name", "")
        try:
            product = cast(CCVProduct, adapter.get(CCVProduct, productnumber))
            category = cast(CCVCategory, adapter.get(CCVCategory, category_name))
        except ObjectNotFound as e:
            logger.error(f"Couldn't find product or category {productnumber} or {category_name}")
            raise e

        prod_to_cat_payload = {
            "product_id": product.id,
            "category_id": category.id
        }
        result = adapter.conn.product_to_category.create_product_to_category(prod_to_cat_payload)
        data = result.data if result.data else {}
        attrs.update({
            "id" : data["id"],
            "category_id": category.id,
            "product_id": product.id,
            }
        )
        return super().create(adapter, ids, attrs)

    def delete(self):
        """Delete implementation of CCV Category"""
        adapter = cast("CCVShopAdapter", self.adapter)
        if not self.id:
            raise ValueError("Expected exesting object to have an ID")

        adapter.conn.product_to_category.delete_product_to_category(f"{self.id}")
        return super().delete()

class CCVAttributeValueToProduct(AttributeValueToProduct):

    id: int

    @classmethod
    def create(cls, adapter: "CCVShopAdapter", ids, attrs): # type: ignore 'Create is compatible'
        productnumber = ids.get("productnumber", "")
        attribute = ids.get("attribute", "")
        value = ids.get("value", "")

        try:
            product = cast(CCVProduct, adapter.get(CCVProduct, {"productnumber": productnumber}))
            attribute_value = cast(CCVAttributeValue, adapter.get(CCVAttributeValue, {"attribute": attribute, "value": value}))
        except ObjectNotFound as e:
            logger.error(f"Could not find product {productnumber }or attribute value {value} {e}")
            raise ObjectNotCreated(e)

        attr_to_prod_payload = {
            "optionvalue": attribute_value.id,
            "price": attrs['price'],
        }

        result = adapter.conn.product_to_attribute.create_product_attribute_values(f"{product.id}", attr_to_prod_payload)
        data = result.data if result.data else {}
        attrs.update({
            "id": data["id"]
        })

        return super().create(adapter, ids, attrs)

    def delete(self):
        """Delete implementation of CCV Attribute Value to Product"""
        adapter = cast("CCVShopAdapter", self.adapter)
        if not self.id:
            raise ValueError("Expected exesting object to have an ID")

        adapter.conn.product_to_attribute.delete_product_attribute_value(f"{self.id}")
        return super().delete()



class CCVProductPhoto(ProductPhoto):

    id: int

    @classmethod
    def create(cls, adapter: "CCVShopAdapter", ids, attrs): # type: ignore 'Create is compatible'
        productnumber = ids.get("productnumber", "")

        try:
            product = cast(CCVProduct, adapter.get(CCVProduct, {"productnumber": productnumber}))
        except ObjectNotFound as e:
            logger.error("Could not find product or attribute value")
            raise e


        photo_payload = {
            "file_type": ids["file_type"],
            "alttext": ids["alttext"],
            "source": attrs["source"],
        }

        result = adapter.conn.photos.create_photo(f"{product.id}", photo_payload)
        data = result.data if result.data else {}
        attrs.update({
            "id": data["id"]
        })

        return super().create(adapter, ids, attrs)
