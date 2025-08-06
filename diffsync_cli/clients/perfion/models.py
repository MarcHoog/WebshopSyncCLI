from typing import List


class PerfionResult:

    def __init__(self, status_code: int, data: List):
        self.status_code = status_code
        self.data = data
