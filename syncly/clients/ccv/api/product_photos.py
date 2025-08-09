from syncly.clients.ccv.api.endpoint import CCVApiEndpoints
from typing import Dict, Any

class ProductPhotoEndpoint(CCVApiEndpoints):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def delete_photo(self, id: str):
        return self.client._delete(f"/api/rest/v1/productphotos/{id}")

    def get_photos(self, id: str, per_page: int = 100, total_pages: int = 1):
        return self.client._get_paged(f"/api/rest/v1/products/{id}/productphotos", per_page=per_page, total_pages=total_pages)

    def create_photo(self, id: str, body: Dict[str, Any]):
        return self.client._post(f"/api/rest/v1/products/{id}/productphotos", body)
