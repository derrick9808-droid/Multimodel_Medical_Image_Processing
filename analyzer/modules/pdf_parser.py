"""
PDF Text & Layout Extraction Module using pdfplumber.
Extracts raw text, structured tables, and word-level bounding boxes with font sizes
to power the ATS parser preview and Recruiter 6-Second Eye-Scan Simulation.
"""

import pdfplumber
from pathlib import Path
from typing import Dict, Any, List

def extract_pdf_data(pdf_path: str) -> Dict[str, Any]:
    """
    Extracts text, word layout bounding boxes, and table structures from a PDF.
    """
    file_path = Path(pdf_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    full_text_pages: List[str] = []
    word_boxes: List[Dict[str, Any]] = []
    tables_found: List[List[List[str]]] = []
    page_dimensions: List[Dict[str, float]] = []

    with pdfplumber.open(file_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            page_text = page.extract_text() or ""
            full_text_pages.append(page_text)
            page_dimensions.append({
                "page_number": page_idx + 1,
                "width": float(page.width),
                "height": float(page.height)
            })

            # Extract tables if present
            try:
                page_tables = page.extract_tables()
                if page_tables:
                    tables_found.extend(page_tables)
            except Exception:
                pass

            # Extract words with layout coordinates & font attributes
            try:
                words = page.extract_words(
                    extra_attrs=["fontname", "size", "upright"],
                    keep_blank_chars=False
                )
                for w in words:
                    word_boxes.append({
                        "text": w.get("text", ""),
                        "x0": round(float(w.get("x0", 0)), 1),
                        "top": round(float(w.get("top", 0)), 1),
                        "x1": round(float(w.get("x1", 0)), 1),
                        "bottom": round(float(w.get("bottom", 0)), 1),
                        "size": round(float(w.get("size", 10)), 1),
                        "fontname": str(w.get("fontname", "default")),
                        "page": page_idx + 1
                    })
            except Exception:
                pass

    joined_text = "\n\n".join(full_text_pages).strip()
    
    # Calculate statistics
    font_sizes = [w["size"] for w in word_boxes if w.get("size")]
    avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 10.0
    max_font_size = max(font_sizes) if font_sizes else 14.0

    return {
        "text": joined_text,
        "page_count": len(full_text_pages),
        "pages": full_text_pages,
        "page_dimensions": page_dimensions,
        "word_boxes": word_boxes,
        "tables": tables_found,
        "stats": {
            "total_words": len(word_boxes),
            "avg_font_size": round(avg_font_size, 1),
            "max_font_size": round(max_font_size, 1),
            "character_count": len(joined_text)
        }
    }
