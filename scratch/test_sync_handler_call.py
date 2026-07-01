import sys
import os
import threading

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import run_search, SearchRequest

def run_in_thread():
    req = SearchRequest(
        query="bread",
        memory={
            "location": "Bangalore"
        }
    )
    res = run_search(req)
    print("Sub-thread Result:")
    print("Recommendation:", res.get("recommendation"))
    print("Comparisons count:", len(res.get("comparisons", [])))
    for c in res.get("comparisons", []):
        print("  -", c)

if __name__ == "__main__":
    t = threading.Thread(target=run_in_thread)
    t.start()
    t.join()
