"""
Pipeline Orchestrator (Person 1 CV Pipeline: Stage 1 -> Stage 2A)

Connects Input Preprocessing and Qwen2-VL Element Inference.
Includes an optional debug visualization tool to overlay bounding boxes.
"""

import os
import json
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont

from src.vision.stage1_preprocessing import preprocess_image
from src.vision.stage2a_vlm import infer_elements, Qwen2VLInference
from src.common.types import Stage1Result, Stage2AResult


def draw_debug_overlay(
    image_path: str,
    stage2_result: Stage2AResult,
    output_path: str
) -> None:
    """
    Draws predicted bounding boxes and type labels onto the image.
    Helpful for visually inspecting VLM predictions during development.
    """
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    # Simple distinct colors for element types
    color_palette = {
        "button": "#FF3B30",
        "container": "#007AFF",
        "card": "#34C759",
        "input": "#FF9500",
        "image": "#AF52DE",
        "icon": "#5856D6",
        "navbar": "#5AC8FA",
        "sidebar": "#FF2D55",
        "text_block": "#8E8E93"
    }
    default_color = "#32D74B"

    for elem in stage2_result.elements:
        b = elem.bounds
        x0, y0 = b.x, b.y
        x1, y1 = b.x + b.w, b.y + b.h

        color = color_palette.get(elem.type, default_color)

        # Draw bounding rectangle
        draw.rectangle([x0, y0, x1, y1], outline=color, width=2)

        # Draw label tag
        label = f"{elem.type} [{elem.id}]"
        # Background badge for text label
        draw.rectangle([x0, max(0, y0 - 16), x0 + len(label) * 8 + 4, y0], fill=color)
        draw.text((x0 + 2, max(0, y0 - 15)), label, fill="white")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.save(output_path)
    print(f"[Debug] Saved visualization overlay to: {output_path}")


def run_pipeline(
    input_file_path: str,
    output_dir: str = "outputs",
    model_name: str = "Qwen/Qwen2-VL-7B-Instruct",
    use_4bit: bool = True,
    vlm_engine: Optional[Qwen2VLInference] = None,
    save_debug_image: bool = True
) -> Dict[str, Any]:
    """
    Runs the vision pipeline from Stage 1 to Stage 2A.

    Parameters:
        input_file_path: Path to raw input image or PDF.
        output_dir: Folder to store normalized images, debug overlays, and JSON results.
        model_name: Hugging Face model id.
        use_4bit: Whether to load model with 4-bit quantization.
        vlm_engine: Optional pre-loaded Qwen2VLInference instance.
        save_debug_image: Whether to generate a bounding box overlay PNG.

    Returns:
        Dictionary containing metadata, Stage 1 result, and Stage 2A element list.
    """
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n=== [Stage 1] Preprocessing Input: {input_file_path} ===")
    stage1_res = preprocess_image(
        input_path=input_file_path,
        output_dir=os.path.join(output_dir, "normalized"),
        max_dim=1280
    )
    print(f"  Modality detected : {stage1_res.input_type}")
    print(f"  Original size     : {stage1_res.original_size}")
    print(f"  Normalized size   : {stage1_res.normalized_size}")
    print(f"  Resize ratio      : {stage1_res.resize_ratio:.4f}")

    print(f"\n=== [Stage 2A] Running VLM Element Inference (Qwen2-VL) ===")
    if vlm_engine is None:
        vlm_engine = Qwen2VLInference(model_name=model_name, use_4bit=use_4bit)

    stage2_res = infer_elements(
        normalized_image_path=stage1_res.normalized_image_path,
        vlm_engine=vlm_engine
    )

    print(f"  Inference status  : {stage2_res.status}")
    print(f"  Elements detected : {len(stage2_res.elements)}")
    if stage2_res.error_message:
        print(f"  Warning / Error   : {stage2_res.error_message}")

    # Optional debug visualization
    base_name = os.path.splitext(os.path.basename(input_file_path))[0]
    if save_debug_image and stage2_res.status == "success":
        debug_path = os.path.join(output_dir, f"{base_name}_debug_overlay.png")
        draw_debug_overlay(stage1_res.normalized_image_path, stage2_res, debug_path)

    # Package output payload
    combined_output = {
        "source_file": input_file_path,
        "stage1_preprocessing": stage1_res.to_dict(),
        "stage2a_vlm_elements": stage2_res.to_dict()
    }

    # Save output JSON
    json_path = os.path.join(output_dir, f"{base_name}_stage2a_output.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(combined_output, f, indent=2)
    print(f"  Saved JSON output to: {json_path}")

    return combined_output


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        run_pipeline(test_file)
    else:
        print("Usage: python -m src.vision.pipeline <path_to_image_or_pdf>")
