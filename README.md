# MiniServe

**MiniServe** v0 is a minimal distributed image classification inference pipeline built for CPU-based asynchronous processing.

The system decouples request handling from model execution using a queue-based architecture (Redis Streams), enabling horizontal worker scaling and non-blocking inference.

---

## Features

- **Async inference API** — Submit images, get a job ID, poll for results
- **Redis Streams** — Job queue and result storage
- **CPU-based ResNet** — Pretrained ImageNet model via torchvision (CPU-only for v0)
- **Dockerized** — API, worker, and inference prototype run in containers
- **Extensible** — Clean layout for adding workers, batching, or GPU later

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

### Sync API (Day 2)

Run the FastAPI service with a `/predict` endpoint: upload an image, get back prediction JSON (class_id, label, confidence).

**Using Docker:**

```bash
docker compose up api
# API at http://localhost:8000
# Docs: http://localhost:8000/docs
```

**Local:**

```bash
# From repo root (so worker package is importable)
pip install -r api/requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Example request:**

```bash
curl -X POST http://localhost:8000/predict -F "file=@path/to/image.jpg"
# → {"class_id": 281, "label": "tabby", "confidence": 0.7234}
```

---

## Project Structure

```
MiniServe/
├── api/                 # FastAPI service (submit job, poll result)
│   ├── main.py
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
├── PLAN.md              # Week plan and architecture
└── README.md
```

---

## Architecture (target)

1. **Client** uploads image to API `/submit` → receives `job_id`
2. **API** pushes job to Redis Stream, returns `job_id`
3. **Worker(s)** consume from stream, run ResNet inference, write result to Redis
4. **Client** polls `/result/{job_id}` until complete → gets prediction + confidence

See [PLAN.md](PLAN.md) for the full week plan, tech stack, and roadmap.

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
