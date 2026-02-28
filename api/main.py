"""
MiniServe API — Day 2: synchronous /predict endpoint.
Accepts image upload, runs inference, returns prediction JSON.
"""

import io
import sys
from pathlib import Path

# Ensure worker package is importable (when run from api/ or repo root)
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

from worker.model import load_model, preprocess_image, predict

app = FastAPI(
    title="MiniServe",
    description="Image classification inference API",
    version="0.2.0",
)

DEVICE = "cpu"


@app.on_event("startup")
def startup():
    app.state.model = load_model(DEVICE)


def get_model():
    return app.state.model


@app.get("/")
def root():
    return {"service": "MiniServe", "endpoints": ["/predict", "/health"]}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict_endpoint(file: UploadFile = File(...)):
    """
    Accept an image file, run ResNet inference, return top-1 prediction.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Expected an image file")

    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e!s}")

    model = get_model()
    tensor = preprocess_image(img).to(DEVICE)
    result = predict(model, tensor, DEVICE)
    return JSONResponse(content=result)
