import traceback
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.blinkit import BlinkitTool
from tools.zepto import ZeptoTool

def run_tests():
    print("Testing Blinkit for Bangalore...")
    try:
        b = BlinkitTool()
        res = b.search("bread", "Bangalore")
        print("Blinkit count:", len(res))
        for r in res[:2]:
            print("  -", r.to_dict())
    except Exception as e:
        traceback.print_exc()
        
    print("\nTesting Zepto for Bangalore...")
    try:
        z = ZeptoTool()
        res = z.search("bread", "Bangalore")
        print("Zepto count:", len(res))
        for r in res[:2]:
            print("  -", r.to_dict())
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_tests()
