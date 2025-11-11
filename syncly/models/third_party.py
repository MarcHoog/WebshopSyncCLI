from typing import List, Tuple
from .base import Product


class ThirdPartyProduct(Product):
    category: List[str] = []
    colors: List[tuple[str, float]] = []
    sizing: List[Tuple[str, float]] = []
    images: List[Tuple[str, str]] = []
