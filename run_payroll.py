"""Run the bi-weekly payroll in two simple steps, for one dated folder.

Each pay period lives in one folder:  payroll/{year}/{month}/{day}
Put the timesheet photos/scans in there, then run the two steps below. The
review file and the final payroll are written back into the same folder.

Step 1 (read):  python run_payroll.py read
    Reads the handwritten timesheets and writes hours_to_review.csv.

Step 2 (pay):   python run_payroll.py pay
    Reads the (checked) hours file and the wage rates, then writes
    payroll_final.csv.

Both steps default to today's folder. To run an earlier period, pass a date:
    python run_payroll.py read --date 2026-06-15
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import payroll
import timesheets

# ------------------------------- SETTINGS -------------------------------
# Top of the payroll tree. Each pay period is a folder underneath it:
#   PAYROLL_ROOT/{year}/{month}/{day}
PAYROLL_ROOT = Path("payroll")

# The wage-rate file, shared across all periods (its own folder at the repo root).
RATES_CSV = Path("employee_rates") / "employee_rates.csv"

# File names used inside each dated period folder.
HOURS_FILENAME = "hours_to_review.csv"
PAYROLL_FILENAME = "payroll_final.csv"
# ------------------------------------------------------------------------


def period_folder(day: date) -> Path:
    """Return the folder for a pay period: ``payroll/YYYY/MM/DD``.

    Month and day are zero-padded so they sort correctly (``06`` before ``12``).
    """
    return PAYROLL_ROOT / f"{day.year:04d}" / f"{day.month:02d}" / f"{day.day:02d}"


def read_step(folder: Path) -> None:
    """Step 1: OCR the timesheets in ``folder`` into a CSV for a human to check."""
    hours_csv = folder / HOURS_FILENAME
    count = timesheets.read_all_timesheets(folder, hours_csv)
    print(f"\nWrote {count} row(s) to {hours_csv}.")
    print("Please open that file, check it against the paper timesheets, fix any")
    print("mistakes, then run:  python run_payroll.py pay")


def pay_step(folder: Path) -> None:
    """Step 2: join the folder's reviewed hours to wage rates and write pay."""
    rates = payroll.load_rates(RATES_CSV)
    hours = payroll.load_hours(folder / HOURS_FILENAME)
    lines = payroll.build_payroll(rates, hours)
    payroll_csv = folder / PAYROLL_FILENAME
    payroll.write_payroll(lines, payroll_csv)
    print(f"Wrote payroll to {payroll_csv}.\n")
    print(payroll.summarize(lines))


def main() -> None:
    """Resolve the pay-period folder from the chosen date and run the step."""
    parser = argparse.ArgumentParser(description="Bi-weekly payroll helper.")
    parser.add_argument("step", choices=["read", "pay"], help="which step to run")
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=date.today(),
        help="pay-period date as YYYY-MM-DD (default: today)",
    )
    args = parser.parse_args()
    folder = period_folder(args.date)
    if not folder.exists():
        raise FileNotFoundError(f"No folder for that date: {folder}")
    {"read": read_step, "pay": pay_step}[args.step](folder)


if __name__ == "__main__":
    main()