import os
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
from planner.graph import app_graph
from memory.store import MemoryStore
from tools.location import format_location_label, normalize_location

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory_store = MemoryStore()
search_executor = ThreadPoolExecutor(max_workers=4)
jobs: Dict[str, Dict[str, Any]] = {}
jobs_lock = Lock()

class SearchRequest(BaseModel):
    query: str
    memory: Dict[str, Any]

class LocationResolveRequest(BaseModel):
    location: Dict[str, Any]

class ProfileUpdateRequest(BaseModel):
    profile: Dict[str, Any]

def _base_steps() -> List[Dict[str, Any]]:
    return [
        {"id": "1", "label": "Decomposing query", "status": "pending"},
        {"id": "2", "label": "Searching Blinkit", "status": "pending"},
        {"id": "3", "label": "Searching Zepto", "status": "pending"},
        {"id": "4", "label": "Searching Instamart", "status": "pending"},
        {"id": "5", "label": "Searching BigBasket Now", "status": "pending"},
        {"id": "6", "label": "Searching Flipkart Minutes", "status": "pending"},
        {"id": "7", "label": "Searching Amazon Fresh", "status": "pending"},
        {"id": "8", "label": "Applying Coupons", "status": "pending"},
        {"id": "9", "label": "Optimizing Delivery Fees", "status": "pending"},
        {"id": "10", "label": "Generating Recommendation", "status": "pending"},
    ]


def _progress_from_steps(job: Dict[str, Any]) -> Dict[str, Any]:
    steps = job.get("steps", [])
    total = len(steps) or 1
    completed = len([step for step in steps if step.get("status") in ["completed", "failed"]])
    running_steps = [step for step in steps if step.get("status") == "running"]
    search_steps = [step for step in steps if step.get("label", "").startswith("Searching ")]
    completed_search_steps = [
        step for step in search_steps
        if step.get("status") in ["completed", "failed"]
    ]
    elapsed = max(0, time.time() - job.get("started_at", time.time()))
    eta = None
    if completed_search_steps and completed < total:
        eta = max(0, (elapsed / len(completed_search_steps)) * (len(search_steps) - len(completed_search_steps)))

    pending = next((step for step in steps if step.get("status") == "pending"), None)
    if job.get("status") == "complete":
        percent = 100
        phase = "Search complete"
    elif running_steps:
        percent = min(99, ((completed + (len(running_steps) * 0.5)) / total) * 100)
        if len(running_steps) > 1 and all(step.get("label", "").startswith("Searching ") for step in running_steps):
            phase = f"Checking {len(running_steps)} stores in parallel"
        else:
            phase = running_steps[0].get("label", "Checking stores")
    else:
        percent = min(99, (completed / total) * 100)
        phase = pending.get("label", "Starting search") if pending else "Finalizing"

    return {
        "elapsedSeconds": round(elapsed),
        "etaSeconds": round(eta) if eta is not None else None,
        "progressPercent": round(percent),
        "phaseLabel": phase,
        "completedSteps": completed,
        "totalSteps": total,
    }


def _build_search_response(final_state: Dict[str, Any], resolved_location: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "steps": final_state.get("steps", []),
        "recommendation": final_state.get("recommendation", {}),
        "comparisons": final_state.get("results", []),
        "reasoning": final_state.get("reasoning", []),
        "brandOptions": final_state.get("brand_options", []),
        "brandStrategy": final_state.get("brand_strategy", {}),
        "location": resolved_location,
    }


def _run_search(payload: SearchRequest, job_id: str | None = None) -> Dict[str, Any]:
    resolved_location = normalize_location(payload.memory.get("location"))
    if not resolved_location.get("label"):
        resolved_location["label"] = format_location_label(resolved_location)
    memory = {**payload.memory, "location": resolved_location}

    def progress_callback(update: Dict[str, Any]) -> None:
        if not job_id:
            return
        with jobs_lock:
            job = jobs.get(job_id)
            if not job:
                return
            job["steps"] = update.get("steps", job.get("steps", []))
            job["partialResults"] = update.get("results", job.get("partialResults", []))
            job["updated_at"] = time.time()
            job["progress"] = _progress_from_steps(job)

    initial_state = {
        "query": payload.query,
        "user_profile": memory,
        "selected_tools": [],
        "results": [],
        "recommendation": {},
        "reasoning": [],
        "steps": [],
        "brand_options": [],
        "brand_strategy": {},
        "progress_callback": progress_callback,
    }

    final_state = app_graph.invoke(initial_state)
    return _build_search_response(final_state, resolved_location)


def _run_job(job_id: str, payload: SearchRequest) -> None:
    try:
        result = _run_search(payload, job_id)
        with jobs_lock:
            job = jobs[job_id]
            job["status"] = "complete"
            job["result"] = result
            job["steps"] = result.get("steps", job.get("steps", []))
            job["updated_at"] = time.time()
            job["progress"] = _progress_from_steps(job)
    except Exception as exc:
        with jobs_lock:
            job = jobs[job_id]
            job["status"] = "failed"
            job["error"] = str(exc)
            job["updated_at"] = time.time()
            job["progress"] = _progress_from_steps(job)


@app.post("/api/search")
def run_search(payload: SearchRequest):
    try:
        return _run_search(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search/start")
def start_search(payload: SearchRequest):
    job_id = str(uuid.uuid4())
    now = time.time()
    with jobs_lock:
        jobs[job_id] = {
            "id": job_id,
            "status": "running",
            "query": payload.query,
            "steps": _base_steps(),
            "partialResults": [],
            "result": None,
            "error": None,
            "started_at": now,
            "updated_at": now,
        }
        jobs[job_id]["progress"] = _progress_from_steps(jobs[job_id])

    search_executor.submit(_run_job, job_id, payload)
    return {"jobId": job_id}


@app.get("/api/search/status/{job_id}")
def get_search_status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Search job not found")
        job["progress"] = _progress_from_steps(job)
        return {
            "id": job["id"],
            "status": job["status"],
            "query": job["query"],
            "steps": job["steps"],
            "partialResults": job.get("partialResults", []),
            "progress": job["progress"],
            "result": job.get("result"),
            "error": job.get("error"),
        }

@app.post("/api/location/resolve")
def resolve_user_location(payload: LocationResolveRequest):
    resolved_location = normalize_location(payload.location)
    if not resolved_location.get("label"):
        resolved_location["label"] = format_location_label(resolved_location)
    return resolved_location

@app.get("/api/profile")
async def get_profile():
    return memory_store.get_profile()

@app.post("/api/profile")
async def update_profile(payload: ProfileUpdateRequest):
    return memory_store.update_profile(payload.profile)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
