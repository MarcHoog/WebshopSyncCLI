from typing import List, Tuple
from syncly.intergrations.ccvshop.models.base import Product

class MascotProduct(Product):

    category: str
    colors: List[str] = []
    sizing: List[str] = []
    images: List[Tuple[str, str]] = []
    avalability:str = ""
    reorder_status: int = -1
