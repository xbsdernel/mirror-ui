"""
Data Types and Schemas for UI-to-Code Pipeline.
Shared across Vision Pipeline (Person 1) and Code Generation Pipeline (Person 2).
Uses standard Python dataclasses for simplicity and readability.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple


@dataclass
class BoundingBox:
    """
    Axis-aligned bounding box coordinates.
    Values represent pixels in the normalized image space.
    """
    x: float
    y: float
    w: float
    h: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "w": round(self.w, 2),
            "h": round(self.h, 2)
        }


@dataclass
class StyleHints:
    """
    Visual style attributes detected by the VLM.
    """
    background: Optional[str] = None
    border: Optional[str] = None
    rounded: Optional[str] = None
    shadow: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "background": self.background,
            "border": self.border,
            "rounded": self.rounded,
            "shadow": self.shadow
        }


@dataclass
class UIElement:
    """
    A single UI element detected by the VLM in Stage 2A.
    """
    id: str
    type: str
    bounds: BoundingBox
    style_hints: StyleHints

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "bounds": self.bounds.to_dict(),
            "style_hints": self.style_hints.to_dict()
        }


@dataclass
class Stage1Result:
    """
    Output produced by Stage 1 (Input Preprocessing).
    """
    normalized_image_path: str
    input_type: str                   # 'screenshot', 'wireframe', or 'sketch'
    resize_ratio: float               # normalized_size / original_size
    original_size: Tuple[int, int]    # (width, height)
    normalized_size: Tuple[int, int]  # (width, height)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "normalized_image_path": self.normalized_image_path,
            "input_type": self.input_type,
            "resize_ratio": self.resize_ratio,
            "original_size": list(self.original_size),
            "normalized_size": list(self.normalized_size)
        }


@dataclass
class Stage2AResult:
    """
    Output produced by Stage 2A (VLM Element Inference).
    """
    elements: List[UIElement] = field(default_factory=list)
    status: str = "success"           # 'success', 'partial', or 'failed'
    error_message: Optional[str] = None
    raw_response: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "error_message": self.error_message,
            "element_count": len(self.elements),
            "elements": [elem.to_dict() for elem in self.elements]
        }
