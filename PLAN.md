# MiniServe — Project Plan

## Overview

**MiniServe** v0 is a minimal distributed image classification inference pipeline built for CPU-based asynchronous processing.

The system decouples request handling from model execution using a queue-based architecture, enabling horizontal worker scaling and non-blocking inference.

The goal is to ship a demoable, production-style service within one week.

---

## Objectives

* Build an async inference API
* Use Redis Streams for job queuing
* Run CPU-based image classification
* Support multiple worker replicas
* Deploy with Docker Compose
* Host a live demo
* Keep architecture clean and extensible

---

## System Architecture

### Components

1. **API Service (FastAPI)**

   * Accepts image uploads
   * Pushes jobs to Redis Stream
   * Returns job ID
   * Provides result polling endpoint

2. **Redis**

   * Job queue (Streams)
   * Result storage (Hash per job)

3. **Worker Service**

   * Consumes jobs from stream
   * Loads model at startup
   * Performs inference
   * Stores prediction result

4. **Frontend (Optional Minimal UI)**

   * Upload image
   * Poll result
   * Display prediction + latency

---

## High-Level Flow

1. Client uploads image to `/submit`
2. API:

   * Generates `job_id`
   * Pushes job to Redis Stream
   * Returns `job_id`
3. Worker:

   * Consumes job
   * Runs inference
   * Stores result in Redis
4. Client polls `/result/{job_id}`
5. API returns prediction when complete

---

## Tech Stack

* Python 3.10+
* FastAPI
* Redis (Streams)
* Torch + torchvision (CPU)
* Pillow (image handling)
* Docker
* Docker Compose
* AWS EC2 (deployment)

---

## Model Selection

Initial version:

* Pretrained ResNet (torchvision)
* CPU inference only
* Single image per job

Future versions may support:

* Batching
* Multiple models
* GPU workers
* Model routing

---

## Week Execution Plan

### Day 1 – Model Prototype

* Load pretrained ResNet
* Run inference locally
* Validate image preprocessing
* Benchmark CPU latency

Deliverable:

* Standalone inference script

---

### Day 2 – API Layer (Sync Version)

* Build `/predict` endpoint
* Accept image file
* Return prediction JSON

Deliverable:

* Working synchronous API

---

### Day 3 – Introduce Redis Queue

* Replace direct inference call
* Push job into Redis Stream
* Return job_id

Deliverable:

* Async submission endpoint

---

### Day 4 – Worker Service

* Create worker process
* Consume from Redis Stream
* Load model once at startup
* Store results in Redis Hash

Deliverable:

* End-to-end async flow

---

### Day 5 – Scaling + Metrics

* Run multiple worker replicas
* Load test with multiple requests
* Log:

  * Processing time
  * Queue depth
  * Worker ID handling each job

Deliverable:

* Demonstrate horizontal scaling

---

### Day 6 – Minimal Frontend

* Basic HTML page
* Upload image
* Poll job status
* Display prediction + confidence

Deliverable:

* Demo-ready UI

---

### Day 7 – Deployment

* Dockerize API + Worker
* Configure docker-compose
* Deploy to EC2
* Expose public endpoint

Deliverable:

* Live demo link

---

## Directory Structure

```
MiniServe/
│
├── api/
│   ├── main.py
│   └── requirements.txt
│
├── worker/
│   ├── worker.py
│   └── requirements.txt
│
├── frontend/
│   └── index.html
│
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.worker
└── plan.md
```

---

## Core Engineering Principles

* Decouple API from compute
* Load model once per worker
* Avoid blocking request threads
* Make workers stateless
* Keep infrastructure minimal
* Ship fast, refine later

---

## Success Criteria

By end of week:

* Image upload returns job_id
* Worker processes asynchronously
* Multiple workers can run simultaneously
* Results persist in Redis
* System deployable on single EC2 instance
* Public demo link available

---

## Future Roadmap (Post-MVP)

* Batch processing
* Multiple model support
* GPU worker pool
* Metrics endpoint (Prometheus style)
* Autoscaling
* Model registry
* Auth layer
