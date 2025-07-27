from diffsync import DiffSyncModel

class Category(DiffSyncModel):
    _modelname = "category"
    _identifiers = ("name",)
    _attributes = ()

    name: str

class Package(DiffSyncModel):
    _modelname = "package"
    _identifiers = ("name",)
    _attributes = ()

    name: str

class Supplier(DiffSyncModel):
    _modelname = "supplier"
    _identifiers = ("name",)
    _attributes = ()

    name: str

class Attribute(DiffSyncModel):

    _modelname = "attribute"
    _identifiers = ("name", )
    _attributes = ()
    _children = {"attribute_value": "attribute_values"}

    name: str
    attribute_values: list = []


class AttributeValue(DiffSyncModel):

    _modelname = "attribute_value"
    _identifiers = ("attribute", "value")
    _attributes = ()

    attribute: str
    value :str


class Product(DiffSyncModel):

    _modelname = "product"
    _identifiers = ("productnumber",)
    _attributes = (
        "name",
        "short_description",
        "description",
        "package",
        "price",
    )
    _children = {
        "category_to_device": "categories",
        "attribute_value_to_product": "attributes",
        "product_photo": "photos",
    }

    name: str
    productnumber: str
    package: str
    price: int = 0
    short_description: str = ""
    description: str = ""
    categories: list = []
    attributes: list = []
    photos: list = []

class CategoryToDevice(DiffSyncModel):

    _modelname = "category_to_device"
    _identifiers = ("category_name", "productnumber")
    _attributes = ()

    category_name: str
    productnumber: str

class AttributeValueToProduct(DiffSyncModel):

    _modelname = "attribute_value_to_product"
    _identifiers = ("productnumber", "attribute", "value")
    _attributes = ("price",)

    productnumber: str
    attribute: str
    value: str
    price: int = 0


class ProductPhoto(DiffSyncModel):

    _model = "product_photo"
    _identifiers = ("productnumber", "name", "file_type")
    _attributes = ("alttext", "source", "is_main" )

    name: str
    file_type: str
    productnumber: str
    source: str
    alttext: str
    is_main: bool = False
