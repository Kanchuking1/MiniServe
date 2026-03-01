"""
MiniServe API — Day 3: async submission via Redis Stream.
/submit: accept image, push job to stream, return job_id.
/result/{job_id}: return result when ready (worker writes in Day 4).
"""

import base64
import io
import sys
import uuid
from pathlib import Path

# Ensure worker package is importable when run from api/ or repo root
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from api.redis_client import get_queue_depth, get_result, push_job

app = FastAPI(
    title="MiniServe",
    description="Image classification inference API (async job queue)",
    version="0.3.0",
)


@app.get("/")
def root():
    return {
        "service": "MiniServe",
        "endpoints": ["/submit", "/result/{job_id}", "/health", "/queue"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/queue")
def queue():
    """Return current job stream length (queue depth). For scaling and load tests."""
    try:
        depth = get_queue_depth()
        return JSONResponse(content={"queue_depth": depth})
    except Exception as e:
        return JSONResponse(content={"queue_depth": -1, "error": str(e)}, status_code=503)


@app.post("/submit")
async def submit(file: UploadFile = File(...)):
    """
    Accept an image file, push job to Redis Stream, return job_id.
    Client should poll /result/{job_id} for the prediction.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Expected an image file")

    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e!s}")

    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")

    job_id = str(uuid.uuid4())
    image_b64 = base64.standard_b64encode(contents).decode("ascii")
    print(f"job_id: {job_id}")
    try:
        push_job(job_id, image_b64)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Queue unavailable: {e!s}")

    return JSONResponse(content={"job_id": job_id})


@app.get("/result/{job_id}")
def result(job_id: str):
    """
    Return job result if ready. Worker writes to Redis when inference is done.
    Returns {"status": "pending"} until then.
    """
    data = get_result(job_id)
    if data is None:
        return JSONResponse(content={"status": "pending"})
    # Worker stores: status, class_id, label, confidence (and optionally error)
    return JSONResponse(content=data)
