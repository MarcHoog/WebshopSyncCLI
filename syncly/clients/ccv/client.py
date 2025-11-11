import requests
import logging
import json
import time
from requests.exceptions import ConnectionError, Timeout, RequestException
from urllib3.exceptions import ProtocolError

from typing import Dict, Optional, Any, Union
from .auth import CCVAuth

# TODO: Consuludate this all into like one __init__ file cause this is a bit "extra"
from .api.product import ProductEndpoint
from .api.category import CategoryEndpoint
from .api.package import PackageEndpoint
from .api.product_to_category import ProductToCategoryEndpoint
from .api.attributes import AttributesEndpoint
from .api.supplier import SupplierEndpoint
from .api.product_to_attribute import ProductToAttributeEndpoint
from .api.product_photos import ProductPhotoEndpoint
from .api.brands import BrandEndpoint
from .models import CCVShopResult

logger = logging.getLogger(__name__)
class CCVClient():

    def __init__(self,
                 public_key: str,
                 secret_key: str,
                 base_url: Optional[str] = None,
                 verify_ssl: bool = True):

        if not public_key or not secret_key:
            raise ValueError("public_key and or secret_key should be passed or defined in environment Variables or passed through config")
        if not base_url:
            raise ValueError("base url cannot be None")

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
        self.brands = BrandEndpoint(self)

    def _do(
        self,
        method: str,
        uri: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        raw: Any = None,
        attempt = 0,
        max_attempt = 3,
        wait_before_retry = 60
    ) -> CCVShopResult: # type: ignore

        uri = f"/{uri.strip('/')}/"
        url = f"{self.base_url}{uri}"

        data = None
        if body != None:
            try:
                data = json.dumps(body)
            except json.decoder.JSONDecodeError:
                raise ValueError(f"Body: {body} couldn't be decoded into json, if you want to send a non decodable body, or raw  ")

        # Try to make the request with connection error handling
        try:
            resp = requests.request(
                url=url,
                method=method.upper(),
                params=params,
                auth=self.auth,
                headers=self.default_headers,
                verify=self.verifiy_ssl,
                data=data or raw
            )
        except (ConnectionError, ProtocolError, Timeout) as conn_error:
            # Handle connection errors with exponential backoff
            attempt += 1
            if attempt <= max_attempt:
                # Exponential backoff: 5s, 10s, 20s
                wait_time = 5 * (2 ** (attempt - 1))
                logger.warning(
                    f"Connection error on attempt {attempt}/{max_attempt}: {type(conn_error).__name__}. "
                    f"Retrying in {wait_time} seconds..."
                )
                time.sleep(wait_time)
                return self._do(
                    method,
                    uri,
                    params,
                    body,
                    raw,
                    attempt,
                    max_attempt,
                    wait_before_retry
                )
            else:
                logger.error(
                    f"Connection failed after {max_attempt} attempts. Error: {conn_error}"
                )
                raise

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
            if resp.status_code == 429:  # Rate-limiting response
                attempt += 1
                if attempt <= max_attempt:  # Retry up to 3 times
                    logger.info(f"Rate limit hit. Retrying attempt {attempt} after a delay {wait_before_retry} seconds...")
                    time.sleep(wait_before_retry)
                    return self._do(
                        method,
                        uri,
                        params,
                        body,
                        raw,
                        attempt,
                        max_attempt,
                        wait_before_retry
                    )
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

    def _patch(self, uri_path: str, body: Dict[str, Any]) -> CCVShopResult:
        """
        Internal helper to perform PATCH requests.

        Args:
            uri_path: Relative URI path to append to base URL.
            body: body Data to send

        Returns:
            requests.Response: The HTTP response object.
        """
        return self._do(
            method="PATCH",
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
