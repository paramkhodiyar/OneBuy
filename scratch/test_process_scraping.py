import sys
import os
import traceback
from concurrent.futures import ProcessPoolExecutor

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def run_search_wrapper(query, location):
    try:
        from dotenv import load_dotenv
        load_dotenv()
        from tools.blinkit import BlinkitTool
        tool = BlinkitTool()
        res = tool.search(query, location)
        return {"success": True, "results": [r.to_dict() for r in res]}
    except Exception as e:
        err_msg = "".join(traceback.format_exception(*sys.exc_info()))
        return {"success": False, "error": err_msg}

def main():
    print("Running Blinkit search in a separate process...")
    with ProcessPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_search_wrapper, "bread", "Bangalore")
        try:
            res = future.result(timeout=45)
            if res["success"]:
                print("Results count:", len(res["results"]))
                for r in res["results"][:3]:
                    print("  -", r)
            else:
                print("Subprocess failed with error:")
                print(res["error"])
        except Exception as e:
            print("Future call failed:")
            traceback.print_exc()

if __name__ == "__main__":
    main()
