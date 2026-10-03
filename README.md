# mirror-ui

Converts screenshots, wireframes, and hand-drawn sketches into **componentized React + Tailwind applications**.

## How It Works

The system uses a two-stage pipeline:

### 1. UI Perception

The input image is analyzed using:

* **Qwen2-VL** — visual understanding
* **PaddleOCR** — text extraction
* **Custom layout parser** — detects containers, rows, columns, gaps, and repeated components

These signals are combined into a **framework-agnostic UI Intermediate Representation (UIR)**.

### 2. Code Generation & Verification

A **Google ADK multi-agent workflow** then:

1. Converts the UIR into reusable components.
2. Retrieves relevant UI patterns from a **ChromaDB RAG index**.
3. Generates React + Tailwind code using **Qwen2.5-Coder**.
4. Validates the generated code using **Babel AST analysis**.
5. Renders the application with **Vite + Playwright**.
6. Compares the rendered result with the original input using:

   * CW-SSIM
   * LPIPS
   * CLIP
   * DreamSim
7. Uses these external evaluation signals to drive corrections.

The system does **not rely on the LLM to review its own output**. Corrections are driven by deterministic or independently computed signals from the rendered result.

## Pipeline

```text
Image
  ↓
Qwen2-VL + PaddleOCR + Layout Parser
  ↓
UI Intermediate Representation (UIR)
  ↓
ADK Multi-Agent Workflow
  ↓
Componentization + RAG
  ↓
Qwen2.5-Coder
  ↓
Babel AST Validation
  ↓
Vite + Playwright Rendering
  ↓
Visual Evaluation
(CW-SSIM + LPIPS + CLIP + DreamSim)
  ↓
Correction Loop
  ↓
React + Tailwind Application
```

## Key Features

* Screenshot → React + Tailwind
* Supports wireframes and hand-drawn sketches
* Framework-agnostic UI representation
* Automatic componentization
* RAG-based UI pattern retrieval
* AST-based code validation
* Browser-based rendering and verification
* Multi-metric visual evaluation
* External feedback-driven correction loop
* Fully based on **open-weight, self-hostable models**
