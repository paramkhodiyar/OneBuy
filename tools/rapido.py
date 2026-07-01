from typing import List
from .base import CommerceTool, CommerceItem

class RapidoTool(CommerceTool):
    def search(self, query: str, location: str = "Delhi") -> List[CommerceItem]:
        query_lower = query.lower()
        if "cab" in query_lower or "airport" in query_lower or "ride" in query_lower:
            return [CommerceItem("Rapido", 780.0, "8 mins", "RAP50", 730.0)]
        return []
