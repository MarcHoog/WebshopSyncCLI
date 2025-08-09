from syncly.clients.ccv.api.endpoint import CCVApiEndpoints
from typing import Dict, Any

class ProductToAttributeEndpoint(CCVApiEndpoints):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_product_to_attribute_values(self, id: str, per_page: int = 100, total_pages: int = 1):
        return self.client._get_paged(f"/api/rest/v1/products/{id}/productattributevalues", per_page=per_page, total_pages=total_pages)

    def create_product_attribute_values(self, id: str, body: Dict[str, Any]):
        return self.client._post(f"/api/rest/v1/products/{id}/productattributevalues", body)

    def delete_product_attribute_value(self, id:str):
        return self.client._delete(f"/api/rest/v1/productattributevalues/{id}")
