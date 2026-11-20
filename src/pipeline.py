"""
Backward-compatibility alias for src.vision.pipeline.
"""

from src.vision.pipeline import (
    draw_debug_overlay,
    run_pipeline,
)

__all__ = [
    "draw_debug_overlay",
    "run_pipeline",
]

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        run_pipeline(test_file)
    else:
        print("Usage: python -m src.pipeline <path_to_image_or_pdf>")
