"""Turn handwritten timesheet images/PDFs into a plain hours CSV for review.

This is the local, no-key twin of ``timesheets_api.py``: instead of Claude, it
asks a vision model running on your own machine via Ollama. PDFs are rasterized
page by page (Ollama vision models take images, not PDFs) before being sent.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import fitz  # PyMuPDF
import ollama
from dotenv import load_dotenv

load_dotenv()

# Try a different local model, for example "minicpm-v" or "llama3.2-vision".
MODEL = "qwen2.5vl"

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

PROMPT = (
    "This is a handwritten staff timesheet. Read it carefully and list every "
    "employee together with the total hours they worked for the period. "
    "Reply with ONLY a JSON array, no prose, in exactly this shape: "
    '[{"name": "Full Name", "hours": 0.0}]. '
    "Use decimal hours (for example 7.5, not 7:30). If a value is unclear, give "
    "your best reading and still include the row."
)


def find_timesheets(folder: Path) -> list[Path]:
    """Return every image and PDF in ``folder``, sorted for predictable output."""
    allowed = IMAGE_SUFFIXES | {".pdf"}
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in allowed)


def _file_to_images(path: Path) -> list[bytes]:
    """Return ``path`` as one or more PNG/raw image byte strings.

    Images are passed through as-is. PDFs are rasterized one page at a time,
    since Ollama vision models take images, not PDF documents.
    """
    if path.suffix.lower() == ".pdf":
        with fitz.open(path) as doc:
            return [page.get_pixmap(dpi=200).tobytes("png") for page in doc]
    return [path.read_bytes()]


def _parse_rows(text: str) -> list[dict]:
    """Extract the JSON array of rows from a model's reply, ignoring any prose."""
    return json.loads(text[text.index("[") : text.rindex("]") + 1])


def _extract_rows(path: Path) -> list[dict]:
    """Send one timesheet to the local model and parse its JSON reply into rows."""
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT, "images": _file_to_images(path)}],
    )
    return _parse_rows(response.message.content)


def read_all_timesheets(folder: Path, out_csv: Path) -> int:
    """Read every timesheet in ``folder`` and write a reviewable hours CSV.

    Each output row records the employee, the hours read, and the file it came
    from, so a person can check the CSV against the paper. Returns the number of
    rows written.
    """
    try:
        ollama.list()
    except Exception as exc:
        raise RuntimeError(
            "Could not reach Ollama. Install it from https://ollama.com/download, "
            f"make sure it's running, and pull the vision model with:\n"
            f"    ollama pull {MODEL}"
        ) from exc

    files = find_timesheets(folder)
    if not files:
        raise FileNotFoundError(f"No images or PDFs found in {folder}")

    rows_written = 0
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["name", "hours", "source_file"])
        for path in files:
            print(f"Reading {path.name} ...")
            for row in _extract_rows(path):
                writer.writerow([row["name"], row["hours"], path.name])
                rows_written += 1
    return rows_written
