from typing import List, Tuple
from syncly.models.base import Product

class ThirdPartyProduct(Product):

    category: List[str] = []
    colors: List[str] = []
    sizing: List[str] = []
    images: List[Tuple[str, str]] = []
