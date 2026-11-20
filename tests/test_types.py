"""
Unit tests for data types and schemas in src.common.types.
"""

from src.common.types import (
    BoundingBox,
    StyleHints,
    UIElement,
    Stage1Result,
    Stage2AResult,
)


def test_bounding_box_to_dict():
    box = BoundingBox(x=10.1234, y=20.5678, w=100.0, h=50.0)
    d = box.to_dict()
    assert d == {"x": 10.12, "y": 20.57, "w": 100.0, "h": 50.0}


def test_style_hints_to_dict():
    style = StyleHints(background="#ffffff", border="1px solid #ccc", rounded="md", shadow=None)
    d = style.to_dict()
    assert d["background"] == "#ffffff"
    assert d["border"] == "1px solid #ccc"
    assert d["rounded"] == "md"
    assert d["shadow"] is None


def test_ui_element_to_dict():
    box = BoundingBox(x=0, y=0, w=100, h=40)
    style = StyleHints(background="#007bff")
    elem = UIElement(id="btn_1", type="button", bounds=box, style_hints=style)
    d = elem.to_dict()
    assert d["id"] == "btn_1"
    assert d["type"] == "button"
    assert d["bounds"]["w"] == 100
    assert d["style_hints"]["background"] == "#007bff"


def test_stage1_result_to_dict():
    res = Stage1Result(
        normalized_image_path="test.png",
        input_type="screenshot",
        resize_ratio=0.8,
        original_size=(1600, 1200),
        normalized_size=(1280, 960),
    )
    d = res.to_dict()
    assert d["input_type"] == "screenshot"
    assert d["resize_ratio"] == 0.8
    assert d["original_size"] == [1600, 1200]
    assert d["normalized_size"] == [1280, 960]


def test_stage2a_result_to_dict():
    box = BoundingBox(x=10, y=20, w=30, h=40)
    elem = UIElement(id="elem_0", type="card", bounds=box, style_hints=StyleHints())
    res = Stage2AResult(elements=[elem], status="success", error_message=None)
    d = res.to_dict()
    assert d["status"] == "success"
    assert d["element_count"] == 1
    assert len(d["elements"]) == 1
