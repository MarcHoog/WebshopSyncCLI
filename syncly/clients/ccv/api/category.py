from syncly.clients.ccv.api.endpoint import CCVApiEndpoints
from typing import Dict, Any

class CategoryEndpoint(CCVApiEndpoints):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_category(self, id: str):
        return self.client._get(f"/api/rest/v1/categories/{id}")

    def get_sub_categories(self, per_page=100, total_pages=1, **params: Any):
        return self.client._get_paged(f"/api/rest/v1/categories/{id}/categories", per_page, total_pages, **params)

    def get_categories(self, per_page=100, total_pages=1, **params: Any):
        return self.client._get_paged("/api/rest/v1/categories", per_page, total_pages, **params)

    def create_category(self, body: Dict):
        return self.client._post("/api/rest/v1/categories", body)
