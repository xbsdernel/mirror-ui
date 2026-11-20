"""
Backward-compatibility alias for src.vision.stage2a_vlm.
"""

from src.vision.stage2a_vlm import (
    build_system_prompt,
    extract_json_from_text,
    validate_and_filter_elements,
    Qwen2VLInference,
    infer_elements,
)

__all__ = [
    "build_system_prompt",
    "extract_json_from_text",
    "validate_and_filter_elements",
    "Qwen2VLInference",
    "infer_elements",
]
