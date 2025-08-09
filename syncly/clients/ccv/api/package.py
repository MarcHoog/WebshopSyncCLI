from syncly.clients.ccv.api.endpoint import CCVApiEndpoints
from typing import Dict, Any

class PackageEndpoint(CCVApiEndpoints):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_package(self, id: str):
        return self.client._get(f"/api/rest/v1/packages/{id}")

    def get_packages(self, per_page=100, total_pages=1, **params: Any):
        return self.client._get_paged("/api/rest/v1/packages", per_page, total_pages, **params)

    def create_package(self, body: Dict):
        return self.client._post("/api/rest/v1/packages", body)
