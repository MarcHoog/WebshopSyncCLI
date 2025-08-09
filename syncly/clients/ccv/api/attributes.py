from syncly.clients.ccv.api.endpoint import CCVApiEndpoints
from typing import Any

class AttributesEndpoint(CCVApiEndpoints):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_attribute(self, id: str):
        return self.client._get(f"/api/rest/v1/attributes/{id}")

    def get_attribute_values(self, id: str):
        return self.client._get(f"/api/rest/v1/attributes/{id}/attributevalues")

    def get_attributes(self, per_page=100, total_pages=1, **params: Any):
        return self.client._get_paged("/api/rest/v1/attributes", per_page, total_pages, **params)
