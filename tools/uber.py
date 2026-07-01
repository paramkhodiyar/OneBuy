from typing import List
from .base import CommerceTool, CommerceItem

class UberTool(CommerceTool):
    def search(self, query: str, location: str = "Delhi") -> List[CommerceItem]:
        query_lower = query.lower()
        if "cab" in query_lower or "airport" in query_lower or "ride" in query_lower:
            return [CommerceItem("Uber", 850.0, "5 mins", "UBER50", 800.0)]
        return []
