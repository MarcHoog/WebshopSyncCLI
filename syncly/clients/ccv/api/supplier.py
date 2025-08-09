from syncly.clients.ccv.api.endpoint import CCVApiEndpoints
from typing import Dict, Any

class SupplierEndpoint(CCVApiEndpoints):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_supplier(self, body: Dict[str, Any]):
        return self.client._post("/api/rest/v1/suppliers", body=body)

    def get_suppliers(self, per_page: int = 100, total_pages: int = 1):
        return self.client._get_paged("/api/rest/v1/suppliers", per_page=per_page, total_pages=total_pages)
