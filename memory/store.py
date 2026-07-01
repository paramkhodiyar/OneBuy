import os
import json
from typing import Dict, Any

class MemoryStore:
    def __init__(self, filepath: str = "memory_store.json"):
        self.filepath = filepath
        self._initialize_store()

    def _initialize_store(self):
        if not os.path.exists(self.filepath):
            default_data = {
                "user_default": {
                    "preferredStore": "Blinkit",
                    "preferredPayment": "UPI",
                    "isPrime": True,
                    "location": "Bangalore, IN",
                    "ordersEvening": True,
                    "preferredDeliveryTime": "Immediate"
                }
            }
            with open(self.filepath, "w") as f:
                json.dump(default_data, f, indent=2)

    def get_profile(self, user_id: str = "user_default") -> Dict[str, Any]:
        try:
            with open(self.filepath, "r") as f:
                data = json.load(f)
                return data.get(user_id, {})
        except Exception:
            return {}

    def update_profile(self, profile_data: Dict[str, Any], user_id: str = "user_default") -> Dict[str, Any]:
        try:
            with open(self.filepath, "r") as f:
                data = json.load(f)
            data[user_id] = profile_data
            with open(self.filepath, "w") as f:
                json.dump(data, f, indent=2)
            return profile_data
        except Exception:
            return profile_data
