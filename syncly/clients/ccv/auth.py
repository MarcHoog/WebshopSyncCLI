import requests
import requests.auth
import hmac
import hashlib

from datetime import datetime, timezone


class CCVAuth(requests.auth.AuthBase):
    """
    Authentication class for CCV API using HMAC SHA512 hash.

    This class generates the required headers:
    - x-public: Public API key
    - x-date: Current timestamp in ISO 8601 UTC
    - x-hash: HMAC SHA512 hash of the request details

    Attributes:
        base_url (str): Base URL to strip from the request URL.
        public_key (str): Public API key.
        secret_key (str): Secret API key used for HMAC hashing.
    """

    def __init__(self, base_url: str, public_key: str, secret_key: str):
        """
        Initialize CCVAuth with base URL, public key, and secret key.

        Args:
            base_url (str): The base URL of the API.
            public_key (str): The public API key.
            secret_key (str): The secret API key.
        """
        self.base_url = base_url
        self.public_key = public_key
        self.secret_key = secret_key

    def __call__(self, r: requests.PreparedRequest): # type: ignore
        """
        Called by Requests to modify and sign the outgoing request.

        Adds the headers 'x-public', 'x-date', and 'x-hash' for authentication.

        Args:
            r (requests.Request): The request being prepared.

        Returns:
            requests.Request: The modified request with authentication headers.
        """

        if not r.url or not r.method:
            raise ValueError("Cannot authenticate without url or method defined")

        if r.url.startswith(self.base_url):
            uri = r.url[len(self.base_url):]
        else:
            uri = r.url

        data = r.body or ""
        if isinstance(data, bytes):
            data = data.decode("utf-8")

        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', '') + "Z"
        hash_string = f"{self.public_key}|{r.method.upper()}|{uri}|{data}|{timestamp}"
        hash_bytes = hmac.new(self.secret_key.encode(), hash_string.encode(), hashlib.sha512).hexdigest()

        r.headers.update({
            "x-public": self.public_key,
            "x-hash": hash_bytes,
            "x-date": timestamp,
        })
        return r

    def __eq__(self, other):
        """
        Equality check to compare two CCVAuth instances.

        Args:
            other (object): Another object to compare.

        Returns:
            bool: True if both have the same public and secret keys, False otherwise.
        """
        return (
            self.public_key == getattr(other, "public_key", None) and
            self.secret_key == getattr(other, "secret_key", None)
        )

    def __ne__(self, other):
        """
        Inequality check.

        Args:
            other (object): Another object to compare.

        Returns:
            bool: True if instances differ, False otherwise.
        """
        return not self == other
