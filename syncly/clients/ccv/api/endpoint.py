from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from syncly.clients.ccv.client import CCVClient

class CCVApiEndpoints:

    def __init__(self, client: 'CCVClient'):
        self.client: 'CCVClient' = client
