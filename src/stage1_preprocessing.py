"""
Backward-compatibility alias for src.vision.stage1_preprocessing.
"""

from src.vision.stage1_preprocessing import (
    load_pdf_as_image,
    detect_modality,
    clean_sketch_image,
    resize_image_capped,
    preprocess_image,
)

__all__ = [
    "load_pdf_as_image",
    "detect_modality",
    "clean_sketch_image",
    "resize_image_capped",
    "preprocess_image",
]
