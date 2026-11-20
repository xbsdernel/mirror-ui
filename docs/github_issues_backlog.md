# GitHub Issues Backlog — UI-to-Code Pipeline
> **Project:** Screenshot-to-React Code Generation System  
> **Pipeline:** Image → UIR JSON (Person 1 / CV Pipeline) → App.jsx (Person 2 / Code Gen Pipeline)  
> **Team Size:** 5 members  
> **Document Version:** 1.0 — based on full architecture specification (both Person 1 and Person 2 sections)

---

## 1. Project Overview

This project builds an end-to-end system that takes a raw UI image (screenshot, wireframe, or hand-drawn sketch) and produces a compiling, visually accurate React + Tailwind `App.jsx`. The system is split into two independent pipelines joined by a frozen JSON contract — the **Intermediate UI Representation (UIR)**.

**Person 1 (CV Pipeline)** owns everything from raw pixel input to `ui_tree.json`.  
**Person 2 (Code Gen Pipeline)** owns everything from `ui_tree.json` to a validated, rendered `App.jsx`.

---

## 2. Scope and Constraints

### In Scope
- Three input modalities: screenshot, wireframe, hand-drawn sketch (including PDF → PNG rendering)
- Stage 1: Input preprocessing (resize, modality detection, sketch cleaning)
- Stage 2A: VLM element inference via Qwen2-VL-7B (4-bit quantized)
- Stage 2B: OCR text extraction via PaddleOCR
- Stage 3: Spatial fusion (IoU-based VLM ↔ OCR matching)
- Stage 4: Containment detection (tree construction, containment threshold 0.8)
- Stage 5: Layout annotation (row/column classification, gap estimation, alignment, justify)
- Stage 6: Pattern / subtree detection (structural signature hashing, component naming hints)
- Stage 7: UIR validation and serialization to `ui_tree.json` with coordinate back-scaling
- Person 2 Agent 1 (`IngestionAgent`): UIR schema validation
- Person 2 Agent 2 (`SubtreeHashTool` + `ComponentizationAgent`): Subtree hashing and component naming
- Person 2 Agent 3 (`CodeGenAgent`): JSX + Tailwind code generation (Qwen2.5-Coder-7B via vLLM, fan-out/fan-in)
- Person 2 Agent 4 (`JSXValidatorAgent` + `RepairAgent`): Syntax validation loop
- Person 2 Agent 5 (`BrowserRenderAgent`): Vite + Playwright rendering
- Person 2 Agent 6 (`VisualComparisonAgent`): 5-metric visual similarity ensemble (CW-SSIM, bbox/text/color matching, LPIPS, CLIP, DreamSim)
- Person 2 Agent 7 (`CorrectionPlannerAgent` + `TargetedCorrectionAgent`): Targeted visual correction loop
- Person 2 Agent 8 (`OutputAssemblyAgent`): Best-candidate selection, final output writing
- RAG layer: ChromaDB + Qwen3-Embedding-8B
- Node toolchain: `babel_validate.js`, `vite_render.mjs`, `playwright_shoot.mjs`
- Evaluation harness: IoU, tree edit distance (Person 1); Compilation Pass Rate, CW-SSIM/CLIP (Person 2)
- Kaggle notebook for Qwen2-VL QLoRA fine-tuning
- Hardware tiering: local Ollama (dev/plumbing) → Kaggle P100/T4 (real runs) → HF Spaces ZeroGPU (demo)
- OpenTelemetry observability integration

### Out of Scope (explicitly excluded by document)
- Tailwind class name mapping (Person 2 responsibility only — not for Person 1 to output)
- React component naming and prop naming (Person 2 responsibility only)
- Framework-specific concepts in UIR (UIR is framework-independent)
- Pixel-value CSS output (Person 1 must use semantic gap/alignment labels, not raw px values)
- Full multi-tenancy or authentication infrastructure
- Any CAPTCHA or bot-bypass mechanism

### Explicitly Agreed Technology Stack
| Concern | Technology |
|---|---|
| VLM (Person 1) | Qwen2-VL-7B-Instruct (4-bit BitsAndBytes) |
| OCR | PaddleOCR |
| Agent Orchestration | Google ADK (`SequentialAgent`, `ParallelAgent`, `LoopAgent`) |
| Code Gen Model | Qwen2.5-Coder-7B-Instruct AWQ 4-bit (vLLM) |
| Embedding (RAG) | Qwen3-Embedding-8B |
| Vector Store | ChromaDB (local) |
| JSX Validation | `@babel/parser` with `errorRecovery: true` |
| Browser Rendering | Vite + Playwright |
| Visual Metrics | CW-SSIM, LPIPS, CLIP, DreamSim, bbox/text/color element matching |
| Fine-Tuning | QLoRA via PEFT + BitsAndBytes (Kaggle notebooks) |
| Observability | OpenTelemetry |
| Local Dev Inference | Ollama / llama.cpp (Qwen2.5-Coder-1.5B–3B GGUF) |

---

## 3. Unresolved Questions and Missing Information

| ID | Question | Why It Matters | Required Decision |
|---|---|---|---|
| **UQ-01** | Exact final UIR JSON schema field list and allowed values | Both pipelines depend on this frozen contract. No implementation can safely begin until it is committed. | Joint Week-1 session: freeze every field, every type label, every allowed semantic gap/alignment label, bounding box coordinate convention, file name, and schema version. |
| **UQ-02** | Exact structural signature format for subtree hashing | Person 1's Stage 6 and Person 2's `SubtreeHashTool` must use an identical DFS type-label concatenation format. If they diverge, `repeated_pattern` flags will disagree silently. | Agree and commit the exact string encoding algorithm alongside the UIR schema in Week 1. |
| **UQ-03** | Containment threshold grid search range and final value | The document specifies a grid search over [0.70, 0.75, 0.80, 0.85, 0.90] against RICO annotations, with 0.8 as the starting value. The final chosen value is unresolved. | Person 1 (Member 1) runs the grid search and locks the threshold before Stage 4 is finalized. |
| **UQ-04** | Gap semantic label thresholds (0–4px / 4–12px / 12–28px / 28+px) | The document states these must be "calibrated against RICO gap distributions." The document gives initial values but not final calibrated values. | Person 1 (Member 1) runs calibration and locks thresholds before Stage 5 is finalized. |
| **UQ-05** | Visual metric composite score weights | The document states "run all five metrics against 20–30 hand-labeled pages and pick weights that best separate your own labels." Weights are unresolved before the labeled set is built. | Person 2 (Member 4 / Member 5) build the hand-labeled set and run calibration before `VisualComparisonAgent` is finalized. |
| **UQ-06** | Maximum visual correction loop iterations | The document says "3–5 max_iterations" without committing to a value. | Decide a fixed default and configure it in `configs/` before the render loop is integrated. |
| **UQ-07** | PDF multi-page strategy | The document specifies "render the first page." Multi-page handling is not addressed. | For v1, limit to first page only. Document this limitation explicitly. |
| **UQ-08** | `wireframe` modality in detection logic | The document mentions wireframe as a distinct modality but the detection heuristics cover screenshot vs. sketch only. No explicit wireframe signal is defined. | Decide: does wireframe fall under screenshot in the detection logic, or is a separate heuristic needed? |

---

## 4. Epic Overview

| Epic ID | Title | Owner | Depends On |
|---|---|---|---|
| **EPIC-01** | Shared Project Foundation & UIR Contract | Member 5 | — |
| **EPIC-02** | Stage 1 — Input Preprocessing | Member 1 | EPIC-01 |
| **EPIC-03** | Stage 2A — VLM Element Inference (Qwen2-VL) | Member 1 | EPIC-01, EPIC-02 |
| **EPIC-04** | Stage 2B — OCR Text Extraction (PaddleOCR) | Member 2 | EPIC-01, EPIC-02 |
| **EPIC-05** | Stage 3 — Spatial Fusion | Member 2 | EPIC-03, EPIC-04 |
| **EPIC-06** | Stage 4 — Containment Detection | Member 1 | EPIC-05 |
| **EPIC-07** | Stage 5 — Layout Annotation | Member 1 | EPIC-06 |
| **EPIC-08** | Stage 6 — Pattern / Subtree Detection | Member 2 | EPIC-07 |
| **EPIC-09** | Stage 7 — UIR Validation & Serialization | Member 2 | EPIC-06, EPIC-07, EPIC-08 |
| **EPIC-10** | Person 1 Evaluation Harness | Member 1 | EPIC-09 |
| **EPIC-11** | Kaggle Fine-Tuning Notebook (Qwen2-VL) | Member 3 | EPIC-03 |
| **EPIC-12** | Person 2 — Ingestion & Componentization | Member 3 | EPIC-01, EPIC-09 |
| **EPIC-13** | Person 2 — RAG Layer | Member 3 | EPIC-01 |
| **EPIC-14** | Person 2 — Code Generation Pipeline | Member 3 | EPIC-12, EPIC-13 |
| **EPIC-15** | Person 2 — Syntax Validation & Repair Loop | Member 4 | EPIC-14 |
| **EPIC-16** | Node Toolchain (Babel / Vite / Playwright) | Member 4 | — |
| **EPIC-17** | Person 2 — Visual Comparison & Correction Loop | Member 4 | EPIC-15, EPIC-16 |
| **EPIC-18** | Person 2 — Output Assembly Agent | Member 5 | EPIC-17 |
| **EPIC-19** | Observability & OpenTelemetry Integration | Member 5 | EPIC-14, EPIC-15, EPIC-17 |
| **EPIC-20** | Person 2 Evaluation Harness | Member 5 | EPIC-18 |
| **EPIC-21** | End-to-End Integration & System Testing | Member 5 | EPIC-09, EPIC-18 |

---

## 5. Detailed GitHub Issues Backlog

---

### EPIC-01 — Shared Project Foundation & UIR Contract

**Objective:** Establish the frozen UIR JSON schema, agreed type vocabulary, structural signature spec, project scaffolding, and shared Python type definitions that all other Epics build against.  
**Expected Outcome:** A committed `ui_tree.schema.json`, agreed vocabulary list, structural signature spec, `src/types.py`, and project environment files that any team member can install and develop against.

---

#### ISSUE-001 — Freeze and commit the UIR JSON schema

- **Epic:** EPIC-01
- **Priority:** P0
- **Assignee:** Member 5 (joint session with Member 3)
- **Dependencies:** None — this is the root dependency of everything
- **Labels:** `contract`, `schema`, `blocker`

**Purpose:** The UIR schema is the single hard contract between Person 1 and Person 2. No other implementation work can be validated without it.

**Responsibility:** Define, write, and commit the full UIR JSON schema including every field, every allowed type label, every allowed semantic label, and the coordinate convention.

**Scope:**
- Define the complete set of allowed `type` values: `container`, `card`, `button`, `input`, `image`, `icon`, `navbar`, `sidebar`, `modal`, `tab`, `checkbox`, `radio`, `switch`, `avatar`, `divider`, `badge`, `link`, `text_block`.
- Define every node field: `id`, `type`, `bounds` (`x`, `y`, `w`, `h` in original pixel space), `text`, `child_text_nodes`, `style_hints` (`background`, `border`, `rounded`, `shadow`), `direction`, `gap`, `align`, `justify`, `parent_id`, `children`, `repeated_pattern` (`is_repeated`, `instance_count`, `suggested_component_name`, `variable_props`).
- Define allowed semantic labels: `direction` ∈ {`row`, `column`, `grid`, `none`}; `gap` ∈ {`none`, `small`, `medium`, `large`}; `align` ∈ {`start`, `center`, `end`, `stretch`}; `justify` ∈ {`start`, `center`, `end`, `between`}.
- Specify coordinate convention: original pixel space (not normalized), top-left origin.
- Specify file name: `ui_tree.json`.
- Write a JSON Schema (`ui_tree.schema.json`) that can be used for programmatic validation.
- Commit a hand-written example `ui_tree.json` for a login form (as the reference document describes: heading, two inputs, button).
- Assign a schema version number (start at `1.0.0`).

**Acceptance Criteria:**
- [ ] `ui_tree.schema.json` is committed and passes `jsonschema` validation against the hand-written example.
- [ ] The example `ui_tree.json` contains nodes covering every field and every allowed value in the schema.
- [ ] Every field has a documented type, allowed values, and whether it is required or nullable.
- [ ] The schema is confirmed by both Member 5 (Person 1 side) and Member 3 (Person 2 side) in writing (comment on the PR).
- [ ] No downstream Issue proceeds to implementation review until this Issue is merged.

---

#### ISSUE-002 — Define and commit the structural signature specification

- **Epic:** EPIC-01
- **Priority:** P0
- **Assignee:** Member 5 (joint with Member 3)
- **Dependencies:** ISSUE-001
- **Labels:** `contract`, `schema`, `blocker`

**Purpose:** Person 1's Stage 6 (pattern detection) and Person 2's `SubtreeHashTool` both compute structural signatures. If their encoding formats differ, `repeated_pattern` flags will silently disagree.

**Responsibility:** Write and commit a specification document describing the exact DFS type-label concatenation algorithm used by both pipelines.

**Scope:**
- Define the exact signature string format: depth-first traversal, child types joined by comma, container wrapping format (e.g., `container(image,text,text,button)`).
- Define edge cases: single child, empty children list, orphaned text nodes.
- Provide worked examples for each example in Section 6 of the architecture document (Card, MediaItem, ListItem, NavLink, FormField).
- Commit as `docs/structural_signature_spec.md`.

**Acceptance Criteria:**
- [ ] `docs/structural_signature_spec.md` is committed.
- [ ] At least five worked examples match those listed in the architecture document's heuristic lookup table.
- [ ] A Python function `compute_signature(node: dict) -> str` with 100% test coverage is committed alongside the spec and produces identical results to the worked examples.
- [ ] Member 5 and Member 3 both confirm the spec in writing (PR comment) before merging.

---

#### ISSUE-003 — Project scaffolding, environment, and shared type definitions

- **Epic:** EPIC-01
- **Priority:** P0
- **Assignee:** Member 5
- **Dependencies:** ISSUE-001
- **Labels:** `setup`, `infrastructure`

**Purpose:** Establish a consistent project structure, dependency management, and the shared Python type definitions (`src/types.py`) that all stages import.

**Responsibility:** Set up the final project directory structure, `requirements.txt`, `configs/config.py`, and `src/types.py` based on the already-scaffolded starter files but aligned with the frozen UIR schema.

**Scope:**
- Confirm and finalize the directory structure: `configs/`, `src/`, `notebooks/`, `tests/`, `outputs/`, `docs/`, `tools/` (for Node scripts).
- Update `src/types.py` dataclasses to include every field in the frozen UIR schema: add `text`, `child_text_nodes`, `direction`, `gap`, `align`, `justify`, `parent_id`, `children`, `repeated_pattern` fields to `UIElement`. Add `EnrichedUIElement`, `TextRegion`, and `UIRNode` classes.
- Update `configs/config.py` with all configuration constants: vocabulary, resolution caps, IoU thresholds, containment threshold, gap label thresholds, max retries.
- Ensure `requirements.txt` covers all Person 1 dependencies.
- Write a `README.md` installation section with step-by-step setup (virtual environment, `pip install -r requirements.txt`).

**Acceptance Criteria:**
- [ ] `python -c "from src.types import UIRNode, TextRegion, EnrichedUIElement"` succeeds.
- [ ] Every field from ISSUE-001's frozen schema has a corresponding field in `UIRNode`.
- [ ] `configs/config.py` contains constants for: `MAX_IMAGE_DIMENSION`, `PDF_DPI`, `DEFAULT_MODEL_NAME`, `USE_4BIT_QUANTIZATION`, `MAX_PARSE_RETRIES`, `UI_TYPE_VOCABULARY`, `CONTAINMENT_THRESHOLD`, `IOU_ASSIGNMENT_THRESHOLD`, `CONFIDENCE_THRESHOLD_OCR`.
- [ ] All existing starter files (`stage1_preprocessing.py`, `stage2a_vlm.py`, `pipeline.py`) import from the updated `src/types.py` without import errors.

---

### EPIC-02 — Stage 1: Input Preprocessing

**Objective:** Accept raw input files (PNG, JPEG, PDF, photograph), detect modality, apply modality-specific cleaning, resize to max 1280px, and return a normalized PNG with `resize_ratio` tracked.  
**Expected Outcome:** `preprocess_image()` correctly handles all three modalities, produces a normalized PNG, and returns a `Stage1Result` with accurate `resize_ratio`.

---

#### ISSUE-004 — PDF rendering and multi-format image loading

- **Epic:** EPIC-02
- **Priority:** P1
- **Assignee:** Member 1
- **Dependencies:** ISSUE-003
- **Labels:** `stage1`, `preprocessing`

**Purpose:** The pipeline must accept PDFs (rendered at 150 DPI) in addition to raster image formats.

**Responsibility:** Implement and test `load_pdf_as_image()` and the multi-format file loading entry path in `preprocess_image()`.

**Scope:**
- PDF rendering at 150 DPI using `pypdfium2` (primary), `fitz` (secondary), `pdf2image` (tertiary fallback).
- Standard image loading with EXIF orientation correction via `ImageOps.exif_transpose`.
- RGB normalization for all formats.
- Error handling for unsupported file types with a clear `ValueError`.
- Limit to first PDF page only (UQ-07 resolution).

**Acceptance Criteria:**
- [ ] A valid single-page PDF is rendered to a PIL Image at 150 DPI (verify via `image.size` proportional to 150 DPI scaling).
- [ ] A JPEG with camera EXIF rotation is correctly oriented after loading.
- [ ] A PNG loads without modification.
- [ ] An unsupported file type (e.g., `.svg`) raises `ValueError` with a descriptive message.
- [ ] All three PDF backends are tried in order; the test suite mocks each failure individually to verify fallback behavior.

---

#### ISSUE-005 — Modality detection (screenshot vs. sketch)

- **Epic:** EPIC-02
- **Priority:** P1
- **Assignee:** Member 1
- **Dependencies:** ISSUE-004
- **Labels:** `stage1`, `preprocessing`

**Purpose:** Modality-specific processing must only be applied when appropriate. Applying sketch cleaning to a screenshot degrades it.

**Responsibility:** Implement and test `detect_modality()`.

**Scope:**
- EXIF camera tag detection (`Make`, `Model`, `DateTimeOriginal`).
- Background uniformity patch sampling heuristic (flat ratio > 0.35 → screenshot).
- Color saturation / grayscale heuristic (color_diff < 8.0 → sketch).
- Wireframe classification decision (see UQ-08 — for v1, wireframe falls under `screenshot`; this must be documented in code as a known limitation).
- `forced_input_type` override parameter support.

**Acceptance Criteria:**
- [ ] A clean browser screenshot is classified as `screenshot`.
- [ ] A photograph of a hand-drawn sketch (provided as a test fixture) is classified as `sketch`.
- [ ] A low-fidelity grayscale wireframe PNG is classified as `screenshot` (wireframe = screenshot for v1).
- [ ] `forced_input_type="sketch"` overrides detection regardless of image content.
- [ ] Unit tests cover all three branches with actual test image fixtures committed to `tests/fixtures/`.

---

#### ISSUE-006 — Sketch cleaning and resolution capping

- **Epic:** EPIC-02
- **Priority:** P1
- **Assignee:** Member 1
- **Dependencies:** ISSUE-005
- **Labels:** `stage1`, `preprocessing`

**Purpose:** Sketch photographs have paper grain and shadows that impair VLM and OCR accuracy. Resolution capping ensures consistent downstream processing.

**Responsibility:** Implement and test `clean_sketch_image()` and `resize_image_capped()`.

**Scope:**
- CLAHE-based contrast enhancement (OpenCV path, `clipLimit=2.0`, `tileGridSize=(8,8)`).
- PIL autocontrast fallback when OpenCV is unavailable.
- Aspect-ratio-preserving resize with LANCZOS resampling.
- `resize_ratio` calculation: `new_longest_dim / original_longest_dim`.
- Images already within 1280px must pass through with `resize_ratio = 1.0`.

**Acceptance Criteria:**
- [ ] A 2000×1500px image is resized to 1280×960px; `resize_ratio` = `1280/2000 = 0.64`.
- [ ] A 640×480px image passes through unchanged with `resize_ratio = 1.0`.
- [ ] After `clean_sketch_image()`, a test sketch fixture has measurably higher mean local contrast (quantifiable via `np.std` on patches) compared to the original.
- [ ] `clean_sketch_image()` with OpenCV unavailable (mocked import failure) falls back to PIL autocontrast without raising an exception.
- [ ] The full `preprocess_image()` integration: a sketch photograph input produces a normalized PNG at the capped resolution with correct `Stage1Result` fields.

---

### EPIC-03 — Stage 2A: VLM Element Inference

**Objective:** Load Qwen2-VL-7B (4-bit quantized), construct the agreed 4-part prompt, run inference, extract and parse JSON with retry logic, validate bounding boxes, and return a clean `Stage2AResult`.  
**Expected Outcome:** `infer_elements()` returns a valid list of `UIElement` objects from a normalized PNG without crashing on parse failure.

---

#### ISSUE-007 — VLM prompt engineering and JSON extraction

- **Epic:** EPIC-03
- **Priority:** P1
- **Assignee:** Member 1
- **Dependencies:** ISSUE-003
- **Labels:** `stage2a`, `vlm`, `prompt-engineering`

**Purpose:** The 4-part prompt is Person 1's primary engineering artifact for structured VLM output. JSON extraction must handle the VLM's common failure modes (markdown fences, prose wrapping).

**Responsibility:** Implement and test `build_system_prompt()` and `extract_json_from_text()`.

**Scope:**
- 4-part prompt: (1) role instruction, (2) concrete JSON schema example, (3) agreed type vocabulary, (4) hard negative constraint ("output ONLY the raw JSON array").
- Image resolution injection into prompt.
- JSON extraction: direct `json.loads`, markdown fence stripping, regex fallback for outermost `[...]`.
- Wrapper/dict unwrapping: if model returns `{"elements": [...]}`, extract the list.

**Acceptance Criteria:**
- [ ] `build_system_prompt(640, 480)` returns a string containing all four prompt parts, the resolution, and the full vocabulary list.
- [ ] `extract_json_from_text('[{"id":"elem_0","type":"button"}]')` returns a list with one dict.
- [ ] `extract_json_from_text('` ``` `json\n[{"id":"elem_0"}]\n` ``` `')` strips the fence and returns the list.
- [ ] `extract_json_from_text('Here is the output: [{"id":"elem_0"}]')` extracts the array via regex.
- [ ] `extract_json_from_text('not json at all')` returns `None`.
- [ ] All cases above have unit tests.

---

#### ISSUE-008 — Qwen2-VL model loader with 4-bit quantization

- **Epic:** EPIC-03
- **Priority:** P1
- **Assignee:** Member 1
- **Dependencies:** ISSUE-007
- **Labels:** `stage2a`, `vlm`, `model-loading`

**Purpose:** The model must be loadable on hardware with ≤12GB VRAM using 4-bit BitsAndBytes quantization, and must fall back gracefully on CPU-only systems.

**Responsibility:** Implement and test `Qwen2VLInference.__init__()` and `load_model()`.

**Scope:**
- BitsAndBytes `BitsAndBytesConfig` with `nf4`, `bfloat16` compute dtype, double quant.
- CUDA path: 4-bit quantized model load with `device_map="auto"`.
- CPU fallback: `float32` dtype, no quantization.
- Lazy loading: model is not loaded until `load_model()` is explicitly called.
- Support for `model_name` override (for 2B fallback).

**Acceptance Criteria:**
- [ ] With a mocked `transformers` import, `Qwen2VLInference(use_4bit=False)` can be instantiated without errors on a CPU-only machine.
- [ ] `load_model()` is idempotent: calling it twice does not reload the model.
- [ ] The quantization config uses `nf4` quant type and `bfloat16` compute dtype (verified by inspecting the config object in tests).
- [ ] `model_name="Qwen/Qwen2-VL-2B-Instruct"` overrides the default.

---

#### ISSUE-009 — VLM inference, retry loop, and post-parse validation

- **Epic:** EPIC-03
- **Priority:** P1
- **Assignee:** Member 1
- **Dependencies:** ISSUE-007, ISSUE-008
- **Labels:** `stage2a`, `vlm`, `fault-tolerance`

**Purpose:** Inference must be fault-tolerant: JSON parse failures must trigger a corrective retry (max 2), and persistent failure must return a graceful empty result — not crash.

**Responsibility:** Implement and test `generate_response()`, the retry loop in `infer_elements()`, and `validate_and_filter_elements()`.

**Scope:**
- `generate_response()`: chat template formatting, `process_vision_info`, tensor to device, `model.generate` with `max_new_tokens=2048, temperature=0.1, do_sample=False`, output ID trimming.
- Retry loop: on parse failure, append error correction message; retry up to `MAX_PARSE_RETRIES`; return `Stage2AResult(status="failed")` on third failure.
- `validate_and_filter_elements()`: discard `x < 0`, `y < 0`, `w ≤ 1`, `h ≤ 1`, out-of-bounds; normalize out-of-vocabulary types to `container`.
- File-not-found guard.

**Acceptance Criteria:**
- [ ] With a mocked model that returns valid JSON on first attempt: `status == "success"`, correct element count.
- [ ] With a mocked model that returns invalid JSON twice then valid JSON on third attempt: `status == "success"`.
- [ ] With a mocked model that always returns invalid JSON: `status == "failed"`, `elements == []`, no exception raised.
- [ ] An element with `x=-5` is discarded.
- [ ] An element with `type="unknown_type"` is coerced to `type="container"`.
- [ ] An element with `x=100, w=1200` where `image_width=640` is discarded (beyond tolerance).
- [ ] `infer_elements("nonexistent.png")` returns `status == "failed"` with a file-not-found message.

---

### EPIC-04 — Stage 2B: OCR Text Extraction

**Objective:** Run PaddleOCR on the same normalized PNG as Stage 2A, extract text regions as `TextRegion` objects with axis-aligned bounding boxes and confidence scores, filtered at ≥ 0.6 confidence.  
**Expected Outcome:** `extract_text_regions()` returns a list of `TextRegion` objects from a normalized PNG without side effects on the VLM branch.

---

#### ISSUE-010 — PaddleOCR integration and polygon-to-AABB conversion

- **Epic:** EPIC-04
- **Priority:** P1
- **Assignee:** Member 2
- **Dependencies:** ISSUE-003
- **Labels:** `stage2b`, `ocr`

**Purpose:** PaddleOCR returns 4-point polygons; the UIR schema requires axis-aligned bounding boxes (AABB). Text below 0.6 confidence must be discarded.

**Responsibility:** Implement `extract_text_regions()` including PaddleOCR initialization, raw output parsing, polygon-to-AABB conversion, and confidence filtering.

**Scope:**
- PaddleOCR initialization (English model, angle classification on).
- Raw output parsing: iterate over `result[0]`, each item is `[[polygon_4pts], [text, confidence]]`.
- Polygon to AABB: `x = min(pts[:, 0])`, `y = min(pts[:, 1])`, `w = max(pts[:, 0]) - x`, `h = max(pts[:, 1]) - y`.
- Confidence threshold: discard regions with `confidence < 0.6`.
- Do not normalize or modify text content — exact string preservation.
- Return `List[TextRegion]` where `TextRegion` has `text: str`, `confidence: float`, `bounds: BoundingBox`.

**Acceptance Criteria:**
- [ ] Given a test PNG with two clearly rendered text strings, both are returned as `TextRegion` objects with exact text matches.
- [ ] A `TextRegion` with mocked `confidence=0.55` is excluded from results.
- [ ] A `TextRegion` with mocked `confidence=0.6` is included.
- [ ] The AABB conversion for a rotated polygon correctly returns the min/max envelope.
- [ ] Text content is not uppercased, lowercased, corrected, or modified in any way.

---

#### ISSUE-011 — Stage 2B unit tests and integration with Stage 1 output

- **Epic:** EPIC-04
- **Priority:** P2
- **Assignee:** Member 2
- **Dependencies:** ISSUE-010, ISSUE-006
- **Labels:** `stage2b`, `ocr`, `testing`

**Purpose:** Verify Stage 2B operates correctly on actual Stage 1 normalized outputs and that it is truly independent of Stage 2A.

**Responsibility:** Write integration tests that chain Stage 1 → Stage 2B and verify correct text extraction.

**Scope:**
- Integration test: `preprocess_image()` → `extract_text_regions()` on test fixture images.
- Verify that Stage 2B reads from the same normalized PNG path as Stage 2A without any shared state.

**Acceptance Criteria:**
- [ ] Integration test with a screenshot fixture containing the word "Login" produces a `TextRegion` with `text == "Login"`.
- [ ] Stage 2A and Stage 2B can be called in either order on the same `Stage1Result` with identical results each time (statelessness).
- [ ] No test requires Stage 2A to have run before Stage 2B.

---

### EPIC-05 — Stage 3: Spatial Fusion

**Objective:** Merge the VLM element list and OCR text region list into a single enriched element list by IoU-based assignment, with explicit rules for single-match, multi-region, ambiguous, and unmatched cases.  
**Expected Outcome:** `fuse_elements()` returns a list of `EnrichedUIElement` objects plus an `orphaned_text_nodes` list.

---

#### ISSUE-012 — IoU matrix computation and primary assignment logic

- **Epic:** EPIC-05
- **Priority:** P1
- **Assignee:** Member 2
- **Dependencies:** ISSUE-003, ISSUE-009, ISSUE-010
- **Labels:** `stage3`, `spatial-fusion`

**Purpose:** The IoU-based bipartite matching between VLM elements and OCR regions is the core algorithm of spatial fusion.

**Responsibility:** Implement the pairwise IoU matrix and the four assignment rules.

**Scope:**
- Pairwise IoU calculation between all VLM elements and all OCR text regions (n×m matrix).
- Rule 1: Single match (IoU > 0.5 with exactly one element) → assign as `text` field.
- Rule 2: Multiple OCR regions matched to one element → if Y center variance < 5px: concatenate left-to-right; otherwise: create `child_text_nodes` ordered by Y then X.
- Rule 3: Ambiguous match (IoU > 0.5 with two or more elements) → assign to highest IoU element; if top two within 0.05, assign to smaller element (by area).
- Rule 4: No match (no IoU > 0.3) → OCR region becomes orphaned text node with `type: "text"`.

**Acceptance Criteria:**
- [ ] A button VLM element that fully contains one OCR region (IoU ≈ 0.9) has its `text` set to the OCR region's string.
- [ ] A card VLM element containing a title (y=100) and description (y=140) produces two `child_text_nodes` ordered by Y, with no concatenation.
- [ ] A card VLM element containing "Sign Up" (y=100) and "Now" (y=102, Y diff < 5px) has `text = "Sign Up Now"`.
- [ ] An OCR region with IoU > 0.5 to two overlapping VLM elements is assigned to the smaller element when the top two IoUs are within 0.05.
- [ ] An OCR region with max IoU = 0.1 (below 0.3) appears in `orphaned_text_nodes`.
- [ ] All rules are covered by unit tests with synthetic bounding box data (no real model required).

---

#### ISSUE-013 — Spatial fusion integration and EnrichedUIElement serialization

- **Epic:** EPIC-05
- **Priority:** P2
- **Assignee:** Member 2
- **Dependencies:** ISSUE-012
- **Labels:** `stage3`, `spatial-fusion`, `serialization`

**Scope:**
- `EnrichedUIElement` dataclass: inherits all `UIElement` fields plus `text: Optional[str]`, `child_text_nodes: List[dict]`.
- `to_dict()` serialization that matches the UIR schema field names.
- `run_stage3(stage2a_result, stage2b_result) -> Tuple[List[EnrichedUIElement], List[TextRegion]]`.

**Acceptance Criteria:**
- [ ] `EnrichedUIElement.to_dict()` produces a dict with all required UIR fields including `text` and `child_text_nodes`.
- [ ] `run_stage3()` accepts `Stage2AResult` and `List[TextRegion]` and returns enriched elements + orphans.
- [ ] Integration test: a `Stage2AResult` with 3 elements and a `Stage2BResult` with 5 regions produces the correct assignment (verified against hand-computed expected output).

---

### EPIC-06 — Stage 4: Containment Detection

**Objective:** Convert the flat enriched element list into a tree by assigning `parent_id` and `children` using bounding box containment geometry. Detect and resolve cycles.

---

#### ISSUE-014 — Containment algorithm and tree construction

- **Epic:** EPIC-06
- **Priority:** P1
- **Assignee:** Member 1
- **Dependencies:** ISSUE-013
- **Labels:** `stage4`, `containment`

**Responsibility:** Implement the containment detection algorithm.

**Scope:**
- Sort all elements by area descending.
- For each element (processing smallest first): find all candidates where `intersection(E, candidate) / E.area > CONTAINMENT_THRESHOLD`. Assign parent = smallest qualifying candidate.
- Elements with no valid parent are roots.
- Assign `parent_id` and populate `children` lists.
- Include orphaned text nodes from Stage 3 in the input.

**Acceptance Criteria:**
- [ ] A button (100×40px) fully inside a card (300×200px) which is inside a container (600×400px): button's parent is card, card's parent is container.
- [ ] Two non-overlapping buttons inside the same card are siblings (same parent, not parent-child).
- [ ] An element that is 50% inside a container fails the 0.8 threshold and is not assigned as the container's child.
- [ ] Orphaned OCR text nodes from Stage 3 participate in containment assignment.
- [ ] A valid UI with one navbar, one main content area, and several cards produces 1–2 root nodes.

---

#### ISSUE-015 — Cycle detection, resolution, and overlapping sibling handling

- **Epic:** EPIC-06
- **Priority:** P1
- **Assignee:** Member 1
- **Dependencies:** ISSUE-014
- **Labels:** `stage4`, `containment`, `edge-cases`

**Responsibility:** Implement cycle detection (DFS) and the overlapping non-containing element rule.

**Scope:**
- DFS cycle detection after tree construction.
- Cycle resolution: demote the deeper node to sibling of the cycle participant under their shared ancestor.
- Overlapping non-containing elements (IoU > 0, containment ratio < 0.5 for both): classify as siblings under same parent.
- Log all cycle resolutions.

**Acceptance Criteria:**
- [ ] Two elements with identical bounding boxes (cycle scenario) are resolved to siblings without raising an exception.
- [ ] After cycle resolution, a DFS traversal of the resulting tree completes without infinite loop.
- [ ] Two overlapping elements where neither contains the other by 80% are assigned as siblings, not parent-child.
- [ ] A cycle resolution event is logged with the implicated element IDs.

---

#### ISSUE-016 — Containment threshold calibration script (RICO)

- **Epic:** EPIC-06
- **Priority:** P2
- **Assignee:** Member 1
- **Dependencies:** ISSUE-014
- **Labels:** `stage4`, `evaluation`, `calibration`

**Responsibility:** Implement the calibration script and document the chosen threshold.

**Scope:**
- Script loads RICO annotation files and corresponding element lists.
- Grid search over [0.70, 0.75, 0.80, 0.85, 0.90].
- Computes tree edit distance vs. RICO ground truth for each threshold.
- Update `configs/config.py` with the chosen `CONTAINMENT_THRESHOLD` value.

**Acceptance Criteria:**
- [ ] Script runs against at least 50 RICO samples without error.
- [ ] Script outputs a table of threshold values vs. mean tree edit distance.
- [ ] The best threshold is committed to `configs/config.py` with a comment citing the calibration result.

---

### EPIC-07 — Stage 5: Layout Annotation

**Objective:** For each parent node with ≥ 2 children, determine `direction`, `gap`, `align`, and `justify` using statistical analysis of child bounding boxes. Output semantic labels, not pixel values.

---

#### ISSUE-017 — Row/column/grid direction classifier

- **Epic:** EPIC-07
- **Priority:** P1
- **Assignee:** Member 1
- **Dependencies:** ISSUE-014
- **Labels:** `stage5`, `layout`

**Responsibility:** Implement the direction classification sub-module.

**Scope:**
- `cv_y = std(center_y) / mean(height)` across children; if < 0.3: `direction = "row"`.
- `cv_x = std(center_x) / mean(width)` across children; if < 0.3: `direction = "column"`.
- Both low: `direction = "row"`.
- Both high and child count has clean 2D factorization (4, 6, 9): `direction = "grid"`.
- Single child: `direction = "none"`.

**Acceptance Criteria:**
- [ ] Three buttons arranged horizontally (same Y ± 2px) → `direction = "row"`.
- [ ] Three form fields stacked vertically (same X ± 2px) → `direction = "column"`.
- [ ] A 2×3 grid of cards (6 children) → `direction = "grid"`.
- [ ] A container with one child → `direction = "none"`.
- [ ] All cases verified with unit tests using synthetic element positions.

---

#### ISSUE-018 — Gap estimator, alignment classifier, and justify classifier

- **Epic:** EPIC-07
- **Priority:** P1
- **Assignee:** Member 1
- **Dependencies:** ISSUE-017
- **Labels:** `stage5`, `layout`

**Responsibility:** Implement gap estimation, alignment classification, and justify classification.

**Scope:**
- **Gap:** Sort children by primary axis. Measure trailing-to-leading edge distance for each consecutive pair. Average all gaps. Map: 0–4px → `"none"`, 4–12px → `"small"`, 12–28px → `"medium"`, 28+px → `"large"` (pending UQ-04 calibration).
- **Align (cross-axis):** Compute variance of top edges, center coordinates, bottom edges. Assign lowest-variance axis: top → `"start"`, center → `"center"`, bottom → `"end"`. Neither low → `"stretch"`.
- **Justify (main-axis):** Measure std dev of gaps. Equal gaps → `"between"`. Clustered at start → `"start"`. Clustered at end → `"end"`. Centered → `"center"`.
- Full DFS pass integrating all four layout properties.

**Acceptance Criteria:**
- [ ] Five buttons with 6px gaps → `gap = "small"`.
- [ ] Five buttons with 24px gaps → `gap = "large"`.
- [ ] Three buttons with identical top edges → `align = "start"`.
- [ ] Three buttons with identical centers → `align = "center"`.
- [ ] Three buttons equally spaced between start and end → `justify = "between"`.
- [ ] All cases verified with unit tests using synthetic element positions.

---

#### ISSUE-019 — Gap label calibration script (RICO)

- **Epic:** EPIC-07
- **Priority:** P2
- **Assignee:** Member 1
- **Dependencies:** ISSUE-018
- **Labels:** `stage5`, `calibration`

**Scope:**
- Measure actual gap distributions from RICO layout annotations.
- Identify natural break points in the gap histogram.
- Update `configs/config.py` with calibrated thresholds.

**Acceptance Criteria:**
- [ ] Script runs over at least 100 RICO samples and produces a gap distribution histogram.
- [ ] Updated thresholds are committed to `configs/config.py` with calibration evidence.

---

### EPIC-08 — Stage 6: Pattern / Subtree Detection

**Objective:** Identify repeated structural subtrees and annotate them with `is_repeated`, `instance_count`, `suggested_component_name`, and `variable_props`.

---

#### ISSUE-020 — Structural signature computation and repeated pattern grouping

- **Epic:** EPIC-08
- **Priority:** P1
- **Assignee:** Member 2
- **Dependencies:** ISSUE-002, ISSUE-014
- **Labels:** `stage6`, `pattern-detection`

**Responsibility:** Implement `compute_signature()` integration into pattern grouping and `detect_patterns()`.

**Scope:**
- Import `compute_signature` from ISSUE-002's implementation.
- DFS traversal of the annotated tree; group same-level siblings by signature.
- Groups with ≥ 2 members: mark `is_repeated = True`, set `instance_count`.
- Compare corresponding leaf nodes across group members: nodes with differing `text` or `style_hints` → add to `variable_props`.
- Assign `suggested_component_name` from the lookup table (Card, MediaItem, ListItem, NavLink, FormField).

**Acceptance Criteria:**
- [ ] Three sibling containers each with `[image, text, text, button]` children → all three marked `is_repeated=True`, `instance_count=3`, `suggested_component_name="Card"`.
- [ ] `variable_props` for a Card where only the button text differs across instances: contains the button text field path.
- [ ] Non-repeated containers are not marked.
- [ ] `compute_signature()` output matches the worked examples from ISSUE-002's spec.

---

#### ISSUE-021 — Pattern detection edge cases and integration test

- **Epic:** EPIC-08
- **Priority:** P2
- **Assignee:** Member 2
- **Dependencies:** ISSUE-020
- **Labels:** `stage6`, `pattern-detection`, `testing`

**Scope:**
- Edge case: single child with a given signature → not flagged as repeated.
- Edge case: nested repeated patterns (cards inside grid of sections) → both levels annotated independently.
- Integration test: Stage 1 → 2A → 2B → 3 → 4 → 5 → 6 on a test fixture with known repeated patterns.

**Acceptance Criteria:**
- [ ] A container with a single child matching a "Card" signature is NOT marked `is_repeated`.
- [ ] A grid of sections where each section contains repeated cards: both section-level and card-level repetition are annotated.
- [ ] Integration test with a provided fixture produces at least one correctly identified repeated pattern group.

---

### EPIC-09 — Stage 7: UIR Validation & Serialization

**Objective:** Validate the completed annotated tree against the frozen schema, scale coordinates back from normalized to original pixel space, and write `ui_tree.json`.

---

#### ISSUE-022 — UIR validation logic (hard and soft checks)

- **Epic:** EPIC-09
- **Priority:** P1
- **Assignee:** Member 2
- **Dependencies:** ISSUE-001, ISSUE-014, ISSUE-017, ISSUE-020
- **Labels:** `stage7`, `validation`

**Scope (hard checks — block serialization):**
- Every node has all required schema fields.
- All `bounds` are within original image dimensions.
- Exactly one root node exists.
- Tree is acyclic (DFS).
- All `text` fields are string or null.
- All `direction` values are in `{"row", "column", "grid", "none"}`.

**Scope (soft checks — log and continue):**
- `type` values not in agreed vocabulary → replace with `"unknown"`, log.

**Acceptance Criteria:**
- [ ] A tree with a missing `bounds` field on any node → hard failure, `serialize_uir()` raises `ValidationError` with the specific node ID and missing field.
- [ ] A tree with one root node and all valid fields → validation passes.
- [ ] A tree with zero root nodes → hard failure.
- [ ] A tree with two root nodes → hard failure.
- [ ] A node with `type="unsupported_type"` → soft failure: type replaced with `"unknown"`, warning logged, serialization continues.
- [ ] All 7 validation checks have dedicated unit tests.

---

#### ISSUE-023 — Coordinate back-scaling and JSON serialization

- **Epic:** EPIC-09
- **Priority:** P1
- **Assignee:** Member 2
- **Dependencies:** ISSUE-022
- **Labels:** `stage7`, `serialization`

**Scope:**
- For every `bounds`: `x_original = x_normalized / resize_ratio`, same for `y`, `w`, `h`.
- Write `ui_tree.json` to the specified output directory.
- JSON must validate against `ui_tree.schema.json` (run `jsonschema` validation as part of serialization).
- Return both the output file path and a `ValidationReport` object.

**Acceptance Criteria:**
- [ ] A node with `bounds.x = 320` from a normalized image with `resize_ratio = 0.5` → serialized as `bounds.x = 640`.
- [ ] A node with `resize_ratio = 1.0` → `bounds` values unchanged.
- [ ] The output `ui_tree.json` passes `jsonschema` validation against `ui_tree.schema.json`.
- [ ] The output file is UTF-8 encoded, indented JSON.

---

#### ISSUE-024 — Debug overlay visualization

- **Epic:** EPIC-09
- **Priority:** P3
- **Assignee:** Member 2
- **Dependencies:** ISSUE-023
- **Labels:** `stage7`, `debugging`

**Scope:**
- Draw original-pixel-space bounding boxes on the original image.
- Label each box with element `id` and `type`.
- Write as `debug_overlay.png` alongside `ui_tree.json`.
- Disabled in production; enabled via `save_debug_image=True` flag.

**Acceptance Criteria:**
- [ ] With `save_debug_image=True`: `debug_overlay.png` is written next to `ui_tree.json`.
- [ ] With `save_debug_image=False`: no PNG is written.
- [ ] Bounding boxes are drawn in original pixel space (verify that box dimensions ≈ `normalized_dim / resize_ratio`).

---

### EPIC-10 — Person 1 Evaluation Harness

---

#### ISSUE-025 — IoU evaluation script for Stage 2A element detection

- **Epic:** EPIC-10
- **Priority:** P2
- **Assignee:** Member 1
- **Dependencies:** ISSUE-009
- **Labels:** `evaluation`, `person1`

**Scope:**
- Load RICO annotations and run Stage 2A on corresponding images.
- Compute mean IoU (mIoU) between predicted bounding boxes and ground truth.
- Report per-type IoU breakdown. Output results to `eval_results/stage2a_iou.json`.

**Acceptance Criteria:**
- [ ] Script runs over at least 100 RICO test samples without error.
- [ ] Output JSON contains `mean_iou`, `per_type_iou`, and `sample_count`.
- [ ] At least one baseline mIoU number is documented in `docs/evaluation_results.md`.

---

#### ISSUE-026 — Tree edit distance evaluation script for Stage 4–6 hierarchy

- **Epic:** EPIC-10
- **Priority:** P2
- **Assignee:** Member 1
- **Dependencies:** ISSUE-016, ISSUE-021
- **Labels:** `evaluation`, `person1`

**Scope:**
- Load RICO hierarchy annotations. Run Stage 1 → 2A → 2B → 3 → 4 → 5 → 6 → 7.
- Compute tree edit distance between predicted UIR tree and RICO ground truth.

**Acceptance Criteria:**
- [ ] Script runs over at least 50 RICO samples.
- [ ] Output JSON contains `mean_ted`, `sample_count`.
- [ ] Result is documented in `docs/evaluation_results.md`.

---

### EPIC-11 — Kaggle Fine-Tuning Notebook

---

#### ISSUE-027 — Kaggle QLoRA fine-tuning notebook (Qwen2-VL)

- **Epic:** EPIC-11
- **Priority:** P2
- **Assignee:** Member 3
- **Dependencies:** ISSUE-007
- **Labels:** `kaggle`, `fine-tuning`, `vlm`

**Scope:**
- Complete notebook with 9 sections: package install, GPU check, config/vocab, 4-bit model load + LoRA attach (`r=16`, `lora_alpha=32`, target modules `["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"]`), dataset loading (dummy + `/kaggle/input/` path), `UICollator` multi-modal batch collation, `TrainingArguments`+`Trainer` with `paged_adamw_8bit`, adapter saving, inference.
- Simple code style: no advanced Python patterns, plain loops, clear markdown documentation.

**Acceptance Criteria:**
- [ ] Running all cells sequentially on a Kaggle T4 notebook with the dummy dataset completes without error.
- [ ] `model.print_trainable_parameters()` shows < 5% trainable parameters.
- [ ] The inference section produces a JSON array string as output.
- [ ] Adapter is saved to `OUTPUT_DIR` (verified by checking file existence at end of notebook).

---

### EPIC-12 — Person 2: Ingestion & Componentization

---

#### ISSUE-028 — IngestionAgent: UIR schema validation

- **Epic:** EPIC-12
- **Priority:** P1
- **Assignee:** Member 3
- **Dependencies:** ISSUE-001
- **Labels:** `person2`, `ingestion`, `adk`

**Scope:**
- Read `ui_tree.json` from path argument. Validate against `ui_tree.schema.json`.
- Fail with structured error report (node ID, field, violation) on schema violations.
- Load validated UIR into ADK session state. ADK Custom Agent (no LLM).

**Acceptance Criteria:**
- [ ] A valid `ui_tree.json` passes validation and is stored in session state.
- [ ] A UIR missing the `bounds` field on any node produces a structured error message naming the node ID and field.
- [ ] A UIR with an invalid `direction` value produces an error naming the offending node.
- [ ] `IngestionAgent` exits with ADK `ErrorEvent` on hard failures.

---

#### ISSUE-029 — SubtreeHashTool and ComponentizationAgent

- **Epic:** EPIC-12
- **Priority:** P1
- **Assignee:** Member 3
- **Dependencies:** ISSUE-002, ISSUE-028
- **Labels:** `person2`, `componentization`, `adk`

**Scope:**
- **SubtreeHashTool (FunctionTool):** Recomputes structural signatures using shared `compute_signature()` from ISSUE-002. Compares against `is_repeated` flags. Logs discrepancies. Does NOT modify UIR.
- **ComponentizationAgent (LlmAgent):** For each verified repeated pattern: confirm/refine `suggested_component_name`, identify `variable_props`. Use vLLM guided decoding for JSON output.

**Acceptance Criteria:**
- [ ] `SubtreeHashTool` correctly re-verifies the three Card instances from ISSUE-020's test case.
- [ ] A discrepancy between Person 1's flag and the re-computed hash is logged with node IDs.
- [ ] `ComponentizationAgent` produces a component name and prop list for each verified repeated pattern.
- [ ] The agent does not crash if `is_repeated` flags are absent.

---

### EPIC-13 — Person 2: RAG Layer

---

#### ISSUE-030 — ChromaDB setup and pattern corpus ingestion

- **Epic:** EPIC-13
- **Priority:** P2
- **Assignee:** Member 3
- **Dependencies:** ISSUE-001
- **Labels:** `person2`, `rag`, `chromadb`

**Scope:**
- Local ChromaDB instance (persistent, file-backed).
- Pattern corpus: curated JSX+Tailwind component patterns (Markdown files with structured frontmatter).
- Ingestion script: embeds descriptions using Qwen3-Embedding-8B, inserts into ChromaDB.
- Initial coverage: navbar, card, form field, button, modal, hero section, list item, media item.

**Acceptance Criteria:**
- [ ] Running the ingestion script populates ChromaDB with at least 20 initial patterns.
- [ ] ChromaDB persists to disk between Python sessions.
- [ ] Each stored document has metadata: `component_type`, `tailwind_classes`, `source_file`.

---

#### ISSUE-031 — Qwen3-Embedding-8B integration and RAGRetrievalTool

- **Epic:** EPIC-13
- **Priority:** P2
- **Assignee:** Member 3
- **Dependencies:** ISSUE-030
- **Labels:** `person2`, `rag`, `embedding`

**Scope:**
- `Qwen3EmbeddingClient`: loads or calls Qwen3-Embedding-8B to produce query embeddings.
- `RAGRetrievalTool(query: str, top_k: int = 3) -> List[dict]`: embeds query, queries ChromaDB, returns top-k patterns.
- Retrieved patterns formatted as labeled few-shot examples ("here is a similar working component — adapt it").
- ADK FunctionTool wrapper.

**Acceptance Criteria:**
- [ ] Query `"primary action button with rounded corners and blue background"` returns at least one result with `component_type == "button"`.
- [ ] `top_k=3` returns exactly 3 results (or fewer if corpus has < 3).
- [ ] Retrieved patterns include the JSX code body, not just metadata.

---

### EPIC-14 — Person 2: Code Generation Pipeline

---

#### ISSUE-032 — vLLM server setup and OpenAI-compatible endpoint configuration

- **Epic:** EPIC-14
- **Priority:** P1
- **Assignee:** Member 3
- **Dependencies:** None
- **Labels:** `person2`, `codegen`, `vllm`, `infrastructure`

**Scope:**
- Confirm vLLM serving `Qwen/Qwen2.5-Coder-7B-Instruct-AWQ` on Kaggle.
- Confirm model does NOT use tool-calling for code output (outputs text only) — per architecture §7 gotcha.
- Confirm vLLM guided JSON decoding works for structured output.
- Document in `docs/vllm_setup.md`.
- Local dev alternative: Ollama with Qwen2.5-Coder-1.5B GGUF.

**Acceptance Criteria:**
- [ ] A Python `requests` call to the vLLM endpoint returns a code generation response within 30 seconds (Kaggle T4).
- [ ] The model does not emit `tool_calls` in the response when prompted to generate JSX code.
- [ ] A prompt requesting structured JSON returns valid JSON via guided decoding.
- [ ] `docs/vllm_setup.md` documents: startup command, model ID, quantization flag, endpoint URL, confirmed gotcha behavior.

---

#### ISSUE-033 — CodeGenAgent: prompt assembly with RAG and UIR context

- **Epic:** EPIC-14
- **Priority:** P1
- **Assignee:** Member 3
- **Dependencies:** ISSUE-029, ISSUE-031, ISSUE-032
- **Labels:** `person2`, `codegen`, `adk`

**Scope:**
- Input: UIR subtree (JSON), parent component code (string or null), list of RAG-retrieved patterns.
- Prompt: (1) role + task, (2) UIR subtree as JSON, (3) parent code context, (4) RAG examples as few-shot patterns, (5) output instructions.
- Output: JSX string (text only, no tool-calls).
- Qwen2.5-Coder-7B via vLLM OpenAI-compatible API.

**Acceptance Criteria:**
- [ ] Given a button UIR node (`type="button"`, `text="Sign Up"`, `style_hints.background="#2563eb"`, `style_hints.rounded="md"`), the agent produces JSX with a `<button>` element and appropriate Tailwind classes.
- [ ] Generated code includes text content exactly matching the UIR `text` field.
- [ ] The agent does not add prose explanation before or after the JSX.
- [ ] Prompt assembly test verifies UIR, parent code, and RAG examples are all present in the final prompt string.

---

#### ISSUE-034 — Fan-out/fan-in parallel code generation over UIR tree

- **Epic:** EPIC-14
- **Priority:** P1
- **Assignee:** Member 3
- **Dependencies:** ISSUE-033
- **Labels:** `person2`, `codegen`, `adk`, `parallel`

**Scope:**
- Siblings at the same UIR tree depth dispatched to `CodeGenAgent` via ADK `ParallelAgent`.
- `FileAssemblyTool` merges generated sibling code into the parent's context before next level.
- Tree traversal: top-down (generate parent shell first, then children with parent code as context).
- Session state: generated code for each node stored by `node_id`.

**Acceptance Criteria:**
- [ ] A UIR tree with 3 sibling card components dispatches 3 concurrent `CodeGenAgent` calls.
- [ ] Each `CodeGenAgent` call receives the parent container's already-generated JSX as context.
- [ ] The final assembled `App.jsx` imports all generated components.

---

### EPIC-15 — Person 2: Syntax Validation & Repair Loop

---

#### ISSUE-035 — JSXValidatorAgent: Babel parsing and error classification

- **Epic:** EPIC-15
- **Priority:** P1
- **Assignee:** Member 4
- **Dependencies:** ISSUE-034, ISSUE-037
- **Labels:** `person2`, `validation`, `adk`

**Scope:**
- Calls `babel_validate.js` as a subprocess via `asyncio.create_subprocess_exec`.
- Parses JSON error list from stdout.
- Classifies errors: auto-fixable (missing semicolons, unclosed tags) vs. needs-model (structural issues).
- Applies auto-fixes directly (Python string manipulation).
- Returns to ADK `LoopAgent`: either all files pass, or `RepairAgent` is invoked.

**Acceptance Criteria:**
- [ ] JSX with a missing closing tag → classified as "needs-model" (passed to `RepairAgent`).
- [ ] JSX with a trailing comma in props → classified as "auto-fixable" and corrected without model invocation.
- [ ] JSX with no errors → loop exits immediately.
- [ ] A file that fails all repair attempts exits the loop with `status="syntax_failed"`.

---

#### ISSUE-036 — RepairAgent: LLM-based JSX repair

- **Epic:** EPIC-15
- **Priority:** P1
- **Assignee:** Member 4
- **Dependencies:** ISSUE-035, ISSUE-032
- **Labels:** `person2`, `validation`, `adk`

**Scope:**
- Input: failing JSX file content + Babel error list (line/col/message).
- Prompt: "Fix ONLY the errors listed. Output only the corrected JSX file, no prose."
- Output: corrected JSX string (text only, no tool-calls).
- File is rewritten with corrected content. `JSXValidatorAgent` re-validates.

**Acceptance Criteria:**
- [ ] Given a JSX file with an unclosed JSX tag and the exact Babel error message, `RepairAgent` produces valid JSX (verified by Babel re-parse).
- [ ] `RepairAgent` does not modify lines not implicated by the error.
- [ ] After repair, `JSXValidatorAgent` re-runs and confirms the fix.

---

### EPIC-16 — Node Toolchain (Babel / Vite / Playwright)

---

#### ISSUE-037 — `babel_validate.js`: JSX parser with errorRecovery

- **Epic:** EPIC-16
- **Priority:** P1
- **Assignee:** Member 4
- **Dependencies:** None
- **Labels:** `toolchain`, `node`, `babel`

**Scope:**
- Input: JSON `{"files": ["path/to/file.jsx"]}` from stdin.
- Uses `@babel/parser` with `{plugins: ["jsx"], errorRecovery: true}`.
- Output: JSON `{"results": [{"file": "...", "errors": [{"line": n, "col": n, "message": "..."}]}]}`.
- Exit code 0 if no errors; exit code 1 if any errors.

**Acceptance Criteria:**
- [ ] Valid JSX file: stdout contains `{"errors": []}`, exit code 0.
- [ ] JSX file with two errors: stdout contains both errors with correct line/col, exit code 1.
- [ ] `errorRecovery: true` ensures all errors are reported, not just the first.
- [ ] A JSON parsing failure of stdin exits with exit code 2 and a descriptive error message to stderr.

---

#### ISSUE-038 — `vite_render.mjs`: Vite dev server boot and URL return

- **Epic:** EPIC-16
- **Priority:** P1
- **Assignee:** Member 4
- **Dependencies:** None
- **Labels:** `toolchain`, `node`, `vite`

**Scope:**
- Input: JSON `{"project_dir": "path/to/react/project"}` from stdin.
- Starts Vite dev server in given directory, waits for health check.
- Output: JSON `{"url": "http://localhost:5173"}` on success; `{"error": "...", "stderr": "..."}` on failure.
- Server process cleanly terminated when parent exits.

**Acceptance Criteria:**
- [ ] A valid React+Vite project dir: Vite starts, URL is returned, server is reachable via HTTP.
- [ ] A project with a compile error: stderr is captured and returned, exit code 1.
- [ ] No zombie Vite processes after parent process exits.

---

#### ISSUE-039 — `playwright_shoot.mjs`: headless screenshot at specified viewport

- **Epic:** EPIC-16
- **Priority:** P1
- **Assignee:** Member 4
- **Dependencies:** ISSUE-038
- **Labels:** `toolchain`, `node`, `playwright`

**Scope:**
- Input: JSON `{"url": "...", "viewport_width": W, "viewport_height": H, "output_path": "..."}`.
- Playwright chromium headless. Navigates to URL, waits for `networkidle`.
- Screenshots at specified viewport. Output: JSON `{"screenshot_path": "..."}`.
- Timeout error: JSON `{"error": "timeout"}`, no PNG written, exit code 1.

**Acceptance Criteria:**
- [ ] A running Vite dev server → screenshot PNG written to specified path.
- [ ] Screenshot PNG dimensions match the specified viewport.
- [ ] `networkidle` wait ensures React hydration is complete before screenshot.
- [ ] A URL that never loads → timeout error in JSON, no PNG written, exit code 1.

---

### EPIC-17 — Person 2: Visual Comparison & Correction Loop

---

#### ISSUE-040 — BrowserRenderAgent: Vite + Playwright orchestration

- **Epic:** EPIC-17
- **Priority:** P1
- **Assignee:** Member 4
- **Dependencies:** ISSUE-038, ISSUE-039, ISSUE-035
- **Labels:** `person2`, `render`, `adk`

**Scope:**
- Called only after `JSXValidatorAgent` confirms no syntax errors.
- Calls `vite_render.mjs` → gets URL. Calls `playwright_shoot.mjs` → gets screenshot.
- On compile failure: captures Vite stderr, stores as error artifact, exits `status="render_failed"`.
- Saves screenshot as ADK Artifact (by ID/version).

**Acceptance Criteria:**
- [ ] After valid JSX: `BrowserRenderAgent` produces a screenshot PNG stored as ADK Artifact.
- [ ] Vite compile failure: `status="render_failed"` with stderr content in session state.
- [ ] Screenshot is taken at the same resolution as the original input image.

---

#### ISSUE-041 — VisualComparisonAgent: 5-metric ensemble computation

- **Epic:** EPIC-17
- **Priority:** P1
- **Assignee:** Member 4
- **Dependencies:** ISSUE-040
- **Labels:** `person2`, `visual-comparison`, `adk`

**Scope:**
- **CW-SSIM:** complex-wavelet SSIM, runs every iteration.
- **Bounding-box/text/color element matching:** pairs via Jonker-Volgenant assignment, diffs per pair, produces per-node discrepancy mapped to UIR node IDs. Runs every iteration.
- **LPIPS:** AlexNet/VGG backbone, produces spatial map. Runs every iteration.
- **CLIP:** ViT forward pass for global semantic sanity. Runs every iteration.
- **DreamSim:** CLIP+OpenCLIP+DINO embeddings. Runs ONLY on the accept/reject decision.
- Output: `CompositeScore` with weighted sum + raw per-metric scores + spatial diff mapped to UIR node IDs.
- Initial equal weights; to be calibrated against 20–30 hand-labeled examples per UQ-05.

**Acceptance Criteria:**
- [ ] Given two identical images: composite score is at maximum value.
- [ ] Given two completely different images: composite score is significantly below threshold.
- [ ] Spatial diff output correctly maps high-discrepancy regions to UIR node IDs.
- [ ] DreamSim is called only once per loop iteration (at accept/reject check), not for every intermediate comparison.
- [ ] Raw per-metric scores are stored separately from the composite score.

---

#### ISSUE-042 — CorrectionPlannerAgent and TargetedCorrectionAgent

- **Epic:** EPIC-17
- **Priority:** P1
- **Assignee:** Member 4
- **Dependencies:** ISSUE-041
- **Labels:** `person2`, `correction`, `adk`

**Scope:**
- **CorrectionPlannerAgent (LlmAgent):** Reads composite score + spatial diff. Decides `accept` or `revise`. If `revise`: writes targeted brief naming specific UIR node IDs. Accept/reject threshold check by Python `exit_condition` callback.
- **TargetedCorrectionAgent (LlmAgent, Qwen2.5-Coder):** Rewrites ONLY the components named in the brief.
- Best candidate tracking: after each iteration, compare `CompositeScore` to `best_score` in session state.
- Loop exits on: score ≥ threshold (Python `exit_condition`) OR `max_iterations` reached.

**Acceptance Criteria:**
- [ ] `accept` decision when composite score ≥ threshold: loop exits, `best_candidate` in session state is the accepted version.
- [ ] `revise` decision: correction brief names specific UIR node IDs, not generic instructions.
- [ ] `TargetedCorrectionAgent` rewrites a named component file only; a passing component file is unchanged.
- [ ] Loop terminates even if `CorrectionPlannerAgent` never issues `accept` (max_iterations guard).
- [ ] The best-ever scoring candidate is preserved even if a later iteration regresses.

---

### EPIC-18 — Person 2: Output Assembly Agent

---

#### ISSUE-043 — OutputAssemblyAgent: best-candidate selection and file writing

- **Epic:** EPIC-18
- **Priority:** P1
- **Assignee:** Member 5
- **Dependencies:** ISSUE-042
- **Labels:** `person2`, `output`, `adk`

**Scope:**
- Reads `best_candidate` from session state (highest-scoring code snapshot across all iterations).
- Writes final `App.jsx` and sub-component files to `--output` directory.
- Returns exit code 0 if compilation passed at least once; exit code 1 otherwise.
- Writes `codegen_report.json` with: `best_score`, `total_iterations`, `components_generated`, `exit_code`.

**Acceptance Criteria:**
- [ ] After 3 iterations where iteration 2 had the best score: output files correspond to iteration 2's code (not iteration 3's).
- [ ] `codegen_report.json` exists and contains `best_score`, `total_iterations`, `exit_code`.
- [ ] Exit code 0 when at least one valid JSX was produced; exit code 1 otherwise.
- [ ] All component files referenced by `App.jsx` are written to the output directory.

---

### EPIC-19 — Observability & OpenTelemetry Integration

---

#### ISSUE-044 — OpenTelemetry setup and ADK event instrumentation

- **Epic:** EPIC-19
- **Priority:** P2
- **Assignee:** Member 5
- **Dependencies:** ISSUE-034, ISSUE-035, ISSUE-040
- **Labels:** `observability`, `opentelemetry`

**Scope:**
- OpenTelemetry SDK setup (TracerProvider, ConsoleSpanExporter for local dev).
- ADK `Event` callback hooks to record: agent name, start/end time, input/output size, errors.
- Per-agent spans with: latency (ms), retry count, status.
- Trace output written to `trace.json` when `--debug-trace` flag is passed.
- Document in `docs/observability.md`.

**Acceptance Criteria:**
- [ ] Running with `--debug-trace trace.json` produces a `trace.json`.
- [ ] `trace.json` contains spans for: `IngestionAgent`, `ComponentizationAgent`, `CodeGenAgent`, `JSXValidatorAgent`, `BrowserRenderAgent`, `VisualComparisonAgent`, `OutputAssemblyAgent`.
- [ ] Each span includes latency and status.
- [ ] No observability code introduces latency > 50ms per span.

---

### EPIC-20 — Person 2 Evaluation Harness

---

#### ISSUE-045 — Person 2 evaluation script: Compilation Pass Rate and visual scores

- **Epic:** EPIC-20
- **Priority:** P2
- **Assignee:** Member 5
- **Dependencies:** ISSUE-043, ISSUE-041
- **Labels:** `evaluation`, `person2`

**Scope:**
- Maintained set of at least 20 hand-written UIR files in `tests/fixtures/uir_samples/`.
- Evaluation script runs full Person 2 pipeline on each sample.
- Reports: Compilation Pass Rate, mean CW-SSIM score, mean CLIP score.
- Writes `eval_results/person2_eval.json` per run with per-sample breakdowns.

**Acceptance Criteria:**
- [ ] Script runs over all sample UIR files without crashing.
- [ ] `person2_eval.json` contains `compilation_pass_rate`, `mean_cwssim`, `mean_clip_score`, `sample_results`.
- [ ] At least one baseline number documented in `docs/evaluation_results.md`.

---

### EPIC-21 — End-to-End Integration & System Testing

---

#### ISSUE-046 — Integration test: Stage 1 → UIR on RICO samples

- **Epic:** EPIC-21
- **Priority:** P2
- **Assignee:** Member 5
- **Dependencies:** ISSUE-025, ISSUE-026
- **Labels:** `integration`, `person1`

**Scope:**
- Run the full Person 1 pipeline (Stages 1–7) on 20+ RICO test images.
- Verify `ui_tree.json` is produced and passes `ui_tree.schema.json` validation.

**Acceptance Criteria:**
- [ ] All 20 test images produce a `ui_tree.json` that passes schema validation.
- [ ] At least 80% of test images produce trees with ≥ 1 element correctly detected.
- [ ] Results documented in `docs/integration_test_results.md`.

---

#### ISSUE-047 — Integration test: UIR → App.jsx on Design2Code samples

- **Epic:** EPIC-21
- **Priority:** P2
- **Assignee:** Member 5
- **Dependencies:** ISSUE-045, ISSUE-046
- **Labels:** `integration`, `person2`

**Scope:**
- Run the full Person 2 pipeline on UIR files produced by Person 1 from Design2Code or WebSight samples.
- Report Compilation Pass Rate, CW-SSIM, CLIP scores on cross-pipeline data.

**Acceptance Criteria:**
- [ ] At least 10 end-to-end samples (image → App.jsx) run without crashing.
- [ ] Compilation Pass Rate ≥ 50% on the test set.
- [ ] Results documented in `docs/integration_test_results.md`.

---

#### ISSUE-048 — Full pipeline CLI entry point and documentation

- **Epic:** EPIC-21
- **Priority:** P2
- **Assignee:** Member 5
- **Dependencies:** ISSUE-043, ISSUE-023
- **Labels:** `cli`, `documentation`

**Scope:**
- Person 2 CLI: `python run_codegen_pipeline.py --input ui_tree.json --output ./dist --debug-trace trace.json`, exit code 0/1.
- Update `README.md` with complete usage guide, hardware requirements, and expected output file structure.

**Acceptance Criteria:**
- [ ] `python run_codegen_pipeline.py --help` describes all flags.
- [ ] Exit code 0 on successful run with a valid UIR input.
- [ ] Exit code 1 on syntactically invalid JSX after all repair attempts.
- [ ] `README.md` has a "Quick Start" section executable by a new team member.

---

## 6. Implementation Order and Dependency Map

```
Phase 0 — Foundation (Week 1, joint, blocking for everything)
  ISSUE-001 (UIR schema)
  ISSUE-002 (signature spec)
  ISSUE-003 (project scaffolding)

Phase 1 — Independent Component Implementation (Months 1–2)

  Person 1 Track:                    Person 2 Track:         Node Toolchain:
  ISSUE-004                          ISSUE-032               ISSUE-037
  ISSUE-005                          ISSUE-030               ISSUE-038
  ISSUE-006                          ISSUE-031               ISSUE-039
  ISSUE-007                          ISSUE-028
  ISSUE-008
  ISSUE-009                          ISSUE-027 (Kaggle)
  ISSUE-010
  ISSUE-011

Phase 2 — Core Algorithm Implementation (Months 2–3)

  ISSUE-012 → ISSUE-013
  → ISSUE-014 → ISSUE-015
  ISSUE-016 (calibration, parallel)
  → ISSUE-017 → ISSUE-018
  ISSUE-019 (calibration, parallel)
  → ISSUE-020 → ISSUE-021
  → ISSUE-022 → ISSUE-023
  ISSUE-024 (debug overlay, parallel)

Phase 3 — Person 2 Agent Pipeline (Months 2–4)

  ISSUE-029 → ISSUE-033 → ISSUE-034
  → ISSUE-035 → ISSUE-036
  → ISSUE-040 → ISSUE-041 → ISSUE-042
  → ISSUE-043

Phase 4 — Evaluation, Observability, Integration (Months 3–5)

  ISSUE-025, ISSUE-026 (Person 1 eval)
  ISSUE-045 (Person 2 eval)
  ISSUE-044 (OpenTelemetry)
  → ISSUE-046 → ISSUE-047 → ISSUE-048
```

---

## 7. Parallel Development Opportunities

| Group | Issues | Who | Prerequisite |
|---|---|---|---|
| **P1** | ISSUE-001, ISSUE-002, ISSUE-003 (joint contract) | Member 5 + Member 3 | Nothing |
| **P2** | ISSUE-004–006 (Stage 1) ‖ ISSUE-010 (Stage 2B) | Member 1 ‖ Member 2 | ISSUE-003 |
| **P3** | ISSUE-007–009 (VLM) ‖ ISSUE-011 (OCR integration) | Member 1 ‖ Member 2 | Phase 1 start |
| **P4** | ISSUE-012–023 (spatial parser) ‖ ISSUE-028–034 (Person 2 agents) | Member 1+2 ‖ Member 3 | ISSUE-001, ISSUE-003 |
| **P5** | ISSUE-037–039 (Node toolchain) ‖ ISSUE-008–009 (VLM inference) | Member 4 ‖ Member 1 | ISSUE-003 |
| **P6** | ISSUE-030–031 (RAG) ‖ ISSUE-029 (Componentization) | Member 3 (sequential within) | ISSUE-001 |
| **P7** | ISSUE-016, ISSUE-019 (calibration) ‖ ISSUE-027 (Kaggle notebook) | Member 1 ‖ Member 3 | Respective stage completions |
| **P8** | ISSUE-025, ISSUE-026 (Person 1 eval) ‖ ISSUE-045 (Person 2 eval) ‖ ISSUE-044 (OTel) | Member 1 ‖ Member 5 ‖ Member 5 | Phase 3 completion |

---

## 8. Team Ownership and Responsibility Boundaries

### Member 1 — Person 1 CV/ML Lead
**Primary:** Stages 1, 2A, 4, 5 (containment + layout), Person 1 evaluation  
**Integration:** Passes `Stage1Result` → Member 2; passes VLM element list → Member 2 (Stage 3); provides UIR evaluation output to Member 5  
**Issues:** ISSUE-004, 005, 006, 007, 008, 009, 014, 015, 016, 017, 018, 019, 025, 026

### Member 2 — Person 1 Spatial Processing Lead
**Primary:** Stages 2B, 3, 6, 7 (OCR, spatial fusion, pattern detection, UIR serialization)  
**Integration:** Consumes `Stage1Result` from Member 1; receives VLM element list from Member 1; hands `ui_tree.json` to Member 3  
**Issues:** ISSUE-010, 011, 012, 013, 020, 021, 022, 023, 024

### Member 3 — Person 2 Agent Pipeline Lead (Code Gen)
**Primary:** IngestionAgent, SubtreeHashTool, ComponentizationAgent, RAG layer, CodeGenAgent, fan-out/fan-in, Kaggle notebook  
**Integration:** Consumes `ui_tree.json` from Member 2; passes generated JSX → Member 4; uses Node tools from Member 4  
**Issues:** ISSUE-027, 028, 029, 030, 031, 032, 033, 034

### Member 4 — Person 2 Validation, Rendering & Node Toolchain Lead
**Primary:** Node toolchain (Babel/Vite/Playwright), JSXValidatorAgent, RepairAgent, BrowserRenderAgent, VisualComparisonAgent, CorrectionPlannerAgent, TargetedCorrectionAgent  
**Integration:** Consumes generated JSX from Member 3; passes best candidate and score → Member 5; Node tools consumed by Member 3's agents  
**Issues:** ISSUE-035, 036, 037, 038, 039, 040, 041, 042

### Member 5 — Infrastructure, Integration & Output Lead
**Primary:** UIR schema contract (joint), OutputAssemblyAgent, OpenTelemetry, Person 2 evaluation, end-to-end integration testing, project scaffolding  
**Integration:** Joint schema owner with Member 3; receives best candidate from Member 4; coordinates end-to-end results from Member 1 (UIR eval) and Member 4 (visual eval)  
**Issues:** ISSUE-001, 002, 003, 043, 044, 045, 046, 047, 048

---

## 9. Workload Distribution Summary

| Team Member | Primary Responsibilities | Assigned Issues | Estimated Workload |
|---|---|---|---|
| **Member 1** | Stage 1 Preprocessing, Stage 2A VLM, Stage 4 Containment, Stage 5 Layout, Person 1 Evaluation | ISSUE-004–009, 014–019, 025–026 (14 issues) | **Large** — most algorithmically complex (containment, layout classifiers, calibration, VLM inference with quantization) |
| **Member 2** | Stage 2B OCR, Stage 3 Fusion, Stage 6 Pattern Detection, Stage 7 UIR Serialization | ISSUE-010–013, 020–024 (9 issues) | **Large** — IoU matrix math, tree pattern matching, UIR validation and serialization |
| **Member 3** | Person 2 Ingestion/Componentization, RAG Layer, CodeGen Pipeline, Kaggle Notebook | ISSUE-027–034 (8 issues) | **Large** — ADK agent setup, vLLM serving, fan-out orchestration, ChromaDB + embedding model |
| **Member 4** | Node Toolchain, Syntax Validation Loop, Browser Rendering, 5-metric Visual Comparison, Correction Loop | ISSUE-035–042 (8 issues) | **Large** — most technically diverse (Node.js scripts, ADK LoopAgents, 5 visual metric implementations, targeted repair) |
| **Member 5** | UIR Schema Contract, Project Scaffolding, OutputAssemblyAgent, OpenTelemetry, Evaluation, Integration | ISSUE-001–003, 043–048 (9 issues) | **Medium-Large** — lower algorithm complexity but highest coordination overhead |

> **All five members carry Large or near-Large workloads.** The project's complexity precludes meaningful simplification without changing scope. Member 5 carries the lightest individual algorithmic work but the highest cross-team coordination responsibility.

---

## 10. Backlog Validation Checklist

### Scope Coverage
- [x] Every agreed project component is represented (Stages 1–7 Person 1; all 12 ADK agents Person 2; RAG; Node toolchain; Kaggle notebook; evaluation; observability).
- [x] Every explicitly agreed feature has corresponding implementation coverage.
- [x] No unapproved features or technologies have been introduced.
- [x] Unclear or missing requirements are documented in Section 3 (UQ-01 through UQ-08).

### Issue Quality
- [x] Every Issue has one clear implementation responsibility.
- [x] Every Issue has a descriptive title and detailed description.
- [x] Every Issue has objective acceptance criteria with specific, verifiable conditions.
- [x] Issues are small enough to be implemented and reviewed independently.
- [x] No Issue is unnecessarily fragmented (PDF loading and format loading co-located in ISSUE-004; gap + align + justify in ISSUE-018 as they are part of the same DFS pass).
- [x] No duplicate or overlapping responsibilities exist.

### Dependencies and Ordering
- [x] Dependencies are explicit and correctly referenced by Issue ID.
- [x] No circular dependencies exist (ISSUE-001 → all; ISSUE-002 → ISSUE-020 and ISSUE-029).
- [x] Parallel development opportunities identified (Section 7, groups P1–P8).
- [x] Implementation order reflects technical necessity (schema contract first, infrastructure second, algorithms third, integration last).

### Team Distribution
- [x] Every implementation Issue has exactly one assignee.
- [x] Responsibilities are distributed fairly across five members (all carry Large workload).
- [x] Component ownership is clearly defined (Section 8).
- [x] Unnecessary coordination minimized: Member 1 owns the entire spatial parser (Stages 4+5); Member 2 owns the entire fusion-to-serialization chain (Stages 2B, 3, 6, 7); Member 4 owns the entire validation+render+visual correction chain.

### Overall Consistency
- [x] Epic descriptions match their child Issues.
- [x] All 48 Issue IDs and dependency references are valid and cross-checked.
- [x] Priorities are consistent with the implementation sequence (P0 = schema; P1 = core algorithms and agent implementations; P2 = calibration, evaluation, integration; P3 = debug tooling).
- [x] No agreed project responsibility has been omitted.

### Known Limitations (Reported, Not Assumed Away)
- **UQ-03, UQ-04:** Containment and gap calibration values unknown until ISSUE-016 and ISSUE-019 are run. Downstream acceptance criteria reference "confirmed threshold" rather than hard-coded numbers.
- **UQ-05:** Visual metric composite weights require a hand-labeled set that does not yet exist. ISSUE-041 notes this and defers weight finalization.
- **UQ-08:** Wireframe modality detection heuristic is not fully specified. ISSUE-005 resolves as "wireframe = screenshot for v1" and documents the limitation explicitly in code.
