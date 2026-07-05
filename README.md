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
    .env                      <- a hidden file that you can save your API key to (See below)
    run_payroll.py            <- the thing you run
    payroll.py                <- the money maths
    timesheets.py             <- picks cloud or local, then reads the handwriting
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
   Your mom never types this — it's a one-time step. Pick either way:
   - **Recommended — a `.env` file:** copy `.env.example` to `.env` and put your
     key in it (`ANTHROPIC_API_KEY=sk-ant-...`). The tool loads it automatically,
     and `.env` is git-ignored so the key never gets committed.
   - **Or a shell variable (Mac/Linux):** `export ANTHROPIC_API_KEY="your-key-here"`

> Note: it's important to keep your API key safe. It's like a password for access to your Claude account. If someone else gains access to it, they can charge your account and steal your balance.

### Option B — Local reader (no key, no cost, runs on your computer)

Best if you'd rather not deal with any account or key. Needs a reasonably capable
computer (about 8 GB of memory, 16 GB is better) and is slower.

1. Install Python 3.10 or newer.
2. Install Ollama from https://ollama.com/download
3. Download a vision model:  `ollama pull qwen2.5vl`
4. In a terminal in this folder:  `pip install -r requirements-local.txt`
5. Tell the tool to use it, either way:
   - **In `.env`:** copy `.env.example` to `.env` if you haven't already, and
     set `READER=local` (no API key needed for this option).
   - **Or per run:** add `--reader local` to the command, for example
     `python run_payroll.py read --reader local`.

Nothing else changes — the two steps below work the same either way. Switch
back to the cloud reader any time with `READER=cloud` (or `--reader cloud`) —
no renaming files, no reinstalling.

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
   python run_payroll.py read --date 2026-06-01
   ```
   This creates `hours_to_review.csv` inside that period's folder.
4. **Open `hours_to_review.csv` and check it against the paper timesheets.**
   Fix any hours the computer misread, then save the file. This is the most
   important step — everything after it is just multiplication.
5. **Step 2 — do the pay** (use the same date you used in step 1):
   ```
   python run_payroll.py pay --date 2026-06-01
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
- To try a different local model (Option B), open `timesheets_ollama.py` and
  change `MODEL` (for example to `minicpm-v` or `llama3.2-vision`).
- To try a different cloud model (Option A), open `timesheets_api.py` and
  change `MODEL` (for example between `claude-sonnet-5` and `claude-opus-4-8`).

## The files

- `run_payroll.py` — the thing you run. Settings (folder paths) are at the top.
- `payroll.py` — the money maths (Step 2). Unchanged whichever reader you use.
- `timesheets.py` — picks the reader (Step 1), via `--reader` or the `READER`
  env var.
- `timesheets_api.py` — the cloud reader, Claude vision (Option A).
- `timesheets_ollama.py` — the local, no-key reader, Ollama (Option B).
- `employee_rates/employee_rates.csv` — your list of who earns what.
- `requirements.txt` / `requirements-local.txt` — what to install for each option.

## Testing

You will see a file called `create_dummy_timesheet_pdf.py`, which creates a fake PDF to help simulate the workflow.

You can run it using this:
```bash
python make_sample_timesheet.py --date 2026-06-01
python run_payroll.py read --date 2026-06-01
python run_payroll.py pay  --date 2026-06-01
```

Which does this:
- drops a PDF into payroll/2026/06/15/
- your real reader transcribes it
- produces payroll_final.csv
