from syncly.clients.ccv.api.endpoint import CCVApiEndpoints
from typing import Dict, Any

class ProductEndpoint(CCVApiEndpoints):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_product(self, body: Dict[str, Any]):
        return self.client._post("/api/rest/v1/products", body)

    def patch_product(self, id: str, body: Dict[str, Any]):
        return self.client._patch(f"/api/rest/v1/products/{id}", body)

    def delete_product(self, id:str):
        return self.client._delete(f"/api/rest/v1/products/{id}")

    def get_product(self, id: str):
        return self.client._get(f"/api/rest/v1/products/{id}")

    def get_products(self, per_page=100, total_pages=1, **params: Any):
        return self.client._get_paged("/api/rest/v1/products", per_page, total_pages, **params)

    def get_products_by_categories(self, id:str, per_page=100, total_pages=1, **params: Any):
        return self.client._get_paged(f"/api/rest/v1/categories/{id}/products", per_page, total_pages, **params)

    def get_products_by_brands(self, id: str, per_page=100, total_pages=1, **params: Any):
        return self.client._get_paged(f"/api/rest/v1/brands/{id}/products", per_page, total_pages, **params)

    def get_products_by_webshops(self, id: str, per_page=100, total_pages=1, **params: Any):
        return self.client._get_paged(f"/api/rest/v1/webshops/{id}/products", per_page, total_pages, **params)

    def get_products_by_conditions(self, id: str, per_page=100, total_pages=1, **params: Any):
        return self.client._get_paged(f"/api/rest/v1/conditions/{id}/products", per_page, total_pages, **params)

    def get_products_by_suppliers(self, id: str, per_page=100, total_pages=1, **params: Any):
        return self.client._get_paged(f"/api/rest/v1/suppliers/{id}/products", per_page, total_pages, **params)
