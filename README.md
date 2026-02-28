# MiniServe

**MiniServe** v0 is a minimal distributed image classification inference pipeline built for CPU-based asynchronous processing.

The system decouples request handling from model execution using a queue-based architecture (Redis Streams), enabling horizontal worker scaling and non-blocking inference.

---

## Features

- **Async inference API** - Submit images, get a job ID, poll for results
- **Redis Streams** - Job queue and result storage
- **CPU-based ResNet** - Pretrained ImageNet model via torchvision (CPU-only for v0)
- **Dockerized** - API, worker, and inference prototype run in containers
- **Extensible** - Clean layout for adding workers, batching, or GPU later

---

## Quick Start

### Prerequisites

- **Local:** Python 3.10+, pip
- **Docker:** Docker and Docker Compose (optional)

### Standalone inference

Run the model locally or in Docker: load ResNet, run inference, and optionally benchmark CPU latency.

**Using Docker (recommended):**

```bash
# Build and run CPU benchmark (20 iterations)
docker compose run --rm inference

# Benchmark with more iterations
docker compose run --rm inference --benchmark 50

# Run inference on an image (mount a folder with images)
docker compose run --rm -v ./images:/data inference /data/photo.jpg
```

**Local (no Docker):**

```bash
cd worker
pip install -r requirements.txt

# Single inference (dummy image if no path given)
python run_inference.py
python run_inference.py path/to/image.jpg

# CPU latency benchmark
python run_inference.py --benchmark 20
```

### Async API (Day 3)

Run the API and Redis; submit an image to get a `job_id`, then poll `/result/{job_id}` (worker writes results in Day 4).

**Using Docker:**

```bash
docker compose up api redis
# API at http://localhost:8000, Redis at localhost:6379
# Docs: http://localhost:8000/docs
```

**Local (Redis required):**

```bash
pip install -r api/requirements.txt
# Start Redis (e.g. docker run -p 6379:6379 redis:7-alpine)
REDIS_URL=redis://localhost:6379/0 uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Example flow:**

```bash
# Submit image → get job_id
curl -X POST http://localhost:8000/submit -F "file=@image.jpg"
# → {"job_id": "550e8400-e29b-41d4-a716-446655440000"}

# Poll for result (returns {"status": "pending"} until worker completes it)
curl http://localhost:8000/result/550e8400-e29b-41d4-a716-446655440000
```

---

## Project Structure

```
MiniServe/
├── api/                 # FastAPI service (submit job, poll result)
│   ├── main.py
│   ├── redis_client.py  # Stream + result keys
│   └── requirements.txt
├── worker/              # Inference worker + model
│   ├── model.py         # ResNet loader, preprocessing, predict()
│   ├── run_inference.py # Day 1 standalone script + benchmark
│   ├── worker.py        # Stream consumer (Day 4+)
│   ├── requirements.txt
│   └── imagenet_labels.txt
├── frontend/            # Optional minimal UI
│   └── index.html
├── docker-compose.yml
├── DockerFile.api
├── DockerFile.worker
├── tests/               # Pytest suite (model + API)
├── requirements-dev.txt
├── pytest.ini
├── PLAN.md              # Week plan and architecture
└── README.md
```

---

## Architecture (target)

1. **Client** uploads image to API `/submit` -> receives `job_id`
2. **API** pushes job to Redis Stream, returns `job_id`
3. **Worker(s)** consume from stream, run ResNet inference, write result to Redis
4. **Client** polls `/result/{job_id}` until complete → gets prediction + confidence

See [PLAN.md](PLAN.md) for the full week plan, tech stack, and roadmap.

---

## Tests

From repo root:

```bash
pip install -r requirements-dev.txt
pytest
```

- **tests/test_model.py** — Model: `preprocess_image` shape, `predict` output, `load_model`, `load_and_predict`.
- **tests/test_api.py** — API: `GET /`, `GET /health`, `POST /submit` (image → job_id), `GET /result/{job_id}` (pending).

First run loads ResNet once (slower); later tests reuse it.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| API | FastAPI, Python 3.10+ |
| Queue & results | Redis (Streams, Hashes) |
| Model | PyTorch, torchvision (ResNet18, CPU) |
| Images | Pillow |
| Deploy | Docker, Docker Compose, AWS EC2 |

---

## License

MIT
