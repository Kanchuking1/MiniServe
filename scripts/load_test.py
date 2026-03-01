#!/usr/bin/env python3
"""
Day 5 load test: submit N jobs to the API, optionally wait for results, report queue depth and timing.
Usage:
  python scripts/load_test.py [--api http://localhost:8000] [--image path/to/image.jpg] [--n 20] [--wait]
"""

import argparse
import statistics
import sys
import time
from pathlib import Path

# Add repo root for optional imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import requests
except ImportError:
    print("Install requests: pip install requests", file=sys.stderr)
    sys.exit(1)


def submit_job(api_base: str, image_path: Path) -> str | None:
    """Submit one image; return job_id or None on error."""
    url = f"{api_base.rstrip('/')}/submit"
    with open(image_path, "rb") as f:
        r = requests.post(url, files={"file": (image_path.name, f, "image/png")}, timeout=30)
    if r.status_code != 200:
        return None
    return r.json().get("job_id")


def get_result(api_base: str, job_id: str) -> dict | None:
    """Get result for job_id; returns dict with at least 'status'."""
    url = f"{api_base.rstrip('/')}/result/{job_id}"
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return None
    return r.json()


def get_queue_depth(api_base: str) -> int:
    """Return current queue depth from GET /queue."""
    url = f"{api_base.rstrip('/')}/queue"
    r = requests.get(url, timeout=5)
    if r.status_code != 200:
        return -1
    return r.json().get("queue_depth", -1)


def main() -> None:
    parser = argparse.ArgumentParser(description="MiniServe load test: submit N jobs, report stats")
    parser.add_argument("--api", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--image", type=Path, required=True, help="Path to image file to submit")
    parser.add_argument("--n", type=int, default=20, help="Number of jobs to submit")
    parser.add_argument("--wait", action="store_true", help="Wait for all results and report latency")
    parser.add_argument("--poll-interval", type=float, default=0.5, help="Seconds between result polls when --wait")
    args = parser.parse_args()

    if not args.image.exists():
        print(f"Error: image not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    api = args.api
    n = args.n
    print(f"Submitting {n} jobs from {args.image} to {api} ...")
    job_ids: list[str] = []
    submit_times: list[float] = []  # per-job submit time for accurate latency
    for _ in range(n):
        t_submit = time.perf_counter()
        jid = submit_job(api, args.image)
        if jid:
            job_ids.append(jid)
            submit_times.append(t_submit)
        else:
            print("  submit failed for one job", file=sys.stderr)
    submit_elapsed = (time.perf_counter() - submit_times[0]) if submit_times else 0
    print(f"Submitted {len(job_ids)} jobs in {submit_elapsed:.2f}s ({len(job_ids) / submit_elapsed:.1f} req/s)")
    depth = get_queue_depth(api)
    print(f"Stream length after submit: {depth} (stream is append-only; workers read but do not remove)")

    if not args.wait or not job_ids:
        return

    print("Waiting for results (polling)...")
    latencies: list[float] = []
    for jid, submitted_at in zip(job_ids, submit_times):
        while True:
            res = get_result(api, jid)
            if res and res.get("status") == "completed":
                latencies.append((time.perf_counter() - submitted_at) * 1000)
                break
            if res and res.get("status") == "failed":
                break
            time.sleep(args.poll_interval)
    total_wait = time.perf_counter() - submit_times[0] if submit_times else 0
    print(f"All done in {total_wait:.2f}s")
    if latencies:
        print(f"Latency (submit→completed): min={min(latencies):.0f}ms max={max(latencies):.0f}ms mean={statistics.mean(latencies):.0f}ms")
    print(f"Stream length at end: {get_queue_depth(api)}")


if __name__ == "__main__":
    main()
