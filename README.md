# Mirror UI: Screenshot-to-Code Pipeline

An end-to-end multi-stage pipeline converting raw UI mockups, screenshots, and hand-drawn sketches into responsive, clean React + Tailwind components.

The project is structured according to the **GitHub Issues Backlog** across two primary pipelines connected by a frozen **Intermediate UI Representation (UIR)** JSON contract:
- **Person 1 (Computer Vision & VLM Pipeline)**: Ingests raw pixels, extracts structure via Qwen2-VL and PaddleOCR, performs spatial fusion, containment detection, layout classification, and outputs `ui_tree.json`.
- **Person 2 (Multi-Agent Code Synthesis & Validation Pipeline)**: Ingests `ui_tree.json`, componentizes trees, generates JSX via Qwen2.5-Coder with RAG, and runs syntax & visual comparison validation loops.

---

## 1. Architecture & Pipeline Overview

```
Input File (PNG / JPG / PDF / Sketch Photo)
                   │
                   ▼
  Stage 1 — Input Preprocessing (`src/vision/stage1_preprocessing.py`)
                   │
                   ├─ Multi-format ingestion (PNG, JPEG, PDF at 150 DPI)
                   ├─ Modality detection (screenshot / wireframe / sketch)
                   ├─ Modality-specific cleaning (CLAHE contrast for sketches only)
                   ├─ Capped resize (longest dimension ≤ 1280px)
                   └─ Coordinate tracking (stores `resize_ratio` for Stage 7)
                   │
                   ▼
  Stage 2A — VLM Element Inference (`src/vision/stage2a_vlm.py`)
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

## 2. Repository Directory Structure

```text
mirror-ui/
├── configs/
│   └── config.py                           # Central configurations (resolution caps, models, vocabulary)
├── docs/
│   ├── README.md                           # Documentation overview
│   └── github_issues_backlog.md            # Approved GitHub Issues Backlog (21 Epics, 48 Issues)
├── notebooks/
│   └── qwen2_vl_finetuning_kaggle.ipynb    # Kaggle notebook for QLoRA fine-tuning on UI datasets
├── src/
│   ├── __init__.py
│   ├── common/                             # Shared contracts and data types across pipelines
│   │   ├── __init__.py
│   │   └── types.py                        # Dataclasses: BoundingBox, StyleHints, UIElement, Stage1Result, Stage2AResult
│   ├── vision/                             # Person 1: Computer Vision & VLM Pipeline (Stages 1 through 7)
│   │   ├── __init__.py
│   │   ├── stage1_preprocessing.py         # Image loading, PDF rendering, modality detection & cleaning
│   │   ├── stage2a_vlm.py                  # Qwen2-VL inference engine, JSON parser & bounding box validator
│   │   └── pipeline.py                     # Vision pipeline orchestrator & debug overlay generator
│   ├── codegen/                            # Person 2: Multi-Agent Code Generation Pipeline (ADK Agents)
│   │   └── __init__.py
│   ├── pipeline.py                         # Backward-compatibility alias
│   ├── stage1_preprocessing.py             # Backward-compatibility alias
│   ├── stage2a_vlm.py                      # Backward-compatibility alias
│   └── types.py                            # Backward-compatibility alias
├── tests/                                  # Test suite
│   ├── __init__.py
│   ├── test_types.py                       # Unit tests for data structures
│   ├── test_stage1_preprocessing.py        # Unit tests for image preprocessing & modality detection
│   ├── test_stage2a_vlm.py                 # Unit tests for prompt building, JSON extraction & validation
│   └── test_imports_compatibility.py       # Verification of modular and legacy import paths
├── tools/                                  # Node.js toolchain for Babel, Vite, and Playwright
│   └── README.md
├── run_pipeline.py                         # Top-level CLI entry point
├── requirements.txt                        # Python dependencies
└── LICENSE                                 # License file
```

---

## 3. Getting Started

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Vision Pipeline
Run via the top-level CLI:
```bash
python run_pipeline.py path/to/your/mockup.png
```
Or via module execution:
```bash
python -m src.vision.pipeline path/to/your/mockup.png
```

Generated outputs appear in `outputs/`:
1. `outputs/normalized/<name>_normalized.png` — Capped to $\le 1280\text{px}$ with cleaning applied if sketch.
2. `outputs/<name>_stage2a_output.json` — Enriched JSON containing detected UI elements and bounding boxes.
3. `outputs/<name>_debug_overlay.png` — Visual debug image with colored bounding boxes and labels drawn over the UI.

---

## 4. Running Tests

Run the test suite with `pytest`:
```bash
pytest
```

---

## 5. Fine-Tuning on Kaggle (`notebooks/qwen2_vl_finetuning_kaggle.ipynb`)

A dedicated Jupyter notebook is provided in `notebooks/qwen2_vl_finetuning_kaggle.ipynb` tailored for Kaggle GPUs (T4 x 2 or P100):
- **4-bit QLoRA**: Fits within Kaggle's free GPU limits.
- **Multi-modal batch processing**: Converts UI screenshots and bounding boxes into Qwen2-VL chat format.
- **PEFT / LoRA target modules**: Fine-tunes attention projection layers (`q_proj`, `v_proj`, `o_proj`, etc.).
- **Adapter Export**: Saves trained adapters to `/kaggle/working/qwen2_vl_ui_lora` for downloading or publishing to Hugging Face Hub.

---

## 6. Downstream Roadmap (Stages 2B through 7 & Codegen)

- **Stage 2B (OCR)**: Runs PaddleOCR on `normalized_image_path`.
- **Stage 3 (Spatial Fusion)**: Pairs VLM bounding boxes with OCR text regions via IoU bipartite matching.
- **Stage 4 (Containment)**: Builds parent-child hierarchy tree.
- **Stage 5 (Layout)**: Infers flex direction, semantic gap sizes, and alignment.
- **Stage 6 (Patterns)**: Identifies repeated structural subtrees.
- **Stage 7 (UIR Serialization)**: Back-scales coordinates via `1 / resize_ratio` and exports `ui_tree.json`.
- **Person 2 (Codegen)**: Generates React JSX using Qwen2.5-Coder, validated by Babel AST parsing and Playwright visual diffs.
