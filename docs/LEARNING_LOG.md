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

## M3 repair block: Review findings

- Built: Regression coverage and fixes for all seven reviewed issue groups:
  numeric config failures, bounded percentages, capped deposit lag, missing
  expected registers, unsafe terminal text, ambiguous identifiers, and clearer
  empty-range/database-setup errors. Added policy-version refresh handling and
  updated the plan, README, config comments, and calculation guide.
- Learned: A passing demo cannot cover every input boundary. Daily completeness
  needs an explicit expected-register list; a bounded Decimal must be checked
  before expansion; and valid multiline CSV text still needs safe terminal
  rendering. Saved flags also need refreshing when the review policy changes.
- Interview question: Why can a register's correct cash calculation still be
  insufficient to claim that the whole day's expected deposit is complete?

Verified on 2026-10-22 using the existing Python 3.13.5 / SQLite 3.47.1
environment. No dependencies, generated demo inputs, or web features changed.

| Command or check | Result |
| --- | --- |
| `.venv/bin/pytest -q tests/test_m3_fixes.py --tb=no` before the fixes | Reproduced: 94 failing and 7 passing cases across the reviewed boundaries. Three additional policy-refresh/preservation cases were added afterward. |
| `.venv/bin/pytest -q` | PASS: 401 tests, with ResourceWarning and cleanup warnings still treated as errors. The old empty-selection success case was replaced by explicit error/preservation coverage. |
| `.venv/bin/pytest --collect-only -q` through a captured subprocess | PASS: 401 tests collected. |
| `.venv/bin/ruff check .` | PASS: all checks passed. |
| `.venv/bin/ruff format --check .` | PASS: no formatting changes needed. |
| Installed CLI subprocess reproductions in a temporary directory | PASS: clean exit-1 errors for a 5,000-digit integer, an unrepresentable exponent, huge/tiny/over-precise percentages, excessive lag, unsafe text, padded IDs, empty ranges, and a tableless database. No tracebacks or raw terminal escape codes appeared. |
| Installed normal demo and worked explanation | PASS: 60 shifts and the same 12 expected flags; $518.75 expected, $498.75 counted, -$20.00 variance, and $1,198.75 contribution. |
| Installed missing-register and multiline-note workflow | PASS: a missing R2 shift gives an unknown daily deposit and a date-level R09 flag. A multiline note stays in the database and prints visible escapes, without creating a fake output line. |
| Saved results and policy refresh regressions | PASS: failed/empty requests preserve flags and markers; earlier M3 snapshots require reconciliation again, and a successful new-policy subset clears old-policy results. |
| `PRAGMA foreign_key_check` after the repaired subprocess workflow | PASS: no broken references. |
| `git diff --check` and source/document checks | PASS: no whitespace errors or prohibited punctuation; public functions have docstrings; instruction-file constraints are preserved. |

The new limits and expected-register roster are explicit demo policies, not
industry standards. LF/CR/tab remain valid in free-text CSV fields and are
escaped on terminal output. M4 text reports must reuse `terminal_text`; HTML
escaping and CSV formula protection remain required. M5 must still protect
calendar arithmetic near the maximum supported date.

After this update, run `drawercheck reconcile` without date filters to refresh
earlier M3 results. M4 remains the next milestone, awaiting **next**. No remote
CI or public-deployment result is claimed.

## M3 follow-up: Clear numeric config errors

- Built: A specific out-of-range-number message for numeric conversion failures,
  preserving the existing format error for malformed TOML or invalid UTF-8.
  Added four classification cases and tightened the CLI regression checks.
- Learned: Catching an exception prevents a traceback, but the message must
  still describe the actual cause so the user knows what to correct.
- Interview question: How would you distinguish invalid file syntax from an
  otherwise valid file containing a number your program cannot represent?

Verified on 2026-10-22. The focused config/repair suite passed 149 tests after
the change; the new classification tests first reproduced two failures on the
previous code while syntax/encoding cases passed. The final full suite passed
405 tests, both Ruff checks passed, and `git diff --check` passed. Installed CLI
subprocesses for a 5,000-digit integer and an unrepresentable exponent returned
exit 1 with the numeric message, without a traceback or an encoding claim.
The runtime dependencies, policy version, and next milestone are unchanged.

## M4: Reports and usable demo

- Built: Shared read-only report data; daily status/severity summaries, cashier
  over/short totals, and exact shift amounts; terminal-safe text, escaped offline
  HTML, and protected CSV exports; the `report` command with date selection and
  atomic file output; a real sample HTML report, design notes, and the README's
  three-step demo with an explicit screenshot placeholder.
- Learned: Zero saved flags cannot prove a date was checked, so reports must
  verify every selected completion marker. Output safety depends on the format:
  terminal escaping, HTML escaping, and CSV cell protection solve different
  problems. Known cash subtotals must also expose missing/open record counts.
- Interview question: How can three export formats share the same trustworthy
  results while each protects readers from a different kind of unsafe input?

Verified locally on 2026-10-22 with the existing Python 3.13.5 / SQLite 3.47.1
environment. No runtime or development dependencies were added.

| Command or check | Result |
| --- | --- |
| `.venv/bin/pytest -q` | PASS: 487 tests, retaining ResourceWarning and cleanup-warning failures. |
| `.venv/bin/pytest --collect-only -q` through a captured subprocess | PASS: 487 tests collected. |
| `.venv/bin/ruff check .` | PASS: all checks passed. |
| `.venv/bin/ruff format --check .` | PASS: no formatting changes needed. |
| Installed CLI subprocess demo with default paths in a temporary directory | PASS: `demo-data`, `import`, `reconcile`, and all three report formats work. The CSV contains 12 flag rows. Before reconciliation the report returns the required guidance with exit 1. |
| Installed CLI worked-date and output/error checks | PASS: September 3 shows $518.75 expected, $498.75 counted, and -$20.00 variance. Invalid date-selector combinations, missing output folders, and database output paths return exit 1 without tracebacks. Database contents stay intact. |
| Generated `examples/sample_report.html` | PASS: actual report from the full committed fake month, with 60 shifts, 30 dates, 12 core flags, an unknown September 25 deposit, and visible M5 scope notices. |
| HTML structure/resource and static contrast checks | PASS for semantic tables/captions/column headers, viewport, written severity labels, and no scripts or external assets. Ten declared light/dark text color pairs have contrast of at least 5.91:1. Correction from the M4 review: the malformed base selector prevented the light theme from applying, so these checks did not prove applied colors or a visible banner. See the repair entry below. |
| CSV and hostile-text regressions | PASS: every dangerous prefix in each exported column, protected headers, quoted commas/newlines, escaped HTML values, terminal controls, and multiline display text. |
| Readiness, incomplete-data, and resource tests | PASS: clean completed dates, partly unchecked ranges, old/mixed settings, saved-policy reuse despite a changed config, import invalidation, missing-register daily flags, unknown/open amounts, exact within-tolerance totals, connection closure, and no report mutations. |
| Output integrity tests | PASS: database and sidecar paths, symlink/hardlink aliases, unwritable output, atomic replacement failure, prior-output preservation, and temporary-file cleanup. |
| `PRAGMA foreign_key_check` after the installed CLI demo | PASS: no broken references. |
| `git diff --check` and source/document checks | PASS: no whitespace errors or prohibited punctuation, public functions have docstrings, the original brief is unchanged, and instruction-file constraints remain satisfied. |
| Browser visual preview | BLOCKED: the browser tool rejected the local `file:` URL under its security policy. No alternate browser route was used. Browser layout, narrow-screen appearance, keyboard behavior, and print rendering remain unverified. The README keeps a screenshot placeholder. |

M4 adds reports only. R04/R08 remain unimplemented M5 work, optional rules remain
unauthorized, and M7/M8's public app remains planned. No fresh-install matrix,
remote CI, screenshot, or public deployment is claimed.

Next milestone: **M5**, after the user says **next**.

## M4 repair block: Report review findings

- Built: Fixed the invalid base CSS selector, added the demo banner's fallback
  background, and regenerated the sample. Preserved existing output permission
  bits while new files respect umask, added the first unreconciled date to report
  errors, cached shift-code lookups, and shared the unknown-amount formatter.
- Learned: Checking declared color contrast does not prove a CSS selector is
  valid. Atomic replacement carries the temporary file's permissions, so those
  need deliberate handling without changing the process-wide umask.
- Interview question: How would you replace a generated report safely while
  preserving its permissions and keeping a failed write from destroying it?

Verified locally on 2026-10-22 in the existing environment. No dependencies,
reconciliation policies, demo inputs, or M5 features changed.

| Command or check | Result |
| --- | --- |
| Focused new regression cases before fixes | Reproduced: 9 failures and 2 passing cases covering CSS, banner fallback, missing-date guidance, and output permissions/failure handling. |
| `.venv/bin/pytest -q tests/test_reports.py` | PASS: 78 report tests. |
| `.venv/bin/pytest -q` | PASS: 498 tests, with connection/resource cleanup warnings still treated as errors. |
| `.venv/bin/ruff check .` | PASS: all checks passed. |
| `.venv/bin/ruff format --check .` | PASS: no formatting changes needed. |
| Permission subprocess regressions | PASS: new files use 0644, 0600, and 0664 under umasks 022, 077, and 002; replacements retain 0640 or 0600. Umask remains unchanged, and a permission-setting failure preserves the prior report and removes the temporary file. |
| Installed CLI subprocess demo in a temporary directory | PASS: partial reconciliation through September 10 reports the required guidance plus September 11 as the first unchecked date. Full reconciliation and all report formats still work, with 60 shifts, 30 dates, and 12 core flags. |
| Regenerated `examples/sample_report.html` | PASS: matches a fresh full-demo export apart from generation time; only the base selector, banner fallback, and timestamp differ from the previous sample. |
| `PRAGMA foreign_key_check` after the CLI demo | PASS: no broken references. |
| `git diff --check` and changed-source/document checks | PASS: no whitespace errors or prohibited punctuation, public functions have docstrings, instruction-file constraints hold, and the original brief is unchanged. |

Browser rendering remains unverified because of the previously recorded tool
restriction. These repairs add generated-stylesheet regressions, not a visual
accessibility audit. M5 remains the next milestone, awaiting **next**.
