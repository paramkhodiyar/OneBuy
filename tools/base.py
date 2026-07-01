from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class CommerceItem:
    def __init__(
        self,
        store: str,
        price: float,
        delivery_time: str,
        coupons: str,
        final_cost: float,
        name: str = "",
        source_url: str = "",
        status: str = "available",
        note: str = "",
        brand: str = "",
        pack_size: str = "",
    ):
        self.store = store
        self.price = price
        self.delivery_time = delivery_time
        self.coupons = coupons
        self.final_cost = final_cost
        self.name = name
        self.source_url = source_url
        self.status = status
        self.note = note
        self.brand = brand
        self.pack_size = pack_size

    def to_dict(self) -> Dict[str, Any]:
        return {
            "store": self.store,
            "name": self.name,
            "brand": self.brand,
            "packSize": self.pack_size,
            "price": self.price,
            "delivery": self.delivery_time,
            "coupons": self.coupons,
            "finalCost": self.final_cost,
            "sourceUrl": self.source_url,
            "status": self.status,
            "note": self.note,
        }

class CommerceTool(ABC):
    @abstractmethod
    def search(self, query: str, location: Optional[Any] = None) -> List[CommerceItem]:
        pass
