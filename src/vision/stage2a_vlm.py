"""
Stage 2A — VLM Element Inference (Qwen2-VL) (Person 1 CV Pipeline)

Responsibilities:
1. Construct a strict 4-part prompt with agreed UI vocabulary and concrete JSON schema.
2. Run inference using Qwen2-VL (supports 4-bit quantization for 12GB GPUs).
3. Enforce structured JSON parsing with up to 2 retry attempts.
4. Post-parse validation: Discard out-of-bounds bounding boxes and hallucinated coordinates.
5. Return a clean Stage2AResult without crashing downstream stages.
"""

import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image

from src.common.types import UIElement, BoundingBox, StyleHints, Stage2AResult
from configs.config import (
    DEFAULT_MODEL_NAME,
    USE_4BIT_QUANTIZATION,
    MAX_PARSE_RETRIES,
    UI_TYPE_VOCABULARY
)


def build_system_prompt(image_width: int, image_height: int) -> str:
    """
    Constructs the 4-part prompt for the VLM:
    1. Role instruction
    2. Concrete JSON output schema
    3. Strict type vocabulary
    4. Hard negative output constraint
    """
    vocab_str = ", ".join([f'"{t}"' for t in UI_TYPE_VOCABULARY])

    prompt = f"""You are an expert UI layout analyzer.
Your task is to analyze the user interface in the provided image and extract all visual elements and containers.

Image Resolution: {image_width} width x {image_height} height (in pixels).

Strict Type Vocabulary:
Only use these types: [{vocab_str}].

Output Schema:
Output must be a valid JSON array of element objects. Do NOT detect text content (text is extracted separately by OCR).
Each element object must follow this exact format:
[
  {{
    "id": "elem_0",
    "type": "button",
    "bounds": {{
      "x": 45,
      "y": 120,
      "w": 180,
      "h": 40
    }},
    "style_hints": {{
      "background": "#007bff",
      "border": "none",
      "rounded": "md",
      "shadow": "sm"
    }}
  }}
]

Bounding Box Rules:
- "x": left coordinate in pixels (0 to {image_width}).
- "y": top coordinate in pixels (0 to {image_height}).
- "w": width of element in pixels.
- "h": height of element in pixels.
- Ensure all bounding boxes fit completely within the image dimensions ({image_width}x{image_height}).

Hard Constraint:
Output ONLY the raw JSON array. Do not include markdown formatting (like ```json), commentary, or notes before or after.
"""
    return prompt


def extract_json_from_text(raw_text: str) -> Optional[List[Dict[str, Any]]]:
    """
    Safely extracts and parses a JSON array from model output.
    Handles potential markdown code fences and whitespace.
    """
    text = raw_text.strip()

    # Strip markdown code blocks if the model wrapped them
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    # Try direct parsing
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and "elements" in parsed:
            return parsed["elements"]
    except Exception:
        pass

    # Regex search for the outermost JSON array [...]
    match = re.search(r"\[\s*\{.*\}\s*\]", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

    return None


def validate_and_filter_elements(
    raw_elements: List[Dict[str, Any]],
    image_width: int,
    image_height: int
) -> List[UIElement]:
    """
    Post-parse validation:
    - Discards out-of-bounds boxes (hallucinations).
    - Checks for minimum width/height.
    - Normalizes types against the agreed vocabulary.
    """
    valid_elements: List[UIElement] = []

    for idx, item in enumerate(raw_elements):
        if not isinstance(item, dict):
            continue

        elem_id = str(item.get("id", f"elem_{idx}"))
        raw_type = str(item.get("type", "container")).lower().strip()

        # Check vocabulary
        if raw_type in UI_TYPE_VOCABULARY:
            elem_type = raw_type
        else:
            elem_type = "container"

        # Check bounds
        bounds_dict = item.get("bounds", {})
        if not isinstance(bounds_dict, dict):
            continue

        try:
            x = float(bounds_dict.get("x", -1))
            y = float(bounds_dict.get("y", -1))
            w = float(bounds_dict.get("w", -1))
            h = float(bounds_dict.get("h", -1))
        except (ValueError, TypeError):
            continue

        # Post-parse boundary check: discard if out of bounds or negative
        if x < 0 or y < 0:
            continue
        if w <= 1 or h <= 1:
            continue
        if (x + w) > (image_width + 5) or (y + h) > (image_height + 5):
            # Allow a tiny 5px tolerance by clamping, otherwise discard
            if x >= image_width or y >= image_height:
                continue
            w = min(w, image_width - x)
            h = min(h, image_height - y)

        bbox = BoundingBox(x=x, y=y, w=w, h=h)

        # Style hints
        raw_style = item.get("style_hints", {})
        if not isinstance(raw_style, dict):
            raw_style = {}

        style = StyleHints(
            background=raw_style.get("background"),
            border=raw_style.get("border"),
            rounded=raw_style.get("rounded"),
            shadow=raw_style.get("shadow")
        )

        valid_elements.append(UIElement(
            id=elem_id,
            type=elem_type,
            bounds=bbox,
            style_hints=style
        ))

    return valid_elements


class Qwen2VLInference:
    """
    Wrapper for Qwen2-VL model inference using Hugging Face Transformers.
    Supports 4-bit quantization (BitsAndBytes) for running on GPUs with <=12GB VRAM.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        use_4bit: bool = USE_4BIT_QUANTIZATION,
        device: Optional[str] = None
    ):
        self.model_name = model_name
        self.use_4bit = use_4bit
        self.model = None
        self.processor = None

        if device:
            self.device = device
        else:
            import torch
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load_model(self):
        """
        Loads the Qwen2-VL model and processor into memory.
        """
        if self.model is not None:
            return

        import torch
        from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

        print(f"Loading Qwen2-VL model: '{self.model_name}' (device={self.device}, 4bit={self.use_4bit})...")

        # Load processor
        self.processor = AutoProcessor.from_pretrained(self.model_name)

        # Load model weights
        if self.use_4bit and self.device == "cuda":
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True
            )
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_name,
                quantization_config=bnb_config,
                device_map="auto"
            )
        else:
            dtype = torch.bfloat16 if self.device == "cuda" else torch.float32
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=dtype,
                device_map="auto" if self.device == "cuda" else None
            )
            if self.device == "cpu":
                self.model = self.model.to("cpu")

        print("Qwen2-VL model loaded successfully.")

    def generate_response(self, pil_image: Image.Image, prompt_text: str) -> str:
        """
        Runs forward inference through the Qwen2-VL model.
        """
        from qwen_vl_utils import process_vision_info

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": pil_image},
                    {"type": "text", "text": prompt_text}
                ]
            }
        ]

        text_prompt = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)

        inputs = self.processor(
            text=[text_prompt],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt"
        )
        inputs = inputs.to(self.model.device)

        import torch
        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=2048,
                temperature=0.1,
                do_sample=False
            )

        # Trim input prompt tokens from output
        generated_ids_trimmed = [
            out_ids[len(in_ids):]
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = self.processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]

        return output_text


def infer_elements(
    normalized_image_path: str,
    vlm_engine: Optional[Qwen2VLInference] = None,
    max_retries: int = MAX_PARSE_RETRIES
) -> Stage2AResult:
    """
    Main entry point for Stage 2A.
    Analyzes the normalized image, generates elements, parses JSON,
    and applies retry logic on parse failure.
    """
    if not os.path.exists(normalized_image_path):
        return Stage2AResult(
            elements=[],
            status="failed",
            error_message=f"Image file not found: {normalized_image_path}"
        )

    pil_image = Image.open(normalized_image_path).convert("RGB")
    img_w, img_h = pil_image.size

    # Initialize model if not passed in
    if vlm_engine is None:
        vlm_engine = Qwen2VLInference()
    vlm_engine.load_model()

    prompt = build_system_prompt(img_w, img_h)
    raw_response = ""
    parsed_json = None

    # Retry loop (attempt 0 + up to max_retries)
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                print(f"[Stage 2A] Parse retry {attempt}/{max_retries} with error correction prompt...")
                correction_prompt = (
                    prompt + "\n\nCRITICAL ERROR: Your previous response was not valid JSON. "
                    "You must output ONLY a valid JSON array starting with '[' and ending with ']'. "
                    "No conversational text, no markdown."
                )
                raw_response = vlm_engine.generate_response(pil_image, correction_prompt)
            else:
                raw_response = vlm_engine.generate_response(pil_image, prompt)

            parsed_json = extract_json_from_text(raw_response)
            if parsed_json is not None:
                break
        except Exception as err:
            if attempt == max_retries:
                return Stage2AResult(
                    elements=[],
                    status="failed",
                    error_message=f"Inference error after {max_retries} retries: {str(err)}",
                    raw_response=raw_response
                )

    # If parsing still failed after all retries, return graceful failure without crashing
    if parsed_json is None:
        return Stage2AResult(
            elements=[],
            status="failed",
            error_message=f"Failed to parse valid JSON from VLM output after {max_retries} retries.",
            raw_response=raw_response
        )

    # Post-parse validation: validate and filter bounding boxes
    valid_elements = validate_and_filter_elements(parsed_json, img_w, img_h)

    return Stage2AResult(
        elements=valid_elements,
        status="success",
        error_message=None,
        raw_response=raw_response
    )
