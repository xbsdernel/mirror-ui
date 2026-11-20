"""
Unit tests for Stage 1 Preprocessing logic.
"""

import os
import pytest
from PIL import Image
from src.vision.stage1_preprocessing import (
    resize_image_capped,
    detect_modality,
    clean_sketch_image,
    preprocess_image,
)


def test_resize_image_capped_no_resize():
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    resized, ratio = resize_image_capped(img, max_dim=1280)
    assert resized.size == (800, 600)
    assert ratio == 1.0


def test_resize_image_capped_landscape():
    img = Image.new("RGB", (2560, 1440), color=(255, 255, 255))
    resized, ratio = resize_image_capped(img, max_dim=1280)
    assert resized.size == (1280, 720)
    assert ratio == 0.5


def test_resize_image_capped_portrait():
    img = Image.new("RGB", (1000, 2000), color=(255, 255, 255))
    resized, ratio = resize_image_capped(img, max_dim=1280)
    assert resized.size == (640, 1280)
    assert ratio == 0.64


def test_clean_sketch_image_runs():
    img = Image.new("RGB", (200, 200), color=(200, 200, 200))
    cleaned = clean_sketch_image(img)
    assert cleaned.size == (200, 200)
    assert cleaned.mode == "RGB"


def test_detect_modality_screenshot_uniform():
    # Large uniform background -> screenshot
    img = Image.new("RGB", (640, 480), color=(240, 240, 240))
    modality = detect_modality(img)
    assert modality == "screenshot"


def test_preprocess_image_file_not_found():
    with pytest.raises(FileNotFoundError):
        preprocess_image("non_existent_file_path.png")


def test_preprocess_image_pipeline(tmp_path):
    test_img = Image.new("RGB", (1600, 1200), color=(245, 245, 245))
    img_path = str(tmp_path / "test_input.png")
    test_img.save(img_path)

    out_dir = str(tmp_path / "normalized_out")
    result = preprocess_image(input_path=img_path, output_dir=out_dir, max_dim=1280)

    assert os.path.exists(result.normalized_image_path)
    assert result.original_size == (1600, 1200)
    assert result.normalized_size == (1280, 960)
    assert result.resize_ratio == 0.8
