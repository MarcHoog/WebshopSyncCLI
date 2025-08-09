from typing import List
from diffsync_cli.intergrations.ccvshop.models.base import Product



class PerfionProduct(Product):

    category: str
    colors: List[str] = []
    sizing: List[str] = []
    images: List[str] = []
