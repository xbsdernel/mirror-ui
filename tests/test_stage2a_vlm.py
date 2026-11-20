"""
Unit tests for Stage 2A VLM Parsing and Validation.
"""

from src.vision.stage2a_vlm import (
    build_system_prompt,
    extract_json_from_text,
    validate_and_filter_elements,
)
from configs.config import UI_TYPE_VOCABULARY


def test_build_system_prompt():
    prompt = build_system_prompt(1280, 720)
    assert "1280 width x 720 height" in prompt
    assert "Strict Type Vocabulary:" in prompt
    assert "button" in prompt
    assert "Output ONLY the raw JSON array" in prompt


def test_extract_json_from_clean_text():
    raw = '[{"id": "elem_0", "type": "button", "bounds": {"x": 10, "y": 20, "w": 30, "h": 40}}]'
    res = extract_json_from_text(raw)
    assert res is not None
    assert len(res) == 1
    assert res[0]["id"] == "elem_0"


def test_extract_json_from_markdown_fence():
    raw = """```json
[
  {"id": "elem_1", "type": "card", "bounds": {"x": 0, "y": 0, "w": 100, "h": 100}}
]
```"""
    res = extract_json_from_text(raw)
    assert res is not None
    assert len(res) == 1
    assert res[0]["type"] == "card"


def test_extract_json_with_surrounding_prose():
    raw = """Here is the UI structure:
[
  {"id": "elem_0", "type": "navbar", "bounds": {"x": 0, "y": 0, "w": 800, "h": 60}}
]
Hope this helps!"""
    res = extract_json_from_text(raw)
    assert res is not None
    assert len(res) == 1
    assert res[0]["type"] == "navbar"


def test_extract_json_invalid():
    raw = "This is not valid JSON at all."
    assert extract_json_from_text(raw) is None


def test_validate_and_filter_elements():
    raw_elements = [
        # Valid element
        {
            "id": "elem_0",
            "type": "button",
            "bounds": {"x": 10, "y": 20, "w": 100, "h": 40},
            "style_hints": {"background": "#007bff"}
        },
        # Out-of-bounds negative x -> should be discarded
        {
            "id": "elem_1",
            "type": "card",
            "bounds": {"x": -10, "y": 20, "w": 100, "h": 40}
        },
        # Negative width/height -> should be discarded
        {
            "id": "elem_2",
            "type": "input",
            "bounds": {"x": 10, "y": 20, "w": 0, "h": 40}
        },
        # Beyond image boundary (width=1000) -> should be discarded or clamped
        {
            "id": "elem_3",
            "type": "container",
            "bounds": {"x": 1050, "y": 20, "w": 100, "h": 40}
        },
        # Unknown type -> should fallback to container
        {
            "id": "elem_4",
            "type": "super_fancy_widget",
            "bounds": {"x": 10, "y": 20, "w": 50, "h": 50}
        }
    ]

    valid = validate_and_filter_elements(raw_elements, image_width=1000, image_height=800)
    assert len(valid) == 2
    assert valid[0].id == "elem_0"
    assert valid[0].type == "button"
    assert valid[1].id == "elem_4"
    assert valid[1].type == "container"  # coerced fallback
