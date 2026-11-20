"""
Vision & VLM Pipeline (Person 1: Stages 1 through 7)
"""

from src.vision.stage1_preprocessing import (
    load_pdf_as_image,
    detect_modality,
    clean_sketch_image,
    resize_image_capped,
    preprocess_image,
)
from src.vision.stage2a_vlm import (
    build_system_prompt,
    extract_json_from_text,
    validate_and_filter_elements,
    Qwen2VLInference,
    infer_elements,
)
from src.vision.pipeline import (
    draw_debug_overlay,
    run_pipeline,
)

__all__ = [
    "load_pdf_as_image",
    "detect_modality",
    "clean_sketch_image",
    "resize_image_capped",
    "preprocess_image",
    "build_system_prompt",
    "extract_json_from_text",
    "validate_and_filter_elements",
    "Qwen2VLInference",
    "infer_elements",
    "draw_debug_overlay",
    "run_pipeline",
]
