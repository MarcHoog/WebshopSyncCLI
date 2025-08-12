from syncly.clients.ccv.api.endpoint import CCVApiEndpoints
from typing import  Any

class BrandEndpoint(CCVApiEndpoints):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_brands(self, per_page=100, total_pages=1, **params: Any):
        return self.client._get_paged("/api/rest/v1/brands", per_page, total_pages, **params)
