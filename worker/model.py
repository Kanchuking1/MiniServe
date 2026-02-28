"""
ResNet-based image classification model for MiniServe.
Uses pretrained torchvision ResNet with ImageNet preprocessing (CPU only).
"""

from pathlib import Path
from typing import Any

import torch
from torch import nn
from torchvision import models, transforms
from PIL import Image


# ImageNet normalization (used by pretrained torchvision models)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Standard preprocessing pipeline for inference
PREPROCESS = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])


def load_model(device: str | None = None) -> nn.Module:
    """Load pretrained ResNet18 and set to eval mode. CPU if device is None or 'cpu'."""
    if device is None:
        device = "cpu"
    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    model.to(device)
    model.eval()
    return model


def preprocess_image(image: Image.Image) -> torch.Tensor:
    """Convert PIL image to normalized batch tensor (1, 3, 224, 224)."""
    return PREPROCESS(image).unsqueeze(0)


def predict(model: nn.Module, image_tensor: torch.Tensor, device: str = "cpu") -> dict[str, Any]:
    """
    Run inference and return top-1 prediction with confidence.
    image_tensor: (1, 3, 224, 224) already on correct device.
    """
    model.eval()
    with torch.no_grad():
        logits = model(image_tensor)
        probs = torch.softmax(logits, dim=1)
        top_prob, top_idx = probs[0].max(0)
        top_idx_int = top_idx.item()
    label = _imagenet_label(top_idx_int)
    return {
        "class_id": top_idx_int,
        "label": label,
        "confidence": round(top_prob.item(), 4),
    }


def _imagenet_label(class_id: int) -> str:
    """Map ImageNet class index to human-readable label."""
    labels_path = Path(__file__).parent / "imagenet_labels.txt"
    if labels_path.exists():
        with open(labels_path, encoding="utf-8") as f:
            lines = f.readlines()
        if 0 <= class_id < len(lines):
            return lines[class_id].strip()
    return f"class_{class_id}"


def load_and_predict(model: nn.Module, image_path: str | Path, device: str = "cpu") -> dict[str, Any]:
    """Load image from path, preprocess, run inference. For standalone use."""
    img = Image.open(image_path).convert("RGB")
    tensor = preprocess_image(img).to(device)
    return predict(model, tensor, device)
