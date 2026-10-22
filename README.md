# DrawerCheck

DrawerCheck is a personal learning project for checking end-of-shift cash drawers
with fictional data from **Demo Store #001**. The planned tool imports CSV files,
compares counted cash with POS totals, flags differences for human review, and
produces text, HTML, and CSV reports.

**Current milestone: M2, database and CSV imports.** Installation, money helpers,
database tables, fake demo generation, and validated CSV imports are implemented.
Reconciliation, flags, and reports arrive in later milestones.

A public browser demo is now planned after the core is complete. Visitors will
be able to run the built-in fake-data example or upload synthetic CSVs, inspect
the results, and download reports. This frontend is not implemented yet; see the
[approved web plan](docs/WEB_PLAN.md).

## Why I am building it

I worked two POS registers at a busy convenience store and counted cash at close.
I compared the cash in my register with transaction records.
This project lets me practice those careful checks in code and explain the work
in a job interview.

## Set up and check the project

Use Python 3.12 or newer; Python 3.13 or 3.14 is recommended for development.
The Python installation must include SQLite 3.37.0 or newer for STRICT tables,
which reject values that cannot be stored using the table's declared types.

From the repository folder:

```sh
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
ruff check . && ruff format --check .
drawercheck --help
```

If your system uses `python3` for a supported Python version, use that name in
the first command. The `[dev]` extra installs the test runner and code checker;
the installed application has no third-party runtime dependencies. Downloading
development tools requires internet access during initial setup. The command-line
core makes no network calls. The planned public web layer will be a separate
optional installation that handles browser requests.

Running `drawercheck` without arguments also prints help. An invalid argument
prints a short error and returns exit code 1; successful help returns 0.

## Generate and import demo inputs

After setup, run:

```sh
drawercheck init-db
drawercheck demo-data
drawercheck import --dir data/demo
```

The default generator writes 30 days starting at 2026-09-01, with seed 42 and two
registers. It writes the seven named CSVs in `data/demo`; existing files with
those names are replaced. Unrelated files in the folder are preserved.
`init-db` preserves existing records and is optional because `import` also
creates tables when needed. The default database is `./drawercheck.db`.

Run the import command again to see an `already imported; skipped` line for
each file. Identical inputs add no duplicate records and do not change the log.

For a separate dataset, choose a different folder and database path:

```sh
drawercheck demo-data --out data/another-demo --days 7 --seed 17
drawercheck import --dir data/another-demo --db another-demo.db
```

See the [demo scenarios](docs/DEMO_SCENARIOS.md) for the deliberately constructed
shortages, overage, deposit inputs, and incomplete records. M2 verifies the
input conditions; later milestones will calculate and store their flags.

## CSV import behavior

- Supply all seven files with the exact column names in the
  [input contract](docs/PROJECT_BRIEF.md#5-csv-input-contract-and-import-rules-folder-datademo).
  Column order may vary. Missing, extra, and duplicate headers are errors.
- UTF-8 files may include an Excel byte-order mark. Quoted commas, quoted
  newlines, Windows line endings, and fully blank records are supported.
- Money must use exactly two decimal places. Quantities must be nonnegative
  whole numbers, and counts may use only the specified bills and coins.
- Each validation error names the file, physical starting line, column, and
  reason. Header-only files are valid and report zero imported rows; an empty
  file is an error.
- All files and their import-log entries are saved in one transaction. A failed
  import leaves existing data unchanged. An unsuccessful first import may leave
  an empty database file, with no saved tables or records.
- File hashes compare exact bytes. A changed file is checked again, even if its
  only change is line endings. Existing records cannot be silently overwritten.
  Use new-record-only files or a fresh database for regenerated demo data.
- New imported records clear old flags and any completion markers. Identical
  skipped imports leave results unchanged. Reconciliation itself starts in M3.

## Foundation decisions

- Money is stored and calculated as integer cents. `parse_dollars("0.10")`
  returns the integer `10`, and `format_cents(125075)` returns `"$1,250.75"`.
- Dollar inputs require exactly two decimal places. The shared parser accepts
  negative amounts; later import handlers will enforce each column's sign rule.
- Database connections enable foreign keys and return rows accessible by column
  name. Use `contextlib.closing` to close a connection, with a separate inner
  transaction block to save or roll back changes.
- Tests treat leaked-connection warnings as errors.

## Scope and progress

This is a learning project using fake data, not a tool for real cash control.
Future flags will be neutral leads for human review. The project does not claim
banking, compliance, or accounting expertise, and it is not accounting or legal
advice. Example thresholds in later milestones will be configurable examples,
not industry standards.

The supported closing model will be one shift per register per business day.
Bank matching will be simplified; combined deposits and real banking calendars
are outside the MVP. There are no real POS or bank integrations.

See the [milestone plan](docs/PLAN.md) for scope and decisions, and the
[learning log](docs/LEARNING_LOG.md) for completed work and verification.
The [original project brief](docs/PROJECT_BRIEF.md) preserves the input contracts
and scenario requirements for future work. Its original web/hosting exclusions
were superseded by the public-frontend amendment in the current plan.
The three-step demo and sample report will be added in M4.
