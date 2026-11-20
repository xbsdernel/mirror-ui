#!/usr/bin/env python
"""
Unified CLI Entry Point for UI-to-Code Pipeline.
Ref: Backlog ISSUE-048 / Epic 21.
"""

import sys
from src.vision.pipeline import run_pipeline

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        run_pipeline(test_file)
    else:
        print("Usage: python run_pipeline.py <path_to_image_or_pdf>")
