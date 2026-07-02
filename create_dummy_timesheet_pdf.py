"""Create a typed sample timesheet PDF for testing the payroll pipeline.

Real timesheets are handwritten; this makes a clean, typed stand-in so you can
exercise the whole read -> review -> pay flow (folder discovery, PDF reading,
CSV writing, the join, and the maths) without waiting for real paperwork. Typed
text is easy to read, so a successful run proves the plumbing works rather than
proving anything about handwriting accuracy.

    python make_sample_timesheet.py                  # today's period folder
    python make_sample_timesheet.py --date 2026-06-01

This is a standalone helper on purpose: it does not import the rest of the tool,
so it works whichever reader (cloud or local) you have installed.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

PAYROLL_ROOT = Path("payroll")

# Names match employee_rates/employee_rates.csv so a full run produces a clean
# payroll with no "missing rate" notes.
SAMPLE_ROWS: list[tuple[str, float]] = [
    ("Jane Doe", 72.5),
    ("John Smith", 80.0),
    ("Maria Garcia", 64.0),
]


def period_folder(day: date) -> Path:
    """Return the pay-period folder ``payroll/YYYY/MM/DD`` for ``day``."""
    return PAYROLL_ROOT / f"{day.year:04d}" / f"{day.month:02d}" / f"{day.day:02d}"


def make_timesheet(path: Path, rows: list[tuple[str, float]], period: str) -> None:
    """Write a typed timesheet PDF listing each employee and their hours.

    Args:
        path: Where to write the PDF.
        rows: ``(employee_name, hours)`` pairs to place in the table.
        period: A human-readable period label shown beneath the title.
    """
    styles = getSampleStyleSheet()
    table = Table(
        [["Employee", "Hours"], *[[name, f"{hours:g}"] for name, hours in rows]],
        colWidths=[3.5 * inch, 1.5 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    SimpleDocTemplate(str(path), pagesize=letter).build(
        [
            Paragraph("Staff Timesheet", styles["Title"]),
            Paragraph(f"Pay period: {period}", styles["Normal"]),
            Spacer(1, 0.3 * inch),
            table,
        ]
    )


def main() -> None:
    """Write a sample timesheet into the chosen pay-period folder."""
    parser = argparse.ArgumentParser(description="Make a sample timesheet PDF.")
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=date.today(),
        help="pay-period date as YYYY-MM-DD (default: today)",
    )
    args = parser.parse_args()
    folder = period_folder(args.date)
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / "sample_timesheet.pdf"
    make_timesheet(out, SAMPLE_ROWS, args.date.isoformat())
    print(f"Wrote {out}")
    print(f"Now run:  python run_payroll.py read --date {args.date.isoformat()}")


if __name__ == "__main__":
    main()
