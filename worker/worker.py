"""
MiniServe worker — Day 4: consume jobs from Redis Stream, run inference, store result in Redis Hash.
"""

import base64
import io
import logging
import os
import sys
from pathlib import Path

# Repo root on path for optional shared imports; worker runs from /app in Docker
if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import redis
from PIL import Image

from worker.model import load_model, preprocess_image, predict

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
STREAM_KEY = "miniserve:jobs"
RESULT_KEY_PREFIX = "miniserve:result:"
BLOCK_MS = 5000
LOG_FILE = os.environ.get("WORKER_LOG_FILE", "worker.log")

# Logger: file (and optionally stdout). Set up at import so it works with python -m worker.worker
logger = logging.getLogger("miniserve.worker")
logger.setLevel(logging.INFO)
logger.handlers.clear()
_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
# File: ensure directory exists, use line buffering so logs appear immediately
_log_dir = os.path.dirname(LOG_FILE)
if _log_dir:
    os.makedirs(_log_dir, exist_ok=True)
_fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
_fh.setFormatter(_formatter)
logger.addHandler(_fh)


def result_key(job_id: str) -> str:
    return f"{RESULT_KEY_PREFIX}{job_id}"


def get_redis() -> redis.Redis:
    return redis.from_url(REDIS_URL, decode_responses=True)


def process_job(redis_client: redis.Redis, model, job_id: str, image_b64: str, device: str = "cpu") -> None:
    """Decode image, run inference, write result hash. On error write status=failed."""
    try:
        raw = base64.standard_b64decode(image_b64)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e:
        redis_client.hset(result_key(job_id), mapping={"status": "failed", "error": str(e)})
        return
    try:
        tensor = preprocess_image(img).to(device)
        out = predict(model, tensor, device)
        redis_client.hset(
            result_key(job_id),
            mapping={
                "status": "completed",
                "class_id": str(out["class_id"]),
                "label": out["label"],
                "confidence": str(out["confidence"]),
            },
        )
    except Exception as e:
        redis_client.hset(result_key(job_id), mapping={"status": "failed", "error": str(e)})


def main() -> None:
    device = "cpu"
    print("Loading ResNet18...")
    model = load_model(device)
    print("Connecting to Redis...")
    r = get_redis()
    last_id = "0"
    print(f"Consuming from {STREAM_KEY} (block={BLOCK_MS}ms)...")
    while True:
        reply = r.xread(block=BLOCK_MS, streams={STREAM_KEY: last_id})
        if not reply:
            continue
        # reply = [[stream_name, [(entry_id, {field: value}), ...]]]
        for _stream, messages in reply:
            for entry_id, data in messages:
                # Before processing the job, make sure the job is not already in the result hash
                if r.hget(result_key(data.get("job_id")), "status") == "completed":
                    logger.info("Job %s already processed", data.get("job_id"))
                    continue
                last_id = entry_id
                job_id = data.get("job_id")
                image_b64 = data.get("image_b64")
                if not job_id or not image_b64:
                    continue
                logger.info("Processing job_id=%s", job_id)
                process_job(r, model, job_id, image_b64, device)
                logger.info("Done job_id=%s", job_id)


if __name__ == "__main__":
    main()
