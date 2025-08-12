from typing import TYPE_CHECKING, cast, Optional
from diffsync.exceptions import ObjectNotCreated, ObjectNotFound, ObjectNotDeleted, ObjectNotUpdated
from syncly.intergrations.ccvshop.models.base import (
    Category,
    Product,
    Package,
    CategoryToDevice,
    Attribute,
    AttributeValue,
    AttributeValueToProduct,
    ProductPhoto,
    Brand,

)

import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from syncly.intergrations.ccvshop.adapters.adapter_ccv import CCVShopAdapter

class CCVPackage(Package):
    """ CCV Shop implementation of the Category model"""

    id: int

class CCVBrand(Brand):
    """ CCV Shop implementation of the Brand model"""

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
            brand = cast(CCVBrand, adapter.get(CCVBrand, attrs.get("brand", "")))
        except ObjectNotFound as e:
            logger.warning(f"Package of {attrs.get('package', '')} or brand of {attrs.get('brand')} not found in Loaded Packages or Brands skipping creation of Product")
            raise ObjectNotCreated(e)

        product_payload = {
            "name": attrs["name"],
            "productnumber" : ids["productnumber"],
            "description": attrs["description"],
            "package_id": package.id,
            "brand_id": brand.id,
            "price": attrs["price"],

            # Defaults we don't check Should also be compared but not for now
            "photo_size": "BIG",
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
        adapter = cast("CCVShopAdapter", self.adapter)
        if not self.id:
            raise ObjectNotFound("Expected existing object to have an ID")

        package: Optional[CCVPackage] = None
        brand: Optional[CCVBrand] = None

        try:
            if "package" in attrs:
                package = cast(CCVPackage, adapter.get(CCVPackage, attrs["package"]))
            if "brand" in attrs:
                brand = cast(CCVBrand, adapter.get(CCVBrand, attrs["brand"]))

        except ObjectNotFound as e:
            logger.warning(f"Package of {attrs.get('package_name', '')} not found in Loaded Packages skipping creation of Product")
            raise ObjectNotUpdated(e)

        update_payload = {
            "name": attrs.get("name", ""),
            "description": attrs.get("description", ""),
            "package_id": package.id if package else None,
            "brand_id": brand.id if brand else None,
            "price": attrs.get("price", None),
        }

        adapter.conn.product.patch_product(f'{self.id}', {k: v for k, v in update_payload.items() if v})
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
            raise ObjectNotCreated(e)

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
            raise ObjectNotDeleted("Expected exesting object to have an ID")

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

    def delete(self):
        """Delete implementation of CCV Attribute Value to Product"""
        adapter = cast("CCVShopAdapter", self.adapter)
        if not self.id:
            raise ValueError("Expected exesting object to have an ID")

        adapter.conn.photos.delete_photo(f"{self.id}")
        return super().delete()
