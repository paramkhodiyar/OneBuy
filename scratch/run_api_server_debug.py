import uvicorn
import requests
import threading
import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
from planner.graph import app_graph

app = FastAPI()

class SearchRequest(BaseModel):
    query: str
    memory: Dict[str, Any]

@app.post("/api/search")
def run_search(payload: SearchRequest):
    initial_state = {
        "query": payload.query,
        "user_profile": payload.memory,
        "selected_tools": [],
        "results": [],
        "recommendation": {},
        "reasoning": [],
        "steps": []
    }
    try:
        final_state = app_graph.invoke(initial_state)
        return final_state
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(2)
    
    url = "http://127.0.0.1:8080/api/search"
    payload = {
        "query": "bread",
        "memory": {
            "location": "Bangalore"
        }
    }
    
    print("Testing local debug server...")
    try:
        res = requests.post(url, json=payload, timeout=50)
        print("Status:", res.status_code)
        print("Response:", res.text[:1000])
    except Exception as e:
        print("Request failed:", e)
