from typing import  Dict, Any, Optional

class CCVShopResult:

    def __init__(self, status_code: int,  data: Optional[Dict[str, Any]]):
        self.status_code = status_code
        self.data = data
