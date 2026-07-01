import requests
import json

def test_api():
    url = "http://localhost:8000/api/search"
    payload = {
        "query": "bread",
        "memory": {
            "location": "Bangalore",
            "preferredStore": "Blinkit",
            "preferredPayment": "UPI",
            "preferredDeliveryTime": "Immediate",
            "isPrimeMember": True,
            "ordersEvening": True
        }
    }
    
    print("Sending POST request to FastAPI search endpoint...")
    try:
        res = requests.post(url, json=payload, timeout=45)
        print("Status Code:", res.status_code)
        if res.status_code == 200:
            data = res.json()
            print("Recommendation:")
            print("  - Store:", data.get("recommendation", {}).get("storeName"))
            print("  - Price:", data.get("recommendation", {}).get("price"))
            print("  - Delivery:", data.get("recommendation", {}).get("deliveryTime"))
            print("\nComparisons (first 5 rows):")
            for row in data.get("comparisons", [])[:5]:
                print("  -", row)
            print("\nReasoning:")
            for reason in data.get("reasoning", []):
                print("  -", reason)
        else:
            print("Error Response:", res.text)
    except Exception as e:
        print("HTTP request failed:", e)

if __name__ == "__main__":
    test_api()
