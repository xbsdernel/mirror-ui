"""
Stage 1 — Input Preprocessing

Responsibilities:
1. Load image (PNG, JPEG) or render PDF page at 150 DPI.
2. Detect input modality: 'screenshot', 'wireframe', or 'sketch' (photo).
3. Apply adaptive cleaning ONLY for sketches (contrast enhancement & shadow reduction).
4. Resize longest dimension to <= 1280px while preserving aspect ratio.
5. Track and return the resize_ratio for coordinate restoration in Stage 7.
"""

import os
from typing import Tuple, Optional
from PIL import Image, ImageOps, ExifTags
import numpy as np

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

from src.types import Stage1Result


def load_pdf_as_image(pdf_path: str, dpi: int = 150) -> Image.Image:
    """
    Renders the first page of a PDF document to a PIL Image at the specified DPI.
    Tries pypdfium2, fitz (PyMuPDF), and pdf2image.
    """
    # Attempt 1: pypdfium2 (fast and standalone)
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(pdf_path)
        first_page = pdf[0]
        # 72 points per inch standard -> scale factor = dpi / 72
        scale = dpi / 72.0
        pil_image = first_page.render(scale=scale).to_pil()
        return pil_image.convert("RGB")
    except ImportError:
        pass

    # Attempt 2: PyMuPDF (fitz)
    try:
        import fitz
        doc = fitz.open(pdf_path)
        page = doc[0]
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return img
    except ImportError:
        pass

    # Attempt 3: pdf2image
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path, dpi=dpi, first_page=1, last_page=1)
        if images:
            return images[0].convert("RGB")
    except ImportError:
        pass

    raise RuntimeError(
        f"Unable to read PDF file '{pdf_path}'. "
        "Please install 'pypdfium2' (recommended), 'PyMuPDF', or 'pdf2image'."
    )


def detect_modality(pil_image: Image.Image) -> str:
    """
    Heuristically identifies whether an image is a clean 'screenshot',
    a digital 'wireframe', or a hand-drawn 'sketch' / photograph.
    """
    # 1. Check EXIF metadata (camera photos usually have camera tags)
    exif = pil_image.getexif()
    if exif:
        for tag_id in exif:
            tag_name = ExifTags.TAGS.get(tag_id, "")
            if tag_name in ("Make", "Model", "Software", "DateTimeOriginal"):
                return "sketch"

    # Convert to grayscale array for statistical analysis
    gray = np.array(pil_image.convert("L"), dtype=np.float32)

    # 2. Check background uniformity
    # Clean UI screenshots have large areas of perfectly uniform color (zero variance).
    # Photographs of sketches have paper grain, lighting gradients, and camera noise.
    h, w = gray.shape
    sample_patches = []
    patch_size = 32

    # Sample a grid of small patches across the image
    for y in range(0, h - patch_size, max(h // 6, patch_size)):
        for x in range(0, w - patch_size, max(w // 6, patch_size)):
            patch = gray[y:y + patch_size, x:x + patch_size]
            sample_patches.append(np.std(patch))

    if sample_patches:
        # Percentage of patches with very low local variance (typical of clean UI backgrounds)
        flat_patches = [std for std in sample_patches if std < 2.0]
        flat_ratio = len(flat_patches) / len(sample_patches)

        # If more than 35% of sample patches are virtually flat, it's a digital screenshot/wireframe
        if flat_ratio > 0.35:
            return "screenshot"

    # 3. Check for color saturation: digital screenshots usually have distinct colors,
    # whereas pencil sketches on paper are predominantly grayscale with paper tint.
    rgb_arr = np.array(pil_image.convert("RGB"), dtype=np.float32)
    color_diff = np.mean(np.abs(rgb_arr[:, :, 0] - rgb_arr[:, :, 1]) +
                         np.abs(rgb_arr[:, :, 1] - rgb_arr[:, :, 2]))

    if color_diff < 8.0:
        # Near-grayscale with high noise across patches indicates a paper sketch
        return "sketch"

    return "screenshot"


def clean_sketch_image(pil_image: Image.Image) -> Image.Image:
    """
    Applies adaptive contrast enhancement and shadow removal to sketch photos.
    This helps the VLM detect drawn boxes, text, and lines clearly.
    Clean screenshots should NOT pass through this.
    """
    if not HAS_OPENCV:
        # Fallback using standard PIL if OpenCV is not available
        gray = pil_image.convert("L")
        enhanced = ImageOps.autocontrast(gray, cutoff=2)
        return enhanced.convert("RGB")

    # OpenCV based enhancement
    img_cv = np.array(pil_image.convert("RGB"))
    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)

    # Convert to grayscale
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)

    # Convert back to RGB
    enhanced_rgb = cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2RGB)
    return Image.fromarray(enhanced_rgb)


def resize_image_capped(pil_image: Image.Image, max_dim: int = 1280) -> Tuple[Image.Image, float]:
    """
    Resizes image so that its longest dimension <= max_dim, preserving aspect ratio.
    Returns the resized PIL Image and the resize_ratio (new_dim / original_dim).
    """
    orig_w, orig_h = pil_image.size
    longest = max(orig_w, orig_h)

    if longest <= max_dim:
        return pil_image.copy(), 1.0

    resize_ratio = max_dim / float(longest)
    new_w = int(round(orig_w * resize_ratio))
    new_h = int(round(orig_h * resize_ratio))

    resized_image = pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    return resized_image, resize_ratio


def preprocess_image(
    input_path: str,
    output_dir: str = "outputs/normalized",
    max_dim: int = 1280,
    forced_input_type: Optional[str] = None
) -> Stage1Result:
    """
    Main entry point for Stage 1 Preprocessing.

    Parameters:
        input_path: File path to the raw input (PNG, JPG, PDF, etc.)
        output_dir: Directory where the normalized PNG will be saved.
        max_dim: Maximum allowed size for the longest dimension (default 1280).
        forced_input_type: Optional override ('screenshot', 'wireframe', or 'sketch').

    Returns:
        Stage1Result containing normalized image path, resize_ratio, and dimensions.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found at: {input_path}")

    # 1. Load image (handle PDF or standard image)
    file_ext = os.path.splitext(input_path)[1].lower()
    if file_ext == ".pdf":
        raw_image = load_pdf_as_image(input_path, dpi=150)
    else:
        raw_image = Image.open(input_path)
        # Fix orientation if camera metadata has rotation
        raw_image = ImageOps.exif_transpose(raw_image)
        raw_image = raw_image.convert("RGB")

    orig_size = raw_image.size  # (width, height)

    # 2. Modality detection
    if forced_input_type:
        input_type = forced_input_type
    else:
        input_type = detect_modality(raw_image)

    # 3. Modality-specific cleaning
    if input_type == "sketch":
        processed_image = clean_sketch_image(raw_image)
    else:
        # Screenshots and wireframes pass through unmodified to avoid degrading text/lines
        processed_image = raw_image

    # 4. Resize with capped resolution
    normalized_image, resize_ratio = resize_image_capped(processed_image, max_dim=max_dim)
    norm_size = normalized_image.size  # (width, height)

    # 5. Save normalized PNG
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    normalized_filename = f"{base_name}_normalized.png"
    normalized_filepath = os.path.join(output_dir, normalized_filename)
    normalized_image.save(normalized_filepath, format="PNG")

    return Stage1Result(
        normalized_image_path=normalized_filepath,
        input_type=input_type,
        resize_ratio=resize_ratio,
        original_size=orig_size,
        normalized_size=norm_size
    )
