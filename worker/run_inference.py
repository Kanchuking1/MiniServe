#!/usr/bin/env python3
"""
Day 1 standalone inference script for MiniServe.
Loads pretrained ResNet, validates preprocessing, runs inference, and benchmarks CPU latency.
Usage:
  python run_inference.py [IMAGE_PATH]     Run once on image (or create random tensor if no path)
  python run_inference.py --benchmark [N]  Run N inference iterations and report latency (default 20)
"""

import argparse
import sys
import time
from pathlib import Path

import torch

# Add worker dir for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from model import load_model, preprocess_image, predict, load_and_predict
from PIL import Image


def create_dummy_image() -> Image.Image:
    """Create a 224x224 RGB image for validation (no file I/O)."""
    return Image.new("RGB", (224, 224), color=(120, 80, 160))


def run_single_inference(image_path: str | None) -> None:
    """Load image (or use dummy), run inference once, print result."""
    device = "cpu"
    print("Loading ResNet18 (ImageNet pretrained)...")
    model = load_model(device)

    if image_path and Path(image_path).exists():
        print(f"Running inference on: {image_path}")
        result = load_and_predict(model, image_path, device)
    else:
        print("No valid image path; using dummy image for preprocessing validation.")
        img = create_dummy_image()
        tensor = preprocess_image(img).to(device)
        result = predict(model, tensor, device)

    print(f"  class_id: {result['class_id']}")
    print(f"  label:    {result['label']}")
    print(f"  confidence: {result['confidence']}")


def run_benchmark(n_iters: int = 20) -> None:
    """Run N inference iterations on a fixed tensor and report CPU latency (no I/O)."""
    device = "cpu"
    print("Loading ResNet18 (ImageNet pretrained)...")
    model = load_model(device)
    img = create_dummy_image()
    tensor = preprocess_image(img).to(device)

    print(f"Running {n_iters} inference iterations on CPU...")
    times_ms: list[float] = []
    for _ in range(n_iters):
        start = time.perf_counter()
        predict(model, tensor, device)
        elapsed_ms = (time.perf_counter() - start) * 1000
        times_ms.append(elapsed_ms)

    mean_ms = sum(times_ms) / len(times_ms)
    variance = sum((t - mean_ms) ** 2 for t in times_ms) / len(times_ms)
    std_ms = variance ** 0.5
    print(f"  Mean latency: {mean_ms:.2f} ms")
    print(f"  Std latency:  {std_ms:.2f} ms")
    print(f"  Min / Max:    {min(times_ms):.2f} / {max(times_ms):.2f} ms")


def main() -> None:
    parser = argparse.ArgumentParser(description="MiniServe Day 1: standalone ResNet inference")
    parser.add_argument(
        "image_path",
        nargs="?",
        default=None,
        help="Path to image file (optional; uses dummy image if omitted)",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run benchmark mode: N iterations and report CPU latency",
    )
    parser.add_argument(
        "-n",
        "--iters",
        type=int,
        default=20,
        metavar="N",
        help="Number of iterations for benchmark (default: 20)",
    )
    args = parser.parse_args()

    if args.benchmark:
        run_benchmark(args.iters)
    else:
        run_single_inference(args.image_path)


if __name__ == "__main__":
    main()
