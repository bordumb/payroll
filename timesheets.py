"""Turn handwritten timesheet images/PDFs into a plain hours CSV for review.

This is the only file that uses OCR and the network. It reads every image or PDF
in a folder, asks a Claude vision model to transcribe the names and hours, and
writes them to a CSV that a human checks before any money is calculated.
"""

from __future__ import annotations

import base64
import csv
import json
import os
from pathlib import Path

from anthropic import Anthropic

# Options
# Expensive/Accurate: claude-opus-4-8 
# Cheaper/Capable: claude-sonnet-5
MODEL = "claude-sonnet-5"

IMAGE_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}

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
    allowed = set(IMAGE_MEDIA_TYPES) | {".pdf"}
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in allowed)


def _content_block(path: Path) -> dict:
    """Build the correct image or document block for a single file."""
    data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return {
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf", "data": data},
        }
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": IMAGE_MEDIA_TYPES[suffix],
            "data": data,
        },
    }


def _extract_rows(client: Anthropic, path: Path) -> list[dict]:
    """Send one timesheet to the model and parse its JSON reply into rows."""
    message = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": [_content_block(path), {"type": "text", "text": PROMPT}],
            }
        ],
    )
    text = "".join(block.text for block in message.content if block.type == "text")
    return json.loads(text[text.index("[") : text.rindex("]") + 1])


def read_all_timesheets(folder: Path, out_csv: Path) -> int:
    """Read every timesheet in ``folder`` and write a reviewable hours CSV.

    Each output row records the employee, the hours read, and the file it came
    from, so a person can check the CSV against the paper. Returns the number of
    rows written.
    """
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    files = find_timesheets(folder)
    if not files:
        raise FileNotFoundError(f"No images or PDFs found in {folder}")

    rows_written = 0
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["name", "hours", "source_file"])
        for path in files:
            print(f"Reading {path.name} ...")
            for row in _extract_rows(client, path):
                writer.writerow([row["name"], row["hours"], path.name])
                rows_written += 1
    return rows_written
