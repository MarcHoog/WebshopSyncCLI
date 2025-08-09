from syncly.clients.ccv.api.endpoint import CCVApiEndpoints
from typing import Dict, Any

class ProductToCategoryEndpoint(CCVApiEndpoints):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_product_to_category(self, body: Dict[str, Any]):
        return self.client._post("/api/rest/v1/producttocategories", body=body)

    def get_product_to_category(self, id: str, per_page: int = 100, total_pages: int = 1):
        return self.client._get_paged(f"/api/rest/v1/categories/{id}/producttocategories", per_page=per_page, total_pages=total_pages)

    def delete_product_to_category(self, id: str):
        return self.client._delete(f"/api/rest/v1/producttocategories/{id}/")
