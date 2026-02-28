"""
Redis client for MiniServe: job stream and result storage.
Stream: job queue. Result: Hash per job (written by worker).
"""

import os
from typing import Any

import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
STREAM_KEY = "miniserve:jobs"
RESULT_KEY_PREFIX = "miniserve:result:"


def get_redis() -> redis.Redis:
    """Return a Redis connection (decode_responses=True for string values)."""
    return redis.from_url(REDIS_URL, decode_responses=True)


def result_key(job_id: str) -> str:
    return f"{RESULT_KEY_PREFIX}{job_id}"


def push_job(job_id: str, image_b64: str) -> str:
    """
    Push a job to the stream. Returns the stream entry id.
    Fields: job_id, image_b64 (base64-encoded image).
    """
    r = get_redis()
    entry_id = r.xadd(
        STREAM_KEY,
        {"job_id": job_id, "image_b64": image_b64},
        maxlen=10000,
    )
    return entry_id


def get_result(job_id: str) -> dict[str, Any] | None:
    """
    Get result hash for a job. Returns None if not found (pending).
    Hash fields: status, class_id, label, confidence (and optionally error).
    """
    r = get_redis()
    key = result_key(job_id)
    raw = r.hgetall(key)
    return raw if raw else None
