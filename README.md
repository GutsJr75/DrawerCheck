# DrawerCheck

DrawerCheck is a personal learning project for checking end-of-shift cash drawers
with fictional data from **Demo Store #001**. The planned tool imports CSV files,
compares counted cash with POS totals, flags differences for human review, and
produces text, HTML, and CSV reports.

**Current milestone: M1, project foundation.** Installation, command-line help,
money helpers, and database connections are implemented. CSV import,
reconciliation, demo generation, and reports arrive in later milestones.

## Why I am building it

I worked two POS registers at a busy convenience store and counted cash at close.
I compared the cash in my register with transaction records.
This project lets me practice those careful checks in code and explain the work
in a job interview.

## Set up and check the foundation

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
development tools requires internet access during initial setup. The application
itself makes no network calls.

Running `drawercheck` without arguments also prints help. An invalid argument
prints a short error and returns exit code 1; successful help returns 0.

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
and scenario requirements for future work.
The three-step demo and sample report will be added in M4.
