# Learning log

## M0: Plan

- Built: The milestone plan, source notes, risks, and decisions before coding.
- Learned: Missing cash counts must stay unknown, and zero flags cannot prove
  that reconciliation has already run.
- Interview question: Why separate POS records, physical counts, and deposits
  instead of treating them as one total?

## M1: Project foundation

- Built: The installable package, help command, central errors, exact money
  helpers, safe connection helper, tests, and shared project instructions. Saved
  the original brief so future chats retain the exact requirements.
- Learned: `with con:` saves or rolls back a transaction; `closing(con)` closes
  the connection. Money parsing must reject invalid precision before conversion.
- Interview question: Why use integer cents and a strict decimal parser instead
  of floats for cash calculations?

Verified on 2026-10-22 using Python 3.13.5 and SQLite 3.47.1. Development tools
installed for this run: pytest 9.1.1 and Ruff 0.17.1.

| Command or check | Result |
| --- | --- |
| `PIP_CACHE_DIR=/private/tmp/drawercheck-pip-cache .venv/bin/python -m pip install -e '.[dev]'` | PASS: editable installation and development tools installed. The initial sandboxed attempt could not reach the package index; the authorized retry succeeded. |
| `.venv/bin/pytest -q` | PASS: 52 tests, with ResourceWarning and cleanup warnings treated as errors. |
| `.venv/bin/pytest --collect-only -q` | PASS: 52 tests collected. |
| `.venv/bin/ruff check .` | PASS: all checks passed. |
| `.venv/bin/ruff format --check .` | PASS: no formatting changes needed. |
| `.venv/bin/drawercheck --help` | PASS: installed console command prints help and exits 0. |
| `.venv/bin/drawercheck --unknown` through a subprocess check | PASS: exits 1, prints the central usage error to stderr, and prints no traceback. |
| `.venv/bin/python -m pip check` | PASS: no broken requirements found. |
| Temporary intentional-leak test, run with `pytest -q -c pyproject.toml` | PASS: the probe confirmed pytest exits 1 with a cleanup warning for the deliberate connection leak. The temporary test was then removed; it is not part of the passing suite. |
| Instruction and source checks | PASS: AGENTS.md is under 150 lines, CLAUDE.md contains only the shared import, the brief is copied unchanged, and the checked source/docs contain neither prohibited punctuation character. |

The milestone's test suite checks exact and invalid money values, SQLite integer
limits, decimal-context independence, connection closure, commit/rollback,
foreign keys on reopened connections, old SQLite rejection, and CLI help/errors.
Database tables for the application, imports, reconciliation, and reports are
scheduled for later milestones. GitHub CI and the Python version matrix are
scheduled for M6; those checks have not been claimed as passing here.

Next milestone: **M2**, after the user says **next**.

## Scope update: Public frontend (2026-10-22)

- Built: Updated the plan for a polished public app where visitors can upload
  synthetic CSVs, run checks, inspect results, and download reports. Added
  `docs/WEB_PLAN.md` and recorded the original brief's scope amendment.
- Learned: A static report host cannot execute the Python reconciliation
  workflow. The proposed Flask layer can reuse the core while keeping each
  visitor's run in a separate temporary workspace.
- Interview question: How can a command-line tool and public website share
  calculations while keeping different visitors' data separate?

This is a documentation-only scope update. M7/M8 implementation follows the
core milestones; M2 remains the next build milestone. No web packages have been
installed. Verification is document consistency, instruction length, and
`git diff --check`; the application test results above remain the M1 results.

## M2: Database, demo data, and imports

- Built: The nine STRICT tables and indexes; `init-db`, `demo-data`, and `import`;
  the committed 30-day fake inputs; source-specific validation errors; file
  hashes and duplicate checks; and all-or-nothing imports. Documented the
  scenarios and the distinction between current inputs and future flags.
- Learned: A file hash answers whether the exact bytes were imported before;
  record keys answer whether new input would duplicate an existing record.
  Both are needed. Table creation and import-log writes also belong inside the
  transaction so a late error cannot leave partially saved work.
- Interview question: Why are unique shift codes not enough to make repeated
  CSV imports safe and easy for someone to rerun?

Verified on 2026-10-22 using Python 3.13.5 and SQLite 3.47.1, with the existing
pytest 9.1.1 and Ruff 0.17.1 environment. No dependencies were added.

| Command or check | Result |
| --- | --- |
| `.venv/bin/pytest -q` | PASS: 160 tests, with ResourceWarning and cleanup warnings treated as errors. |
| `.venv/bin/pytest --collect-only -q` through a captured subprocess | PASS: 160 tests collected. |
| `.venv/bin/ruff check .` | PASS: all checks passed. |
| `.venv/bin/ruff format --check .` | PASS: no formatting changes needed. |
| `.venv/bin/drawercheck --help` | PASS: lists the three implemented subcommands. |
| `.venv/bin/drawercheck demo-data` | PASS: regenerated the seven default CSVs with stable LF line endings. |
| Installed CLI subprocess workflow using a temporary `--db` path | PASS: `init-db`, full 30-day `import`, and repeated `import` succeeded. The second import skipped all seven files and preserved every table count. |
| `PRAGMA foreign_key_check` after the full import | PASS: no broken references. |
| `git diff --check` and generated-file attributes | PASS: generated CSVs use LF; importer tests still cover Windows CRLF and BOM input. |

Actual row counts after the full default import were cashiers 5, registers 2,
shifts 60, POS totals 60, safe drops 60, cash counts 708, bank deposits 28,
flags 0, and import-log entries 7. The empty flags table is expected: M2 does
not run a reconciliation engine. The missing count and invalid closing time
remain stored for M3's integrity rules.

The suite exercises rollback after failures in each input file, rollback of a
new schema, missing files, empty/header-only files, BOM/UTF-8, malformed headers
and records, quoted commas/newlines, physical line numbers, duplicate keys,
unknown references/denominations, integer limits, strict dates/times, repeated
imports, changed-record conflicts, and invalidation of old calculated results.
CLI tests simulate locked/read-only failures for platform independence and
also exercise a real non-database file without overwriting it.

The default demo's data conditions and deposit windows are checked with fixed
dates. Rule-output expectations remain pending M3/M5. No network, current-day
assumptions, web implementation, or remote CI results are part of this milestone.

Next milestone: **M3**, after the user says **next**.

## M3: Core reconciliation and shift explanations

- Built: Validated example policies, shared immutable records, exact closing
  and daily deposit calculations, R01/R02/R05/R09, atomic saved flags and
  completion markers, inclusive date filters, and `reconcile`/`explain` commands.
  Added the formulas and rule explanations in `HOW_IT_WORKS.md`.
- Learned: Missing counts must stay unknown, while counted zero is real data.
  A saved settings snapshot makes later explanations consistent, and a separate
  completion marker proves that a zero-flag day was actually checked.
- Interview question: How would you keep a repeated reconciliation safe while
  ensuring a failed replacement cannot destroy the previous results?

Verified on 2026-10-22 using Python 3.13.5 and SQLite 3.47.1, with the existing
pytest 9.1.1 and Ruff 0.17.1 environment. No dependencies were added.

| Command or check | Result |
| --- | --- |
| `.venv/bin/pytest -q` | PASS: 298 tests, including the existing money, database, and import tests. ResourceWarning and cleanup warnings remain errors. |
| `.venv/bin/pytest --collect-only -q` through a captured subprocess | PASS: 298 tests collected. |
| `.venv/bin/ruff check .` | PASS: all checks passed. |
| `.venv/bin/ruff format --check .` | PASS: no formatting changes needed. |
| Installed `.venv/bin/drawercheck --help` through a subprocess | PASS: lists `reconcile` and `explain` alongside the three earlier commands. |
| Installed CLI subprocess workflow in a temporary directory | PASS: generated and imported the full fake month, reconciled twice, and explained the worked shift. The run saved 12 core flags across 60 shifts and 30 completion dates. |
| Installed `explain 2026-09-03-R1 --db PATH` | PASS: $518.75 expected, $498.75 counted, -$20.00 variance, and $1,198.75 deposit contribution. R01/R02 are present and R05 is absent. |
| Repeated import after reconciliation | PASS: all seven identical files were skipped and saved flags/settings/completion markers were unchanged. |
| Installed CLI error and incomplete-data checks | PASS: unknown shifts and invalid dates return exit 1 without tracebacks; the missing-count shift shows unknown cash and a clean completed shift explains successfully. |
| `PRAGMA foreign_key_check` after the subprocess workflow | PASS: no broken references. |
| `git diff --check` and source/document checks | PASS: no whitespace errors or prohibited punctuation in maintained source/docs; public functions have docstrings. |

New tests exercise threshold boundaries and rounding, low Decimal precision,
config validation and saved-setting round trips, zero versus missing counts,
open shifts, negative expected amounts, register overlaps across date filters,
adjacent shifts, duplicate closings, complete/incomplete deposits, and exact
M3 demo flags. They also check same-policy range replacement, changed-policy
invalidation, failure rollback after writes, connection closure on success and
failure, old M2 database upgrades, and real import-result invalidation.

Reports remain M4 work. R04 and R08 remain M5 work, and optional rules remain
unauthorized. No web implementation or remote CI result is claimed.

Next milestone: **M4**, after the user says **next**.
