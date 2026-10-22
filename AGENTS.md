# DrawerCheck

An offline Python cash-drawer reconciliation learning project using fake data.

## Start every task

1. Read [docs/PLAN.md](docs/PLAN.md) and [docs/LEARNING_LOG.md](docs/LEARNING_LOG.md).
   Read [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md) for the original requirements,
   including exact CSV columns, schema, rules, and demo scenarios.
2. Check `git status --short`, recent Git commits, and the relevant files before
   deciding what is complete. Preserve any existing user changes.
3. If asked "What is the next step?", explain the next unfinished milestone
   using the recorded progress. A status question does not authorize coding.
4. Read the user's latest request for authorization. Do not infer approval for
   another milestone from an earlier approval.

## Setup and checks

Use Python 3.12 or newer; develop on 3.13 or 3.14.

```sh
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
ruff check . && ruff format --check .
drawercheck --help
```

If needed, use `python3` for the first command after confirming its version.

## Code and data conventions

- Standard library only at runtime. Use `src/`, setuptools, and the `drawercheck`
  console script. Never add network calls at runtime.
- Small functions, descriptive names, type hints, and one-line docstrings on
  public functions. Use dataclasses, frozen where practical, for domain records.
- Store and calculate money as integer cents. Parse strict two-decimal dollar
  strings with `Decimal`; never use floats for money. Keep parsing and the one
  currency formatter in `src/drawercheck/money.py`.
- Keep all user-facing errors in `src/drawercheck/errors.py`.
- Check SQLite >= 3.37.0 before connecting. Use STRICT tables, `?` parameters,
  `PRAGMA foreign_keys = ON`, and `sqlite3.Row` on every connection.
- Own connections with `with closing(db.connect(path)) as con:` and use an inner
  `with con:` for transactions. A transaction block does not close a connection.
- Keep `-W error::ResourceWarning` in pytest configuration and explicit closure
  tests. Also fail on pytest's warning for an exception raised during cleanup.
- Use fake store, person, and record identities only. Never commit real business
  data. Ignore `data/private/`, databases, and SQLite sidecar files.
- Use `html.escape` on every dynamic HTML value. Reports must be self-contained
  and offline. Protect every CSV export cell with the shared `sanitize_cell`.
- Use neutral flag wording. Flags are leads for review, not findings about a
  person. Do not make claims about loss reduction, real use, or legal standards.
- Do not use em dashes or middle dots. Explain changes briefly in plain English.
- Keep this file under 150 lines. `CLAUDE.md` contains only `@AGENTS.md`.

## Milestone workflow

- Follow the milestones and decisions in [docs/PLAN.md](docs/PLAN.md).
- Complete one authorized milestone at a time. Ask only when blocked; otherwise
  choose the simplest option and record material decisions in the plan.
- After each milestone, run tests and both Ruff checks, add three learning-log
  bullets (built, learned, interview question), update plan progress, and commit.
- Summarize in at most five lines, then stop and wait for the user to say `next`.
- A block should take about 30 to 60 minutes. Split larger work rather than
  expanding scope. Do not build stretch rules without an explicit request.
- Report only checks actually run. Never claim remote CI success without seeing
  a real passing run.

## Project documents

- [Plan and decisions](docs/PLAN.md)
- [Original project brief](docs/PROJECT_BRIEF.md)
- [Learning log and verification](docs/LEARNING_LOG.md)
- [Setup and current features](README.md)
