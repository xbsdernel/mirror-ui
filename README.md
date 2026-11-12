# Computer Vision UI-to-Code Pipeline (Stages 1 & 2A)

This repository contains the implementation of **Stage 1 (Input Preprocessing)** and **Stage 2A (VLM Element Inference with Qwen2-VL)** for extracting semantic UI structures from screenshots, wireframes, and sketches.

---

## 1. Pipeline Overview

```
Input File (PNG / JPG / PDF / Sketch Photo)
                   │
                   ▼
  Stage 1 — Input Preprocessing (`src/stage1_preprocessing.py`)
                   │
                   ├─ PDF Rendering to PNG at 150 DPI
                   ├─ Modality Detection (screenshot / wireframe / sketch)
                   ├─ Modality-Specific Cleaning (CLAHE contrast for sketches only)
                   ├─ Capped Resize (longest dimension ≤ 1280px)
                   └─ Coordinate Tracking (stores `resize_ratio` for Stage 7)
                   │
                   ▼
  Stage 2A — VLM Element Inference (`src/stage2a_vlm.py`)
                   │
                   ├─ Model: Qwen2-VL-7B-Instruct (4-bit quantized)
                   ├─ 4-part strict prompt + agreed UI vocabulary
                   ├─ Structured JSON extraction with retry loop (max 2 retries)
                   └─ Post-parse bounding box boundary validation
                   │
                   ▼
  Stage 2A Output (`outputs/<filename>_stage2a_output.json`)
     [Ready for Stage 3 Spatial Fusion with OCR]
```

---

## 2. Directory Structure

```text
d:\CV project\
├── configs/
│   └── config.py                           # Resolution caps, model names, vocabulary
├── src/
│   ├── __init__.py
│   ├── types.py                            # Simple dataclasses (BoundingBox, UIElement, Stage1Result, Stage2AResult)
│   ├── stage1_preprocessing.py             # Image loading, PDF rendering, modality detection & cleaning
│   ├── stage2a_vlm.py                      # Qwen2-VL inference engine, JSON parser & bounding box validator
│   └── pipeline.py                         # End-to-end runner (Stage 1 -> Stage 2A + visual debug overlay)
├── notebooks/
│   └── qwen2_vl_finetuning_kaggle.ipynb    # Kaggle notebook for QLoRA fine-tuning on UI datasets
├── requirements.txt                        # Python dependencies
└── README.md                               # Project documentation
```

---

## 3. How to Run (When You Are Ready)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Pipeline on an Image or PDF
```bash
python -m src.pipeline path/to/your/mockup.png
```

This will produce three outputs in the `outputs/` folder:
1. `outputs/normalized/<name>_normalized.png` — Capped to $\le 1280\text{px}$ with cleaning applied if sketch.
2. `outputs/<name>_stage2a_output.json` — Enriched JSON containing all detected UI elements and bounding boxes.
3. `outputs/<name>_debug_overlay.png` — Visual debug image with colored bounding boxes and labels drawn over the UI.

---

## 4. Fine-Tuning on Kaggle (`notebooks/qwen2_vl_finetuning_kaggle.ipynb`)

A dedicated Jupyter notebook is provided in `notebooks/qwen2_vl_finetuning_kaggle.ipynb` tailored for Kaggle GPUs (T4 x 2 or P100):
- **4-bit QLoRA**: Fits within Kaggle's free GPU limits.
- **Multi-modal batch processing**: Converts UI screenshots and bounding boxes into Qwen2-VL chat format.
- **PEFT / LoRA target modules**: Fine-tunes attention projection layers (`q_proj`, `v_proj`, `o_proj`, etc.).
- **Adapter Export**: Saves trained adapters to `/kaggle/working/qwen2_vl_ui_lora` for downloading or publishing to Hugging Face Hub.

---

## 5. Downstream Compatibility (Stages 2B - 7)

- **Stage 2B (OCR)** runs on the same `normalized_image_path` produced in Stage 1.
- **Stage 3 (Spatial Fusion)** matches the bounding boxes produced by Stage 2A with the OCR text regions produced by Stage 2B via IoU.
- **Stage 7 (UIR Serialization)** converts coordinates back to original pixel space using:
  $$\text{original\_coord} = \frac{\text{normalized\_coord}}{\text{resize\_ratio}}$$
