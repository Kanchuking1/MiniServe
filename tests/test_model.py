"""
Unit tests for worker.model: load_model, preprocess_image, predict, load_and_predict.
"""

import tempfile
from pathlib import Path

import torch
from PIL import Image

from worker.model import (
    load_model,
    load_and_predict,
    preprocess_image,
    predict,
)


class TestPreprocessImage:
    """Tests for preprocess_image."""

    def test_output_shape(self, sample_image):
        tensor = preprocess_image(sample_image)
        assert tensor.shape == (1, 3, 224, 224)
        assert isinstance(tensor, torch.Tensor)

    def test_different_input_sizes(self):
        for size in [(100, 100), (300, 400), (224, 224)]:
            img = Image.new("RGB", size, color=(0, 0, 0))
            tensor = preprocess_image(img)
            assert tensor.shape == (1, 3, 224, 224)


class TestPredict:
    """Tests for predict (requires loaded model)."""

    def test_returns_dict_with_expected_keys(self, loaded_model, sample_image):
        tensor = preprocess_image(sample_image).to("cpu")
        result = predict(loaded_model, tensor, "cpu")
        assert isinstance(result, dict)
        assert "class_id" in result
        assert "label" in result
        assert "confidence" in result
        assert isinstance(result["class_id"], int)
        assert 0 <= result["class_id"] <= 999
        assert isinstance(result["label"], str)
        assert isinstance(result["confidence"], (int, float))
        assert 0 <= result["confidence"] <= 1

    def test_confidence_is_float(self, loaded_model, sample_image):
        tensor = preprocess_image(sample_image).to("cpu")
        result = predict(loaded_model, tensor, "cpu")
        assert isinstance(result["confidence"], (int, float))


class TestLoadModel:
    """Tests for load_model."""

    def test_returns_eval_mode(self):
        model = load_model("cpu")
        assert not model.training

    def test_accepts_none_device(self):
        model = load_model(None)
        assert model is not None


class TestLoadAndPredict:
    """Tests for load_and_predict (file path)."""

    def test_load_and_predict_from_path(self, loaded_model, sample_image):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            sample_image.save(f.name)
            try:
                result = load_and_predict(loaded_model, f.name, "cpu")
                assert "class_id" in result
                assert "label" in result
                assert "confidence" in result
            finally:
                Path(f.name).unlink(missing_ok=True)
