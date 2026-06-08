from __future__ import annotations

import io
from pathlib import Path

import fitz
from PIL import Image, ImageEnhance, ImageFilter

_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".tiff", ".bmp"})


def pdf_to_images(
    pdf_path: Path, *, dpi: int = 300, max_pages: int | None = None
) -> list[Image.Image]:
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    doc = fitz.open(pdf_path)
    try:
        page_count = doc.page_count
        if max_pages is not None:
            page_count = min(page_count, max_pages)
        pages = [doc[i] for i in range(page_count)]
        result: list[Image.Image] = []
        for page in pages:
            pix = page.get_pixmap(matrix=matrix)
            result.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        return result
    finally:
        doc.close()


def optimize_image(img: Image.Image, *, max_long_edge: int = 3072, jpeg_quality: int = 90) -> bytes:
    if img.mode != "RGB":
        img = img.convert("RGB")

    long_edge = max(img.width, img.height)
    if long_edge > max_long_edge:
        scale = max_long_edge / long_edge
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    img = img.filter(ImageFilter.SHARPEN)
    img = ImageEnhance.Contrast(img).enhance(1.3)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=jpeg_quality)
    return buf.getvalue()


def load_images(
    path: Path,
    *,
    dpi: int = 300,
    max_pages: int | None = None,
    max_long_edge: int = 3072,
) -> list[bytes]:
    if path.suffix.lower() == ".pdf":
        pil_images = pdf_to_images(path, dpi=dpi, max_pages=max_pages)
    elif path.suffix.lower() in _IMAGE_EXTENSIONS:
        pil_images = [Image.open(path)]
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    return [optimize_image(img, max_long_edge=max_long_edge) for img in pil_images]
