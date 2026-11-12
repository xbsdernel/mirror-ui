"""
Project Configuration
Contains standard settings for Stage 1 (Preprocessing) and Stage 2A (Qwen2-VL Inference).
"""

# Maximum resolution for the longest dimension of the image
MAX_IMAGE_DIMENSION = 1280

# PDF rendering resolution (DPI)
PDF_DPI = 150

# Default Hugging Face model identifier for Qwen2-VL
DEFAULT_MODEL_NAME = "Qwen/Qwen2-VL-7B-Instruct"

# Smaller model option for quick local testing on lower VRAM
LIGHTWEIGHT_MODEL_NAME = "Qwen/Qwen2-VL-2B-Instruct"

# 4-bit Quantization setting (recommended for 12GB GPUs)
USE_4BIT_QUANTIZATION = True

# Maximum number of retries if the VLM returns invalid JSON
MAX_PARSE_RETRIES = 2

# Strict UI Element Type Vocabulary
UI_TYPE_VOCABULARY = [
    "container",
    "card",
    "button",
    "input",
    "image",
    "icon",
    "navbar",
    "sidebar",
    "modal",
    "tab",
    "checkbox",
    "radio",
    "switch",
    "avatar",
    "divider",
    "badge",
    "link",
    "text_block"
]
