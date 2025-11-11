from diffsync import DiffSyncModel


class Category(DiffSyncModel):
    """
    DiffSync model for a category.

    Attributes:
        name (str): The category name.
    """

    _modelname = "category"
    _identifiers = ("name",)
    _attributes = ()

    name: str


class Package(DiffSyncModel):
    """
    DiffSync model for a package.

    Attributes:
        name (str): The package name.
    """

    _modelname = "package"
    _identifiers = ("name",)
    _attributes = ()

    name: str


class Brand(DiffSyncModel):
    """
    DiffSync model for a Brand.

    Attributes:
        name (str): The Brand name.
    """

    _modelname = "brand"
    _identifiers = ("name",)
    _attributes = ()

    name: str


class Supplier(DiffSyncModel):
    """
    DiffSync model for a supplier.

    Attributes:
        name (str): The supplier name.
    """

    _modelname = "supplier"
    _identifiers = ("name",)
    _attributes = ()

    name: str


class Attribute(DiffSyncModel):
    """
    DiffSync model for an attribute.

    Attributes:
        name (str): The attribute name.
        attribute_values (list): List of values for this attribute.
    """

    _modelname = "attribute"
    _identifiers = ("name",)
    _attributes = ()
    _children = {"attribute_value": "attribute_values"}

    name: str
    attribute_values: list = []


class AttributeValue(DiffSyncModel):
    """
    DiffSync model for a single attribute value.

    Attributes:
        attribute (str): Identifier of the parent attribute.
        value (str): The value string.
    """

    _modelname = "attribute_value"
    _identifiers = ("attribute", "value")
    _attributes = ()

    attribute: str
    value: str


class Product(DiffSyncModel):
    """
    DiffSync model for a product.

    Attributes:
        name (str): Product name.
        productnumber (str): Unique product identifier.
        package (str): Package identifier.
        price (int): Product price.
        short_description (str): Brief description.
        description (str): Full product description.
        categories (list): Associated categories.
        attributes (list): Associated attribute values.
        photos (list): Associated product photos.
    """

    _modelname = "product"
    _identifiers = ("productnumber",)
    _attributes = (
        "name",
        "short_description",
        "description",
        "package",
        "price",
        "brand",
        "page_title",
        "meta_description",
        "meta_keywords",
    )
    _children = {
        "category_to_device": "categories",
        "attribute_value_to_product": "attributes",
        "product_photo": "photos",
    }

    name: str
    productnumber: str
    package: str
    brand: str = ""
    price: float = 0
    short_description: str = ""
    description: str = ""
    categories: list = []
    attributes: list = []
    photos: list = []

    # SEO Fields
    page_title: str = ""
    meta_description: str = ""
    meta_keywords: str = ""


class CategoryToDevice(DiffSyncModel):
    """
    DiffSync model linking a category to a product.

    Attributes:
        category_name (str): Name of the category.
        productnumber (str): Identifier of the product.
    """

    _modelname = "category_to_device"
    _identifiers = ("category_name", "productnumber")
    _attributes = ()

    category_name: str
    productnumber: str


class AttributeValueToProduct(DiffSyncModel):
    """
    DiffSync model linking an attribute value to a product.

    Attributes:
        productnumber (str): Identifier of the product.
        attribute (str): Identifier of the attribute.
        value (str): The attribute value.
        price (int): Price override for this attribute value.
    """

    _modelname = "attribute_value_to_product"
    _identifiers = ("productnumber", "attribute", "value")
    _attributes = ("price",)

    productnumber: str
    attribute: str
    value: str
    price: float = 0


class ProductPhoto(DiffSyncModel):
    """
    DiffSync model for a product photo.

    Attributes:
        filename (str): Photo filename.
        filetype (str): File extension/type.
        productnumber (str): Identifier of the product.

        source (str): Base64 of the image.
        alttext (str): Alternate text for the photo.
        is_main (bool): Flag indicating if this is the main photo.
    """

    _modelname = "product_photo"
    _identifiers = ("productnumber", "alttext", "file_type")
    _attributes = ("source",)

    file_type: str
    productnumber: str
    source: str
    alttext: str = ""
    is_main: bool = False
