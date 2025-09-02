from typing import List, Tuple
from syncly.intergrations.ccvshop.models.base import Product

class ThirdPartyProduct(Product):

    category: str
    colors: List[str] = []
    sizing: List[str] = []
    images: List[Tuple[str, str]] = []
