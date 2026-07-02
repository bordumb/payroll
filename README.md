# Payroll helper

Reads handwritten timesheets, then works out each person's pay.

You run it in **two steps** every pay period. Step 1 reads the timesheets into a
spreadsheet you can check. Step 2 does the money once you're happy the hours are
right.

## Folder layout

Everything for one pay period lives in a dated folder. You make the folder, drop
the timesheets in, and the tool writes its results back into the same folder.

```
payroll_tool/
    run_payroll.py            <- the thing you run
    payroll.py                <- the money maths
    timesheets.py             <- reads the handwriting
    employee_rates/
        employee_rates.csv    <- who earns what (shared by every period)
    payroll/
        2026/
            06/
                01/           <- one pay period: put the timesheets here
                    week1.jpg
                    week2.pdf
                    hours_to_review.csv   (written by step 1)
                    payroll_final.csv     (written by step 2)
```

The period folder is `payroll/{year}/{month}/{day}`. The date is up to you (the
pay date, or the start of the two weeks) — just be consistent.

## Setup (pick ONE way to read the handwriting)

Do this once. You only need one of the two options below.

### Option A — Cloud reader (most accurate, needs a key set up once)

1. Install Python 3.10 or newer.
2. In a terminal in this folder:  `pip install -r requirements.txt`
3. Get a key from https://console.anthropic.com and tell your computer about it.
   Your mom never types this — it's a one-time step:
   - **Mac/Linux:** `export ANTHROPIC_API_KEY="your-key-here"`
   - **Windows:** `setx ANTHROPIC_API_KEY "your-key-here"` (then reopen the terminal)

### Option B — Local reader (no key, no cost, runs on your computer)

Best if you'd rather not deal with any account or key. Needs a reasonably capable
computer (about 8 GB of memory, 16 GB is better) and is slower.

1. Install Python 3.10 or newer.
2. Install Ollama from https://ollama.com/download
3. Download a vision model:  `ollama pull qwen2.5vl`
4. In a terminal in this folder:  `pip install -r requirements-local.txt`
5. Switch the tool to the local reader by renaming the files:
   - rename `timesheets.py` to `timesheets_api.py` (keeps it as a backup)
   - rename `timesheets_ollama.py` to `timesheets.py`

Nothing else changes — the two steps below work the same either way.

## Every pay period

1. Make this period's folder, for example `payroll/2026/06/01`, and put the
   timesheet photos or scans (`.jpg`, `.png`, or `.pdf`) inside it.
2. Make sure `employee_rates/employee_rates.csv` is up to date. It needs two
   columns: `name` and `hourly_rate`.
3. **Step 1 — read the hours** (defaults to today's folder):
   ```
   python run_payroll.py read
   ```
   To run an earlier or specific period, add the date:
   ```
   python run_payroll.py read --date 2026-06-15
   ```
   This creates `hours_to_review.csv` inside that period's folder.
4. **Open `hours_to_review.csv` and check it against the paper timesheets.**
   Fix any hours the computer misread, then save the file. This is the most
   important step — everything after it is just multiplication.
5. **Step 2 — do the pay** (use the same date you used in step 1):
   ```
   python run_payroll.py pay --date 2026-06-15
   ```
   This creates `payroll_final.csv` in the same folder and prints a summary.

## Reading the results

`payroll_final.csv` has a `note` column. It's blank when all is well. It fills in
when something needs attention — for example, a name on a timesheet that doesn't
match any name in the wage-rate file (usually a spelling difference). Nobody who
worked is ever dropped; they show up with a note instead, so you can fix it.

## Good to know

- Names are matched ignoring capitals and extra spaces, so `jane doe` and
  `Jane   Doe` count as the same person. The clean spelling from the rates file
  is the one that appears on the final sheet.
- If someone appears on more than one timesheet in the period, their hours are
  added together.
- Pay is simple `hours x rate`. It does **not** add overtime, tax, or
  deductions — that matches the current by-hand process.
- To try a different local model (Option B), open `timesheets.py` and change
  `MODEL` (for example to `minicpm-v` or `llama3.2-vision`).
- To try a cheaper cloud model (Option A), open `timesheets.py` and change
  `MODEL` from `claude-opus-4-8` to `claude-sonnet-5`.

## The files

- `run_payroll.py` — the thing you run. Settings (folder paths) are at the top.
- `payroll.py` — the money maths (Step 2). Unchanged whichever reader you use.
- `timesheets.py` — reads the handwriting (Step 1).
- `timesheets_ollama.py` — the local, no-key reader you can swap in (Option B).
- `employee_rates/employee_rates.csv` — your list of who earns what.
- `requirements.txt` / `requirements-local.txt` — what to install for each option.
