import requests
import logging
import json
from typing import cast

from typing import Dict, Optional, Any, Union
from diffsync_cli.clients.ccv.auth import CCVAuth

# TODO: Consuludate this all into like one __init__ file cause this is a bit "extra"
from diffsync_cli.clients.ccv.api.product import ProductEndpoint
from diffsync_cli.clients.ccv.api.category import CategoryEndpoint
from diffsync_cli.clients.ccv.api.package import PackageEndpoint
from diffsync_cli.clients.ccv.api.product_to_category import ProductToCategoryEndpoint
from diffsync_cli.clients.ccv.api.attributes import AttributesEndpoint
from diffsync_cli.clients.ccv.api.supplier import SupplierEndpoint
from diffsync_cli.clients.ccv.api.product_to_attribute import ProductToAttributeEndpoint
from diffsync_cli.clients.ccv.api.product_photos import ProductPhotoEndpoint


from diffsync_cli.clients.ccv.models import CCVShopResult
from diffsync_cli.config import ConfigSettings


logger = logging.getLogger(__name__)

class CCVClient():

    SUPPORTED_METHODS = ['GET', 'POST', 'DELETE']

    def __init__(self,
                 base_url: Optional[str] = None,
                 cfg: Optional[ConfigSettings] = None,
                 verify_ssl: bool = True):

        if not cfg:
            logger.warning("ConfigSettings not provided, using default and loading environment variables")
            cfg = ConfigSettings()
            cfg.load_env_vars(["CCVSHOP"])

        if not cfg.verify("CCVSHOP_PRIVATE_KEY", "CCVSHOP_PUBLIC_KEY"):
            raise ValueError("CCVSHOP_PRIVATE_KEY and or CCVSHOP_PUBLIC_KEY should be passed or defined in environment Variables or passed through config")

        if not base_url and cfg.verify("CCVSHOP_BASE_URL"):
            base_url = cast(str, cfg.get("CCVSHOP_BASE_URL"))
        else:
            raise ValueError("CCVSHOP_BASE_URL should be passed or defined in environment Variables or passed through config")

        self.cfg = cfg
        public_key = self.cfg.get("CCVSHOP_PUBLIC_KEY")
        secret_key = self.cfg.get("CCVSHOP_PRIVATE_KEY")

        base_url = base_url.strip('/')
        self.auth = CCVAuth(base_url, public_key, secret_key)
        self.base_url = base_url
        self.default_headers = {
            "Content-Type": "application/json"
        }

        self.verifiy_ssl = verify_ssl

        self.product = ProductEndpoint(self)
        self.categories = CategoryEndpoint(self)
        self.packages = PackageEndpoint(self)
        self.product_to_category = ProductToCategoryEndpoint(self)
        self.product_to_attribute = ProductToAttributeEndpoint(self)
        self.supplier = SupplierEndpoint(self)
        self.attributes = AttributesEndpoint(self)
        self.photos = ProductPhotoEndpoint(self)

    def _do(
        self,
        method: str,
        uri: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        raw: Any = None
    ) -> CCVShopResult: # type: ignore

        if method.upper() not in self.SUPPORTED_METHODS:
            raise ValueError(f"Method of type {method.upper()} is not supported please use any of {self.SUPPORTED_METHODS}")


        uri = f"/{uri.strip('/')}/"
        url = f"{self.base_url}{uri}"

        data = None
        if body != None:
            try:
                data = json.dumps(body)
            except json.decoder.JSONDecodeError:
                raise ValueError(f"Body: {body} couldn't be decoded into json, if you want to send a non decodable body, or raw  ")

        resp = requests.request(
            url=url,
            method=method.upper(),
            params=params,
            auth=self.auth,
            headers=self.default_headers,
            verify=self.verifiy_ssl,
            data=data or raw
        )

        resp_data = None
        if resp.ok:
            try:
                if method in ["POST", "GET"]:
                    resp_data = resp.json()
            except json.decoder.JSONDecodeError as e:
                raise e
            return CCVShopResult(status_code=resp.status_code,
                                       data=resp_data)

        if not resp.ok:
            logger.warning(f"Non-2xx response: {resp.status_code} - {resp.text}")
            try:
                resp.raise_for_status()
            except requests.HTTPError as e:
                raise Exception(f"HTTP request failed: {e}") from e

    def _get(
        self,
        uri_path: str,
        **params
    ) -> CCVShopResult:
        """
        Internal helper to perform GET requests.

        Args:
            uri_path: Relative URI path to append to base URL.
            **params: Optional query parameters as keyword arguments.

        Returns:
            requests.Response: The HTTP response object.
        """
        return self._do(
            method="GET",
            uri=uri_path,
            params=params if params else None,
        )


    def _post(self,uri_path: str, body: Dict[str, Any]) -> CCVShopResult:
        """
        Internal helper to perform POST requests.

        Args:
            uri_path: Relative URI path to append to base URL.
            body: body Data to send

        Returns:
            requests.Response: The HTTP response object.
        """
        return self._do(
            method="POST",
            uri=uri_path,
            body=body,
        )



    def _delete(self, uri_path: str) -> CCVShopResult:
        """
        Internal helper to perform DELETE requests.

        Args:
            uri_path: Relative URI path to append to base URL.

        Returns:
            requests.Response: The HTTP response object.
        """
        return self._do(
            method="DELETE",
            uri=uri_path,
        )

    def _get_paged(self, uri_path: str, per_page: int, total_pages: Union[str, int], **params: Any):
        """
        Fetch paginated results from a CCV Shop API endpoint.

        This helper performs multiple GET requests to retrieve paginated data. It supports
        both a fixed number of pages or automatic pagination by setting total_pages="all".

        Args:
            uri_path: The relative URI path to request (e.g., "products").
            per_page: Number of items per request (min 1, max 250).
            total_pages: Number of pages to retrieve, or "all" to fetch until 'next' is empty.
            **params: Additional query parameters to pass to the request.

        Returns:
            CCVShopResult: Combined result with all paginated items in result.data["items"].
        """

        if isinstance(total_pages, str):
            if total_pages == "all":
                total_pages = -1
            else:
                raise ValueError(f"Total Pages `{total_pages}` can only be defined as 'all' when string")
        elif isinstance(total_pages, int) and (total_pages < -1 or total_pages == 0):
            raise ValueError("Total Pages cannot be below -1 or 0 when int")

        per_page = max(1, min(per_page, 250))
        start = 0
        results = []
        pages = 0

        status_code = -1

        while pages < total_pages or total_pages == -1:
            paging_params = {
                "start": start,
                "size": per_page,
            }
            result = self._get(uri_path, **{**params, **paging_params})
            status_code = result.status_code

            if not result.data:
                raise ValueError("Something unexpected happend")

            items = result.data.get("items")
            if items is None:
                raise ValueError("Expected 'items' field missing in response")
            results.extend(items)

            pages += 1
            next_link = result.data.get("next")

            if not next_link:
                break

            start += per_page

        return CCVShopResult(status_code=status_code, data={
            "items": results,
            "total_pages": pages,
            "total_items": len(results),
        })
