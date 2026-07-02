"""Pure payroll maths: load wage rates, total up hours, and produce final pay.

Nothing in this file touches images, OCR, or the network. Every function here is
deterministic, which keeps the money side of the tool easy to trust and to test.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

CENTS = Decimal("0.01")


@dataclass(frozen=True)
class PayrollLine:
    """One employee's pay for the period.

    Attributes:
        name: The employee's name as it should appear on the payslip.
        hours: Total hours worked across every timesheet in the period.
        hourly_rate: The wage rate joined from the rates file.
        gross_pay: ``hours * hourly_rate`` rounded to whole cents.
        note: Empty when everything matched, otherwise a plain-English warning
            (for example, a name with no matching wage rate).
    """

    name: str
    hours: Decimal
    hourly_rate: Decimal
    gross_pay: Decimal
    note: str


def normalize_name(name: str) -> str:
    """Return a lower-case, single-spaced key used to match names across files.

    This lets ``"  Jane   DOE "`` and ``"jane doe"`` join to the same person
    without changing how the name is displayed on the final payslip.
    """
    return re.sub(r"\s+", " ", name).strip().lower()


def to_money(amount: Decimal) -> Decimal:
    """Round a Decimal to whole cents using normal (round-half-up) rounding."""
    return amount.quantize(CENTS, rounding=ROUND_HALF_UP)


def load_rates(path: Path) -> dict[str, tuple[str, Decimal]]:
    """Read the wage-rate file into a lookup keyed by normalized name.

    The file must have ``name`` and ``hourly_rate`` columns. Returns a mapping of
    ``normalized_name -> (display_name, hourly_rate)``.
    """
    rates: dict[str, tuple[str, Decimal]] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            name = row["name"].strip()
            rates[normalize_name(name)] = (name, Decimal(str(row["hourly_rate"]).strip()))
    return rates


def load_hours(path: Path) -> dict[str, tuple[str, Decimal]]:
    """Read the reviewed hours file, summing hours per person.

    The file must have ``name`` and ``hours`` columns. A person may appear on
    several rows (one per timesheet); their hours are added together. Returns a
    mapping of ``normalized_name -> (display_name, total_hours)``.
    """
    totals: dict[str, tuple[str, Decimal]] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            name = re.sub(r"\s+", " ", row["name"]).strip()
            key = normalize_name(name)
            display, running = totals.get(key, (name, Decimal("0")))
            totals[key] = (display, running + Decimal(str(row["hours"]).strip()))
    return totals


def build_payroll(
    rates: dict[str, tuple[str, Decimal]],
    hours: dict[str, tuple[str, Decimal]],
) -> list[PayrollLine]:
    """Join hours to wage rates and calculate gross pay for everyone who worked.

    Every person with hours gets a line, so nobody who worked is silently
    dropped. A name with no matching wage rate still produces a line, flagged
    with a note so the problem is visible on the final sheet. Lines are returned
    sorted by name.
    """
    lines: list[PayrollLine] = []
    for key, (timesheet_name, total_hours) in hours.items():
        if key in rates:
            display, rate = rates[key]
            note = "" if total_hours > 0 else "Zero hours - please double-check"
        else:
            display, rate = timesheet_name, Decimal("0")
            note = "No wage rate found - check the name spelling"
        lines.append(
            PayrollLine(
                name=display,
                hours=total_hours,
                hourly_rate=rate,
                gross_pay=to_money(total_hours * rate),
                note=note,
            )
        )
    return sorted(lines, key=lambda line: normalize_name(line.name))


def write_payroll(lines: list[PayrollLine], path: Path) -> None:
    """Write the final payroll to a CSV with one row per employee."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["name", "hours", "hourly_rate", "gross_pay", "note"])
        for line in lines:
            writer.writerow(
                [line.name, line.hours, line.hourly_rate, line.gross_pay, line.note]
            )


def summarize(lines: list[PayrollLine]) -> str:
    """Return a short, human-readable summary to print after a payroll run."""
    total = to_money(sum((line.gross_pay for line in lines), Decimal("0")))
    problems = [line for line in lines if line.note]
    parts = [f"{len(lines)} employee(s) processed.", f"Total gross pay: {total}"]
    if problems:
        parts.append(f"{len(problems)} line(s) need a look:")
        parts.extend(f"  - {line.name}: {line.note}" for line in problems)
    else:
        parts.append("No problems found.")
    return "\n".join(parts)
