import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import run_search, SearchRequest

async def main():
    print("Calling run_search handler directly...")
    req = SearchRequest(
        query="bread",
        memory={
            "location": "Bangalore",
            "preferredStore": "Blinkit",
            "preferredPayment": "UPI",
            "preferredDeliveryTime": "Immediate",
            "isPrimeMember": True,
            "ordersEvening": True
        }
    )
    res = await run_search(req)
    print("Result:")
    print("Recommendation:", res.get("recommendation"))
    print("Comparisons count:", len(res.get("comparisons", [])))
    for c in res.get("comparisons", [])[:3]:
        print("  -", c)

if __name__ == "__main__":
    asyncio.run(main())
