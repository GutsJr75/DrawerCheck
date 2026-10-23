# Troubleshooting

These examples use fictional records and the current command-line core. Each
symptom below is an exact CLI message, filled with the example values shown.
Tests in `tests/test_troubleshooting.py` trigger all ten messages and compare
them with this guide and [errors.py](../src/drawercheck/errors.py).
Run commands from your project folder with the virtual environment active.
Use the same `--db` path for import, reconciliation, reports, and explanations.

## T01: Money has the wrong number of decimal places

**Symptom**

```text
bank_deposits.csv: line 2, column amount: Invalid money value '1.234'. Use dollars with exactly two decimal places, such as 1250.75.
```

**Likely cause:** The amount contains three decimal places.

**How to check:** Open `bank_deposits.csv` and inspect the `amount` field on
physical source line 2. Quoted multiline fields can make spreadsheet row numbers
differ from source line numbers.

**Fix:** Correct the fictional amount to exactly two decimal places, such as
`1.23`, then repeat the import. The failed import saved no partial records.

## T02: A count uses an unsupported denomination

**Symptom**

```text
cash_counts.csv: line 2, column denomination: Unknown denomination '3.00'. Use an allowed bill or coin value.
```

**Likely cause:** The denomination column contains a total or an unsupported
bill value rather than the value of one bill or coin.

**How to check:** Inspect that field in `cash_counts.csv`. Allowed values are
`100.00`, `50.00`, `20.00`, `10.00`, `5.00`, `2.00`, `1.00`, `0.50`, `0.25`,
`0.10`, `0.05`, and `0.01`.

**Fix:** Use the correct denomination and put the number of bills or coins in
`quantity`. For three one-dollar bills, use denomination `1.00`, quantity `3`.

## T03: The shift code was not imported

**Symptom**

```text
Unknown shift code 'DEMO-NO-SHIFT'. Check the imported shift codes.
```

**Likely cause:** A mistyped code or a different database was used with `explain`.

**How to check:** Look for the exact `shift_code` in `shifts.csv` and confirm
which `--db` path received that import.

**Fix:** Use an imported code, for example
`drawercheck explain 2026-09-03-R1 --db demo.db`, after reconciling that database.

## T04: SQLite is too old

**Symptom**

```text
SQLite 3.37.0 or newer is required; found 3.36.0. Use a Python installation with a newer SQLite.
```

**Likely cause:** Python was built with an older SQLite library. A recent Python
version alone does not guarantee the required SQLite version.

**How to check:** Run
`python -c "import sqlite3; print(sqlite3.sqlite_version)"` inside the environment.

**Fix:** Install a supported Python with SQLite 3.37.0 or newer, recreate the
virtual environment with it, and install `.[dev]` again. Do not remove the
version check or weaken the STRICT tables.

## T05: The database is locked

**Symptom**

```text
Database is locked. Close other database commands and try again.
```

**Likely cause:** Another process or an open database editor is holding a lock.

**How to check:** Look for another running import/reconciliation or a database
editor with an unfinished transaction using the same file.

**Fix:** Let that operation finish or close the editor, then retry. Do not
delete the database or its SQLite sidecar files to work around a lock.

## T06: The database cannot be written

**Symptom**

```text
Database is read-only. Choose a writable path with --db.
```

**Likely cause:** The database or its folder is read-only for your account.

**How to check:** Check the file and folder permissions, and confirm the path
does not point into a protected or read-only location.

**Fix:** Use a writable folder and a fresh fake-data database with `--db`, then
import and reconcile there. Keep all later commands on that same path.

## T07: A report cannot replace its output file

**Symptom**

```text
Cannot write report blocked.html: Permission denied. Choose a writable file path.
```

**Likely cause:** The output file or parent folder does not permit replacement.
The operating system supplies the detail, so other permission problems can have
different wording after the colon.

**How to check:** Inspect the output path and parent-folder permissions. The
folder must already exist, and the output must not be your database or a sidecar.

**Fix:** Choose an existing writable folder and retry, for example
`drawercheck report --db demo.db --format html --out review.html`.
A failed replacement preserves the previous report.

## T08: The requested report date has not been checked

**Symptom**

```text
No flags found. Run `drawercheck reconcile` first. First unreconciled date: 2026-09-01.
```

**Likely cause:** This date was never reconciled, or a new import cleared saved
results. Zero flags alone cannot prove a date was checked.

**How to check:** Confirm that reconciliation ran on the same database and
covered every requested shift or bank-entry date.

**Fix:** Run `drawercheck reconcile --db demo.db` without date filters, then
repeat the report. Earlier saved policy versions also require a fresh run.

## T09: A required CSV column is missing

**Symptom**

```text
cashiers.csv: line 1, column <header>: Missing required columns: display_name.
```

**Likely cause:** A header was removed, renamed, or exported with different text.

**How to check:** Compare the first line with the
[input contract](PROJECT_BRIEF.md#5-csv-input-contract-and-import-rules-folder-datademo).
For this file, the required columns are `cashier_id` and `display_name`.

**Fix:** Restore the exact header names and keep all seven required CSV files
together. Repeat the import into the intended database.

## T10: The configuration file is malformed

**Symptom**

```text
Invalid config bad.toml. Use a valid UTF-8 TOML file.
```

**Likely cause:** The file has invalid TOML syntax or invalid UTF-8 encoding.

**How to check:** Compare `bad.toml` with the repository's `config.toml`, looking
for unclosed section brackets, invalid quoting, or encoding problems.

**Fix:** Correct the file, or start from a copy of the example config, then run
`drawercheck reconcile --db demo.db --config bad.toml`. Values must also satisfy
the documented ranges; invalid values get their own specific messages.

## Informational notices and review leads

An identical file reported as `already imported; skipped` is not an error. A
missing config uses the built-in example defaults and reports that choice.
Missing counts and bank-deposit differences appear as review leads in reports
and explanations. They are not evidence about a person's actions.
