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

## Design direction update (2026-10-22)

- Built: Recorded the approved beginner audience, minimal professional styling,
  four focused views, optional explanations, accurate plain-language labels,
  and future usability checks in `WEB_PLAN.md` and `DESIGN.md`. Linked the
  decision from the plan without changing milestone progress.
- Learned: Reducing clutter means showing relevant help at the right time while
  keeping errors, missing records, and the demo-data notice visible. Simpler
  labels must preserve the meaning of identifiers, amounts, and issue counts.
- Interview question: How would you make a cash-checking demo understandable
  to a first-time visitor without crowding the screen or hiding missing data?

This is a documentation-only update. M0 through M4 remain complete; M5 awaits
the user's explicit authorization. No application code, report styles, data,
dependencies, or deployment settings changed. Browser and participant usability
checks remain future work, not observed results.

Verification for this update: `.venv/bin/pytest -q` passed all 498 tests;
`.venv/bin/ruff check .` and `.venv/bin/ruff format --check .` passed. Reviewed
the documentation diff, checked local Markdown links and prohibited punctuation,
and ran `git diff --check`. The Frontend Design Premium static audit in strict
mode reported no findings; its JSON output is at
`/private/tmp/drawercheck-design-audit.json`. This is static evidence only, not
browser or usability verification. No new tests were added for this docs update.

## M5: Repeated shortages and bank deposits

- Built: R04 rolling cashier-history checks and R08 greedy deposit matching;
  stable bank-entry records and reads; full-history evaluation before date
  filtering; bank-only dates in saved results and reports; policy-version 3
  refresh handling; complete demo expectations and a regenerated HTML sample.
- Learned: A date filter selects results, not the evidence needed to calculate
  them. Matching must consume each bank entry once, leave ambiguity visible,
  and preserve unknown cash. An exact amount can still belong to the wrong day,
  so a concrete greedy-matching limitation belongs in the documentation.
- Interview question: How do you keep a single-day reconciliation consistent
  with a full-month run when cashier history and deposit windows cross dates?

Verified locally on 2026-10-22 using the existing Python 3.13.5 / SQLite 3.47.1
environment. No dependencies, schema tables, committed input CSVs, optional
rules, or web features were added or changed.

| Command or check | Result |
| --- | --- |
| `.venv/bin/pytest -q` | PASS: 542 tests, with ResourceWarning and cleanup warnings still treated as errors. |
| `.venv/bin/pytest --collect-only -q` | PASS: 542 tests collected. |
| `.venv/bin/ruff check .` | PASS: all checks passed. |
| `.venv/bin/ruff format --check .` | PASS: 44 files already formatted. |
| Full-pipeline golden test and documented scenario comparison | PASS: exactly 16 flags for S1 through S8, including date, shift, rule, and severity, with no optional or extra flags. Totals are 2 info, 7 warn, and 7 review. |
| R04 boundary/history tests | PASS: warning boundary, current-shift inclusion, short histories, custom settings, rolling expiry, other cashiers, unknown/open records, later nonshort records, same-date ordering, filtered runs, and saved explanations. |
| R08 matching tests | PASS: exact matches, signed mismatch/review boundaries, missing/unexpected entries, inclusive lag limits, ambiguity, stable exact-match preference/ties, unknown/nonpositive daily amounts, calendar-end clipping, and the equal-amount greedy failure example. |
| Range, policy, and bank-only tests | PASS: filtered matching cannot reuse an earlier day's entry; M4 snapshots require refreshing; dates without shifts have completion markers and exports without invented business activity or cashier records. |
| S9 repeated-import test | PASS: every application table count, saved flags, settings, and completion timestamps remain unchanged when all seven files are skipped. Reconciliation repeats without duplicate flags. |
| Installed CLI subprocess demo in a temporary directory | PASS: generated and imported 60 shifts, reconciled twice, exported text/HTML/CSV, and verified the worked shift plus pattern and deposit explanations. The CSV has 16 data rows; repeated import skips seven files and preserves all 30 completion dates. |
| Refreshed `examples/sample_report.html` | PASS: actual installed CLI export; matches a fresh full-demo report except for generation time. Shows all six required rules, no scripts/external assets, an unknown September 25 expected deposit, and the matching-limit notice. |
| `PRAGMA foreign_key_check` after the installed CLI demo | PASS: no broken references. |

Final source/document checks passed: `git diff --check`, local Markdown links,
prohibited-punctuation checks, public-function docstrings, unchanged original
brief and demo CSVs, and instruction-file limits. The Frontend Design Premium
strict static audit reported no findings. A final private helper-name cleanup
was followed by all 14 pattern tests and both Ruff checks, which passed.

Reports read saved flags instead of rerunning matching. Unexpected deposits are
dated by the bank entry, so default ranges include observed bank dates after
the last shift. No store operating calendar is inferred. Missing-deposit flags
refer to the imported dataset, with no claim that a real-world deadline passed.

Run `drawercheck reconcile` without date filters after updating from M3/M4 to
refresh older saved results. Bank matching remains deliberately simplified;
combined deposits, real banking calendars, and equal-amount ownership are not
resolved. Browser appearance, remote CI, the fresh-install version matrix, and
public deployment are not claimed as verified in this milestone.

Next milestone: **M6**, after the user says **next**.

## M5 repair: Exact matches before leftover review

- Built: The approved two-pass R08 policy: reserve every available exact match
  first, then review unresolved dates against remaining entries. Added one-cent
  and reservation regressions, plain less/more mismatch wording, a shared
  bank-only date label, policy-version 4 refresh checks, and a current sample.
- Learned: A day-by-day matching decision can describe ambiguity that later
  exact matches would resolve. Reserving those matches first makes the remaining
  review leads clearer while retaining the limits of greedy amount/date matching.
  A date without shifts needs a different label from a day with missing counts.
- Interview question: Why reserve exact deposit matches across all dates before
  classifying the remaining entries, and what errors can this still leave?

This is the separately authorized M5 repair approved on 2026-10-22, not the
start of M6. Plan decision 49 amends the original brief's matching sequence;
the original brief remains unchanged. No dependencies, database tables, fake
input CSVs, optional rules, or frontend screens changed.

| Command or check | Result |
| --- | --- |
| Focused deposit/bank-only regressions before the repair | Reproduced 13 failing and 19 passing cases covering matching order, mismatch wording, the initial M5 policy, and bank-only labels. |
| `.venv/bin/pytest -q` | PASS: 547 tests, retaining ResourceWarning and cleanup-warning failures. |
| `.venv/bin/pytest --collect-only -q` through a captured subprocess | PASS: 547 tests collected. |
| `.venv/bin/ruff check .` | PASS: all checks passed. |
| `.venv/bin/ruff format --check .` | PASS: 44 files already formatted. |
| Golden scenarios and sample consistency | PASS: exactly the same 16 default flags, including the missing September 16 deposit and September 21's review mismatch. The regenerated sample matches a fresh export except for generation time. |
| New matching-order regressions | PASS: later exact matches are reserved before an earlier mismatch or missing decision; ambiguity counts only remaining candidates. One-cent shortages and overages on September 2 each produce one warn mismatch, with other demo flags unchanged and filtered/repeated runs consistent. |
| Wording and saved-policy checks | PASS: text/HTML distinguish bank-only dates from unknown incomplete cash; mismatch messages say less/more while evidence retains signed cents. Policy versions 2 and 3 require reconciliation again; a successful subset refresh clears all prior-policy results before saving the selected dates. |
| Installed CLI subprocess default demo | PASS: 16 flags; text/HTML/CSV and `explain` use the new wording. `explain` already includes daily R08 leads, so no new explanation feature was needed. |
| Installed CLI subprocess modified CSVs | PASS: both one-cent directions give one warn lead for September 2, with signed evidence in `explain`. Bank-only dates use the new label; September 25's incomplete cash stays unknown. Foreign-key checks pass. |
| `git diff --check` and changed-source/document checks | PASS: no whitespace errors or prohibited punctuation; local Markdown links resolve; public functions have docstrings; the original brief, committed demo CSVs, and instruction-file constraints are preserved. |

The exact-match pass still breaks ties by bank-entry date then ID, and both
passes use full imported history before filtering output dates. The documented
equal-amount greedy failure, no-combined-deposits limitation, and calendar-day
lag remain. Reports keep unavailable cash as `None` internally and show
`Not calculated (no shifts)` only when there are no shifts on the date.

Run `drawercheck reconcile` without date filters to refresh earlier M3/M4 or
initial M5 results under policy version 4. Browser appearance, remote CI, and
public deployment are not claimed as verified by this repair.

Next milestone: **M6**, after the user says **next**.

## M5 follow-up: Visible daily deposit leads in explain

- Built: Moved the existing saved R08 leads beside the expected daily deposit
  under `Daily deposit review for YYYY-MM-DD`, with severity, message, and
  evidence. Kept other daily record leads separate and prevented duplicate output.
- Learned: A feature can already exist but be hard to notice under a generic
  heading. Putting the deposit lead beside its amount makes its scope clearer.
- Interview question: Why should a shift explanation distinguish that shift's
  cash difference from a bank-deposit lead that covers the whole date?

Verified locally on 2026-10-22: `.venv/bin/pytest -q` passed 549 tests, and both
Ruff checks passed. Two focused CLI regressions first failed on the missing
date-specific heading. An installed CLI run verified September 16's missing
deposit and September 21's mismatch, each printed once under the correct date.
`git diff --check` and prohibited-punctuation checks passed. Reconciliation,
saved policy version 4, the sample report, and the 16 golden flags are unchanged.
This is a small M5 presentation follow-up; M6 remains unstarted.

## M6: Core polish and local verification

- Built: A ten-entry troubleshooting guide with tests tied to exact CLI messages,
  a three-version GitHub Actions workflow, README setup/navigation/concept links
  and CI badge, a PASS/FAIL core checklist, and honest pitches, eight interview
  answers, three resume options, and suggested GitHub description/topics.
- Learned: A passing existing environment does not prove a fresh install works.
  Separate local clones and environments can test packaging and dependencies,
  while a configured hosted matrix still needs an observed remote run. Exact
  troubleshooting examples can be tested against the same messages users see.
- Interview question: How would you distinguish evidence from local tests,
  fresh-install checks, and a hosted CI run when describing project readiness?

The user authorized M6 on 2026-10-22. All local deliverables are complete, but the
required hosted CI observation is pending, so M6 is not declared fully closed.
No reconciliation logic, money calculations, saved-policy version 4, demo CSVs,
optional rules, or web features changed.

| Command or check | Result |
| --- | --- |
| `.venv/bin/pytest -q tests/test_troubleshooting.py` | PASS: all ten exact guide symptoms reproduced. SQLite lock/read-only and report replacement permission failures are simulated for platform independence; the real CLI translation paths are exercised. |
| `.venv/bin/pytest -q` | PASS: 559 tests with resource/cleanup warnings still treated as errors. |
| `.venv/bin/pytest --collect-only -q` through a captured subprocess | PASS: 559 tests collected. |
| `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .` | PASS: both checks clean. |
| Fresh local clone plus new Python 3.12.9 environment, SQLite 3.45.3 | PASS: editable `.[dev]` install, 559 tests, both Ruff checks, installed help, and `pip check`. |
| Independent fresh local clone plus new Python 3.13.5 environment, SQLite 3.47.1 | PASS: editable `.[dev]` install, 559 tests, both Ruff checks, installed help, and `pip check`. |
| Exact default demo/import/reconcile/date-range-report chain in both clones | PASS: 60 shifts, 30 completion dates, and 16 expected flags. Repeated imports skip all seven files and repeated reconciliation preserves results. |
| Installed S1 explanation in both clones | PASS: $518.75 expected, $498.75 counted, -$20.00 variance, and $1,198.75 contribution; R01/R02 present, R05 absent. |
| Installed text/HTML/CSV exports and foreign-key checks in both clones | PASS: 16 CSV rows, no broken references, all six required rule codes, and offline HTML matching the committed sample apart from generation time. Default demo CSV bytes remain unchanged. |
| Separate core-only fresh installation | PASS: no unconditional third-party runtime requirements, no pytest/Ruff/Flask installed, and the complete demo/import/reconcile/HTML command flow works. |
| CI workflow YAML parsing | PASS: YAML parses and declares Python 3.12/3.13/3.14. Release pages verified checkout v7.0.1 and setup-python v7.1.0; links are in the core checklist. |
| Hosted GitHub Actions run | FAIL: not observed. The connected repository has pull access but no push access; its workflow-runs API returned zero runs. The new local workflow has not been published. |
| Final source/document checks | PASS: `git diff --check`, local Markdown links, prohibited punctuation, and instruction-file limits. Runtime files, committed fake CSVs, the sample, and the original brief are unchanged. All source/test bytes match the verified snapshot; the ten troubleshooting tests and both Ruff checks passed again after the documentation results were recorded. |

Fresh verification used separate local clones of an isolated Git snapshot of
the M6 candidate files under a temporary directory. No existing environment or
cache was copied into the clones. Wheels were downloaded into the temporary
wheel folder, then the installs ran with `--no-index --find-links`. Fresh tools
were pytest 9.1.1 and Ruff 0.17.2, with setuptools 84.2.1 used during builds.
The existing repository environment retains Ruff 0.17.1. All runtime code and
tests match the verified snapshot; subsequent edits only record documentation
results. The isolated verification did not change the committed sample report.

`docs/CORE_CHECKLIST.md` lists seven PASS rows and one FAIL row for the original
core definition of done. Interview/sharing material is in
`docs/INTERVIEW_NOTES.md`; it makes no production-use or unobserved CI claims.
The screenshot remains an explicit placeholder. No local Python 3.14 run,
browser verification, public app, or deployment result is claimed.

Remaining M6 step: publish the reviewed local commit and observe all three CI
jobs. M7 remains unstarted and requires the user's separate instruction.

## M6 completion: Hosted CI observed

- Built: Recorded the successful hosted run, updated the final core checklist
  to eight PASS rows, and marked M6 complete in the README and project plans.
- Learned: Read-only GitHub access can inspect workflow runs and job logs without
  installing `gh`. A local Python 3.14 interpreter is not required to observe
  that version passing in hosted CI. Translation tests remain distinct from
  real operating-system lock/permission tests.
- Interview question: What evidence would you show to support the claim that
  this project passes on all three supported Python versions?

The user published commit `75c221c5e362345dffd6d420bd877d81a0628f6d`.
[Core checks run 1](https://github.com/GutsJr75/DrawerCheck/actions/runs/39912675717)
completed successfully on 2026-10-22 in America/Los_Angeles
(2026-10-23 06:38 UTC). The run SHA was checked against the local M6 commit.

| Observed hosted job | Result |
| --- | --- |
| [Python 3.12](https://github.com/GutsJr75/DrawerCheck/actions/runs/39912675717/job/120279029010) | PASS: install, lint, format check, 559 tests, and installed CLI help. |
| [Python 3.13](https://github.com/GutsJr75/DrawerCheck/actions/runs/39912675717/job/120279028772) | PASS: install, lint, format check, 559 tests, and installed CLI help. |
| [Python 3.14](https://github.com/GutsJr75/DrawerCheck/actions/runs/39912675717/job/120279029217) | PASS: install, lint, format check, 559 tests, and installed CLI help. |

Both the job-step conclusions and the test-summary lines in all three logs were
read. T05/T06 remain deliberately simulated SQLite failures to verify the guide's
actual message-translation paths; no extra real-lock test or application change
was needed. This update only records evidence in documentation. Earlier pending
CI statements above describe the initial handoff and are superseded here.

Documentation checks passed: `git diff --check`, local Markdown links,
prohibited punctuation, and both Ruff checks. Application tests were not rerun
for this evidence-only edit; runtime code, tests, and workflow bytes are unchanged
from the hosted commit whose three passing test logs were inspected.

M6 is complete. M7 remains unstarted, awaiting **next**.

## M7: Optional web requests and temporary runs

- Built: An optional Flask application factory with example/upload requests,
  fixed CSV filenames, bounded requests, isolated temporary databases, readable
  source errors, formatted results, shared shift explanations, and all three
  buffered reports. Added web tests to the existing three-version CI workflow
  and documented the response contract for M8.
- Learned: Deleting a run directory is only part of cleanup. A multipart parser
  can open temporary upload streams before it finishes building its file list;
  interrupted uploads need those streams explicitly tracked and closed. Keeping
  complete reports in the response allows downloads after server cleanup.
- Interview question: How can two visitors check different CSV files at the
  same time without sharing data or needing saved server-side run history?

The user explicitly authorized M7 on 2026-10-23. Verified locally with Python
3.13.5, SQLite 3.47.1, Flask 3.1.3, Werkzeug 3.1.9, Gunicorn 26.2.0, pytest
9.1.1, and Ruff 0.17.1. Flask/Gunicorn versions and upload-limit APIs were
checked against primary sources linked in `WEB_PLAN.md`. The optional packages
were installed after a restricted-network attempt failed and an authorized
network retry succeeded. Unconditional runtime dependencies remain empty.

| Command or check | Result |
| --- | --- |
| `.venv/bin/python -m pip install -e '.[dev,web]'` with the temporary pip cache on the authorized retry | PASS: optional dependencies and editable package installed. |
| `.venv/bin/pytest -q tests/test_web.py` during development | PASS: 51 web cases before two final policy/save-failure cases were added; the final full suite below includes all 53 web cases. |
| `.venv/bin/pytest -q` after the final code/tests | PASS: 612 tests, including 559 existing core cases and 53 web cases; resource and cleanup warnings remain errors. |
| `.venv/bin/pytest --collect-only -q` through a captured subprocess | PASS: 612 tests collected. |
| `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .` | PASS: both checks clean; 50 Python files formatted. |
| Full CLI versus example/upload parity using Flask's in-process client | PASS: all 60 shift calculations/explanations, 16 review leads, 30 dates, and exact text/HTML/CSV contents agree with a fixed generation timestamp. |
| Request and shift boundaries | PASS: valid multipart bodies at 2 MiB minus one byte and exactly 2 MiB pass; one byte over fails. Terminated WSGI streams without Content-Length remain bounded. Exactly 1,000 shifts pass; 1,001 fail before reconciliation. |
| Upload validation and content protection | PASS: missing/duplicate/unexpected files, extra fields/options, path filenames, malformed/empty/invalid-encoding CSVs, multipart parser bounds, BOM/CRLF/raw bytes, physical multiline source locations, unknown IDs, HTML escaping, and protected CSV cells. |
| Cleanup and isolation | PASS: simultaneous distinct runs cannot mix results or touch a local database. Connections and upload streams close on success/failure, temporary directories disappear, and a partially saved upload is removed. Unexpected exception text and internal paths are absent from responses/logs. |
| Amount and policy handling | PASS: unknown counts remain unknown, recorded zero stays $0.00, bank-only dates invent no shifts, and local config.toml cannot change the built-in web policies. |
| Fresh core-only wheel installation in a new virtual environment | PASS: installed with `--no-index --no-deps`, confirmed Flask/Gunicorn/pytest/Ruff absent, and ran installed help, demo-data, import, reconcile, worked explanation, and HTML report. The result remains 60 shifts and 16 flags. |
| `.venv/bin/gunicorn --check-config 'drawercheck.web:create_app()'` | PASS: the application factory loads with Gunicorn; no public server or deployment was started. |
| `.venv/bin/python -m pip check` | PASS: no broken requirements. |

The interrupted unknown-length upload test first failed with unclosed parser
streams. A small Flask Request subclass now closes every opened upload stream,
including files never assigned to `request.files`. A separate test-client
multipart-encoding temporary file also needed explicit closure in the tests;
the warning policy was not weakened. Internal HTTP errors retain their status
and method headers while returning plain JSON messages.

M7 is complete with local evidence. CI first runs the core with only `.[dev]`,
then installs `.[dev,web]` and explicitly runs the web suite on Python
3.12/3.13/3.14. This updated workflow has not yet been observed on GitHub; the
earlier hosted result remains M6 evidence only. No local Python 3.12/3.14 web
test run, browser interface, usability check, or public deployment is claimed.

M8 is next, awaiting **next**. The request layer exposes no browser screen yet.

## M7 repair: Workload bounds and plain CSV errors

- Built: Pre-database web caps for shift/deposit/drop records; full-key duplicate
  lookup indexes for new and existing databases; grouped flag/date/shift lookups;
  and plain web explanations for headers, malformed quoting, encoding, and long
  values. Added regression tests and updated the request contract and decisions.
- Learned: A small byte count can contain many records and produce much larger
  results. Limits must reject excess records before costly work starts. An index
  on only a shared date or shift can still scan many similar records, so the
  full lookup key matters. CSV records can span multiple physical source lines.
- Interview question: How would you prove that a lookup stays efficient without
  making a test depend on the speed of the machine running it?

The user authorized this focused repair after reporting that M7 had been pushed.
This repair was verified locally on 2026-10-23 with the existing Python 3.13.5,
SQLite 3.47.1, Flask 3.1.3, and Werkzeug 3.1.9 environment. No dependencies,
calculation policies, generated demo inputs, or M8 implementation changed.

Before the repair, an in-process reproduction with 60 example shifts and 2,000
bank rows took 0.567 seconds and returned 2,645,808 bytes; 8,000 bank rows took
6.365 seconds and returned 10,055,808 bytes. Query plans showed full scans for
both duplicate checks. Exact header and unclosed-quote messages also reproduced.

| Command or check | Result |
| --- | --- |
| New focused regression selection before the fix | Reproduced: 12 failures and 5 passes. Four duplicate lookups exceeded the database-work budget, four excessive-record uploads reached database opening, and four web errors exposed internal wording. |
| `.venv/bin/pytest -q tests/test_workload.py tests/test_web.py tests/test_importer.py tests/test_reports.py tests/test_reconcile.py` | PASS: 260 focused cases before the final long-value wording case and stronger pre-database shift assertion were added. |
| `.venv/bin/pytest -q` after the final code/tests | PASS: 630 tests, with resource and cleanup warnings still treated as errors. Includes the complete golden demo, web/CLI report parity, ten exact CLI troubleshooting symptoms, cleanup, and concurrency cases. |
| `.venv/bin/pytest --collect-only -q` through a captured subprocess | PASS: 630 tests collected. |
| `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .` | PASS: both clean; 51 Python files formatted. |
| Record boundaries and pre-database rejection | PASS: 1,999 and 2,000 bank/drop records succeed; 2,001 and 20,000 return 400 without calling db.connect. The existing 1,000/1,001 shift boundary now also checks rejection before database opening. |
| CSV counting and web wording | PASS: BOM, CRLF, blank lines, and 2,000 quoted multiline records stay valid. Header, encoding, unclosed-quote, other malformed-quote, and overlong-value messages use the intended plain descriptions and preserve source lines. |
| Concentrated duplicate lookups and database upgrades | PASS: lookups across 2,000 rows sharing a date/amount or shift/amount/time stay below 1,000 SQLite VM operations. Tests cover new indexes and adding them back to an existing populated database with repeated init-db. No clock-based test deadline is used. |
| Repeated public-request performance reproduction | Observed: 2,000 bank rows still succeed in 0.218 seconds; 8,000 and 20,000 rows now return 400 in 0.007 and 0.009 seconds, respectively, with 164-byte error responses. Timings are local observations, not hosting guarantees. |
| Uncapped core pipeline with 8,000 bank rows | PASS: import, reconcile, load, and all three report renderers completed in 0.633 seconds, with 8,040 flags across 8,030 dates and summary counts agreeing with saved flags. Web caps do not restrict the CLI. |
| Documentation and instruction checks | PASS: git diff --check, local Markdown links, prohibited punctuation, AGENTS.md length, and the shared CLAUDE.md import. |

The prevention is now executable: record caps run in the shared CSV reader before
any connection opens, and duplicate-lookup tests cap SQLite work rather than
elapsed time. Shared grouping preserves lead order and avoids repeated scans.
The web displays translated messages; raw source-column tags remain structured
metadata, and CLI error text remains unchanged.

No hosted CI result is claimed for this repair commit. M8 still awaits **next**;
its frontend, deployment timeout, and Content-Security-Policy remain later work.

## M7 repair: Roster caps and response budget

- Built: Pre-database caps of 5 registers and 100 people; a web-only 256-character
  field limit; an early bound on expanded overlap/multiple-closing details; and
  a 10 MB complete-response budget with short errors instead of partial results.
  Applied the schema's natural POS/count row maxima before database work, so all
  seven files are capped. Added combined-limit, escaping, roster, calculation,
  and response-boundary tests.
- Learned: Limits can multiply: expected registers create review leads across
  dates, and long IDs repeat in evidence and reports. One stress fixture is
  useful but cannot prove every allowed input stays small. Early expansion
  limits and a final serialized-byte budget cover different parts of the work.
- Interview question: Why would you check both input size and output size for
  a public service that expands uploaded records into explanations and reports?

The user authorized this contained follow-up on 2026-10-23. The existing Python
3.13.5 / SQLite 3.47.1 / Flask 3.1.3 environment was used. No dependencies or
calculation policies changed. The CLI's normal calls omit the optional field
and calculation budgets; the public web factory supplies them explicitly.

The initial read-only assessment measured a combined fixture with 1,000 shifts
on 1,000 dates, 2,000 bank entries, 2,000 drops, and 100 people: 10 registers
returned 13,054,247 bytes, while 5 returned 8,197,238 bytes. During regression
development, using 256-character HTML-escaped register IDs with only 5 registers
reproduced a 19,611,238-byte response before the response guard was added.

| Command or check | Result |
| --- | --- |
| New regression selection before repair | Reproduced missing roster/field caps and missing output-budget enforcement. The normal combined fixture passed; long escaped IDs exceeded 10 MB. An overlap test fixture's timestamp column mapping was corrected before testing the calculation guard. |
| `.venv/bin/pytest -q tests/test_workload.py tests/test_web.py` | PASS: 97 focused cases before two core-default checks and four POS/count limit cases were added. The final six-case POS/count and combined-fixture selection also passed. |
| `.venv/bin/pytest -q` | PASS: 662 tests, including 32 added in this follow-up, with resource/cleanup warnings still treated as errors. Normal demo, CLI/web parity, exact troubleshooting messages, rollback, and isolation checks remain passing. |
| `.venv/bin/pytest --collect-only -q` through a captured subprocess | PASS: 662 tests collected. |
| `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .` | PASS: both clean; 51 Python files formatted. |
| Roster and field boundaries | PASS: 4/5 registers and 99/100 people succeed; excess rosters, including 1,000 extra records, fail before db.connect. A 257-character field also fails before db.connect; the escaped-ID case reaches the response guard with 256-character values. |
| Shift-detail work bounds | PASS: 1,000 same-day closings and 1,000 cross-date overlapping shifts are rejected before rule evaluation. Nine smaller boundary cases verify exact overlap-only, closing-only, and combined reference counts and default uncapped calculations. |
| Complete response boundary | PASS: the exact serialized byte count and one byte more are accepted; a budget one byte smaller returns the short 400 error. A separate test checks oversized error responses and no-store headers. |
| Combined-cap reproduction after repair, filling all seven row caps | PASS: ordinary identifiers return a complete 8,196,971-byte response; escaped long identifiers return a 136-byte 400 error. Local observations were 0.931 and 0.990 seconds, respectively; these are not hosting guarantees. |
| Default core behaviour beyond web limits | PASS: uncapped imports/reconciliation accept 6 registers, 101 people, and a 257-character name. Default calculations also retain all 1,012 other-shift references in a 23-shift overlap case; applying the optional 1,000-reference budget rejects it. |
| Natural POS/count limits before database work | PASS: the combined fixture fills 1,000 POS rows and 12,000 count rows. One extra row or 1,000 extra rows in either file is rejected before db.connect; all four excess-row tests first failed when those early caps were absent. |
| Final documentation checks | PASS: git diff --check, local Markdown links, prohibited punctuation, AGENTS.md length, and the shared CLAUDE.md import. |

The combined fixture has 5 registers, 100 people, 1,000 shifts on 1,000 dates,
2,000 bank entries, 2,000 drops, 1,000 POS rows, and 12,000 count rows. Its assertion measures the full response,
including the three reports and JSON escaping. Temporary-workspace assertions
and ResourceWarning failures also apply to response/detail-limit rejection cases.
The 10,000,000-byte response buffer does not imply a 10 MB process-memory limit:
report strings and parsed records also occupy memory. Input field and expanded
relationship limits prevent the earlier uncontrolled amplification paths.

This repair is verified locally. No new hosted CI, browser, or deployment result
is claimed. M8, including timeout and CSP configuration, still awaits **next**.

## Follow-up: Hosted CI for M7 and clearer status docs (2026-10-23)

The earlier M7 notes said the updated workflow had not been observed on GitHub.
It has now been observed through the GitHub Actions API:

| Commit | Run | Result |
| --- | --- | --- |
| `7406cc3` M7 request layer | [39926469611](https://github.com/GutsJr75/DrawerCheck/actions/runs/39926469611) | success |
| `3922a86` record caps and grouped lookups | [39928859925](https://github.com/GutsJr75/DrawerCheck/actions/runs/39928859925) | success |
| `2bdbb7a` roster caps and response budget | [39932017056](https://github.com/GutsJr75/DrawerCheck/actions/runs/39932017056) | success; the Python 3.12, 3.13, and 3.14 jobs each passed, including "Test optional web requests" |

The README was reorganized for first-time readers: a status table, the
three-step demo near the top, a plain table of what each rule looks for, and
the web limits as a table. PLAN.md and WEB_PLAN.md now open with a short
"Where things stand" section. No code or behavior changed.

## Design rules for M8 (2026-10-23, documentation only)

- Built: a WCAG 2.2 AA target, colour tokens with calculated contrast, IBM Plex
  typography, spacing and component rules, and signature elements in
  `DESIGN.md`; navigation, upload, loading, data, and security-header rules in
  `WEB_PLAN.md`; and decision 59 in `PLAN.md`. No code changed.
- Learned: a minimal design looks generic when it has no point of view. Drawing
  the visual identity from the task itself (a till tape and a count sheet) adds
  character and teaches beginners at the same time. Form-control borders need
  their own darker colour, because divider colours rarely reach 3:1 contrast.
- Interview question: How did you make the website feel distinctive while
  keeping it accessible and keeping all money calculations on the server?

Review refinements applied the same day: the first-visit wait belongs to
Render's own loading page (about one minute, per its documentation), Cancel
only stops the browser waiting, 400% desktop zoom is checked separately from
200% text resizing, and the combined-limits response (measured at 8,196,971
bytes, about 1.8 MB under the 10 MB budget) must stay within budget after the
M8 additions. Labels will be sent once as a lookup to save roughly 400 KB.

## M8 block 1: Screen data and page layout

- Built: Python now sends count-sheet line totals, a results summary (drawers
  checked, drawers needing review, leads by severity, days with deposit leads),
  and one lookup of public words for every rule, severity, and status. Added
  the page layout with colour tokens, self-hosted IBM Plex fonts, the demo
  notice, the footer, package data, and the planned security headers.
- Learned: A test can guard a design rule as well as a calculation. The colour
  tokens are rechecked for contrast from the stylesheet itself, and a packaging
  test fails if a new static file would be left out of an installed copy.
  Serving the page from the app's own address keeps a strict style policy
  possible, because nothing needs inline code.
- Interview question: How would you prove that a web page meets its colour
  contrast and "no third-party requests" rules every time someone changes it?

The user authorized block 1 on 2026-10-23. Verified locally with Python 3.13.5,
Flask 3.1.3, Gunicorn 26.2.0, pytest 9.1.1, and Ruff 0.17.1. Fonts came from
IBM's GitHub releases `@ibm/plex-sans@1.1.0` and `@ibm/plex-mono@2.5.0`; this
was the only download for the site. The Mono zip matched GitHub's published
SHA-256 (`6d23f012...`); the Sans release publishes none, and its measured
SHA-256 was `fb365d91...`.

| Command or check | Result |
| --- | --- |
| `.venv/bin/pytest -q` | PASS: 674 tests, 12 of them new, with resource and cleanup warnings still treated as errors. |
| `.venv/bin/pytest --collect-only -q` | PASS: 674 tests collected. |
| `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .` | PASS: both clean; 52 Python files formatted. |
| Screen fields against the CLI | PASS: the demo summary is 60 drawers, 4 needing review, 16 leads (2, 7, and 7), and 2 deposit-lead days, matching the CLI's saved flags. Line totals add up to the counted cash for every demo shift, and the uncounted shift has none. |
| Combined-limits response size | PASS: 8,539,525 bytes (was 8,196,971), about 1.46 MB under the unchanged 10 MB budget; the existing guard test is unchanged. The demo response is 156,611 bytes. |
| Page, headers, and assets | PASS: one `h1`, `lang="en"`, a skip link, the demo notice, and the footer; no inline scripts, styles, or event attributes; the exact planned Content-Security-Policy and `Referrer-Policy: no-referrer` on the page, a static file, and the API. |
| Budgets and contrast | PASS: CSS 6,472 bytes (no JavaScript yet) against 60 KB; fonts 78,660 bytes against 200 KB. Fourteen token pairs meet WCAG 2.2 AA contrast in both themes. |
| Wheel build and fresh install | PASS: the wheel contains the template, CSS, four fonts, and licence. Installed into a new virtual environment, it served the page, a font, and the demo summary. |
| `.venv/bin/flask --app drawercheck.web:create_app routes` | PASS: lists `/`, `/static/<path:filename>`, and both API routes. |
| Headless Firefox screenshots through local Gunicorn | Observed: light and dark at 1,280 px and 320 px wide render Plex fonts with no sideways scrolling. The access log shows only four local requests: the page, the stylesheet, and the two Sans fonts. |

The Playwright and frontend-design plugins were installed but not loaded into
this session, so the frontend-design guidance was read from its installed file
and Firefox's built-in headless screenshot was used instead of Playwright. That
was a visual look only. Keyboard, zoom, screen-reader, and automated
accessibility checks have not been run and remain block 5. No hosted CI or
deployment result is claimed. Block 2 waits for **next**.

## M8 block 2: Start and Prepare files

- Built: The Start view with "Try the example" and the example drawer tape,
  and the Prepare files view with a seven-file checklist, rename hints, an
  error summary that links to the problem row, and example downloads produced
  by the demo generator. Browser messages joined the server's in `errors.py`.
- Learned: A page can show calculated numbers without calculating them, if a
  test compares every number on the page with the server's own result. A status
  list must describe the latest attempt: a file the server reported needs to
  stop counting as ready, and go back to ready when it is sent again.
- Interview question: How do you keep a browser's file checklist honest when
  only the server is allowed to judge what is inside the files?

The user authorized block 2 on 2026-10-23. Verified locally with the same
Python 3.13.5, Flask 3.1.3, Gunicorn 26.2.0, pytest 9.1.1, and Ruff 0.17.1
environment, plus Firefox 158.0.1 and Node 22.22.0 for browser checks.

| Command or check | Result |
| --- | --- |
| `.venv/bin/pytest -q` | PASS: 681 tests, 7 of them new, with resource and cleanup warnings still treated as errors. See the note on slow exits below. |
| `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .` | PASS: both clean; 52 Python files formatted. |
| `node --check src/drawercheck/static/app.js` | PASS: the script parses. |
| Start tape against the server | PASS: all nine amounts and the "Short / Needs review" line equal the `/api/demo` values for `2026-09-03-R1`, and the "60 drawers on two registers" sentence matches the demo. |
| Prepare checklist and example downloads | PASS: rows follow the seven CSV names; each `/examples/<file>` download is byte-identical to the committed demo CSV; other names, wrong capitals, and an encoded path return the JSON 404. Browser messages on the page equal their `errors.py` constants. |
| Script safety | PASS: `app.js` contains no `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval(`, `new Function`, or `parseFloat`. |
| Budgets | PASS: CSS 13,466 bytes and JavaScript 8,734 bytes (22,200 together) against 60 KB. |
| Headless Firefox through WebDriver BiDi, local Gunicorn, light and dark | Observed: the example run changes the button to "Checking the example...", then shows Results with focus on its heading. A wrongly capitalised file gets the rename hint and an unknown file is refused. Missing files produce the linked error summary, and the link focuses the row. A bad amount on source line 3 of `bank_deposits.csv` marks that row Problem with "6 of 7 files ready". A cross-file problem fixed in another file returns the row to Ready. No sideways scrolling at 320 px. All requests stayed on the local site; the only miss was the browser's automatic `/favicon.ico` request (404, as the site has no icon yet). |

**Slow exits, cause not found.** In 4 of the first 7 full runs during this
block, every test passed in about 10.5 seconds, but the process took about 909
seconds of wall time to end, with only about 9 seconds of CPU time. A
60-second stack-dump timer armed before the tests never fired, so the wait was
outside the test code: either before the timer was armed or late in Python's
shutdown. Eleven later runs did not stall. Ten of them recorded timestamps at
start, after pytest returned, and in the last exit handler, five with pytest's
cache plugin and five without; each ended within 0.1 seconds of pytest
returning, with only the main thread alive. No server or headless browser
from these checks was left running. The steady ~900-second figure looks like
a timeout in the local environment, not in DrawerCheck, but that is unproven.
The CI workflow's 10-minute job limit would expose the stall if it ever
happens there.

These browser checks used scripted clicks and file selection, not a person's
keyboard or a screen reader. Focus order, zoom, screen-reader announcements,
and an automated accessibility scan remain block 5. No hosted CI or deployment
result is claimed. Block 3 waits for **next**.

## M8 block 3: Results and Drawer details

- Built: Results with the plain-facts line, leads by level, every lead in
  priority order, and day and cashier tables that fill when opened. Drawer
  details with the tape (each label opens its meaning), the count sheet with a
  bookkeeping total line, this drawer's and the whole day's leads, and plain
  sentences on limits and the bank deposit. Both tapes share one `TAPE_LINES`
  list in Python.
- Learned: Missing data needs its own words at every level: "unknown" in a
  cell, a sentence saying why, and no count sheet instead of a sheet of zeros.
  Screen readers also need separators that sighted visitors get from spacing,
  such as the hidden commas between the lead counts.
- Interview question: How do you show a calculation step by step in a browser
  without letting the browser do any of the arithmetic?

The user authorized block 3 on 2026-10-23. Verified with the same local
environment as block 2: Python 3.13.5, Flask 3.1.3, Gunicorn 26.2.0, pytest
9.1.1, Ruff 0.17.1, Firefox 158.0.1, and Node 22.22.0.

| Command or check | Result |
| --- | --- |
| `.venv/bin/pytest -q` | PASS: 683 tests, 2 of them new, in 10.4 seconds; the process ended normally (10.6 seconds wall time). |
| `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .` | PASS: both clean. Ruff now reports 53 files because it also reads `docs/screenshots/README.md`. |
| `node --check src/drawercheck/static/app.js` | PASS. |
| Shared tape and Results hooks | PASS: both tapes list the same nine lines in order; every Drawer details label opens its exact `TAPE_LINES` definition; every `data-fact` and `data-status` slot names a field the server sends. |
| Budgets | PASS: CSS 17,596 bytes and JavaScript 20,891 bytes (38,487 together) against 60 KB. |
| Headless Firefox through WebDriver BiDi, local Gunicorn, light and dark | Observed: Results shows 60 drawers checked, 4 drawers need review, 16 leads, and 2 deposit-lead days, matching `summary`; all 7 "Needs review" leads come first; the two whole-day leads have no drawer button. Drawer `2026-09-03-R1`: all nine tape amounts and all twelve count rows equal the `/api/demo` values, the total is $498.75, and the limits and deposit sentences use $1.00, $12.50, $1,198.75, and $2,698.27. Drawer `2026-09-25-R1` shows "unknown" for counted cash and difference, no count sheet, and the reason. An upload without September 3's deposit shows a whole-day lead on that drawer. Day table 30 rows, cashier table 4 rows. No sideways scrolling at 320 px on Results or Drawer details. |
| Fixes found by looking at the screenshots | Bills and coins were right-aligned under a left heading; the hidden tape caption left a gap; a definition stayed open on the next drawer; screen readers would have heard "7Check 7Note". All four were fixed and the run repeated. |

Screenshots are in `docs/screenshots/2026-10-23-m8-block3/` (14 images, about
4.7 MB, mostly tall full-page Results images). Keyboard order, zoom, screen
readers, and an automated accessibility scan remain block 5. No hosted CI or
deployment result is claimed. Block 4 waits for **next**.

## M8 block 3 repair: Outside review findings

- Built: Fixes for an outside review of blocks 1 to 3, each claim verified in
  the code and in Firefox first. The deposit sentence now names the real reason
  a share is unknown; the tape's status line wraps at 320 px; tape labels and
  error links meet the 24 px target rule; script-focused headings and the error
  summary show no ring; and stale Start errors and hidden labels are cleared.
- Learned: A layout check on one example drawer is not a layout check on every
  drawer: the only demo drawer that is balanced and needs review was the one
  that broke at 320 px. Focus rings also depend on how a button is pressed, so
  checks need real mouse and keyboard input, not scripted clicks.
- Interview question: When an outside reviewer reports problems, how do you
  decide which to fix, which to reword, and which to decline?

The user authorized this repair on 2026-10-23. Same local environment as block
3. Review item 5c (an empty file-input change after cancelling the dialog) was
not changed: browsers fire `cancel` there, and the script already empties the
input after each choice.

| Command or check | Result |
| --- | --- |
| Before the repair, in Firefox | Reproduced: drawer `2026-09-27-R2` made the page 362 px wide at 320 px; tape labels and error links were 22 px tall with 2 px between error links; a heading ring appeared after keyboard Enter but not after a real mouse click. `2026-09-25-R2` was counted ($5,493.47) but would have been told its counted cash was unknown. |
| `.venv/bin/pytest -q` | PASS: 683 tests in 10.8 seconds; the contrast test now also checks the review colour on page and panel backgrounds, and a page test checks all four deposit sentences. |
| `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .` | PASS: both clean. |
| `node --check src/drawercheck/static/app.js` | PASS. |
| Headless Firefox through WebDriver BiDi with real pointer and key input, light and dark | Observed: no link, button, summary, or file-chooser label under 24 x 24 px on Start, Prepare files with the error summary, Results with every section open, or Drawer details; error links 24 px tall with 8 px gaps. All nine drawers that Results can open, and Results itself, are exactly 320 px wide at 320 px. Headings and the error summary show no ring after mouse or keyboard; the checklist row reached by an error link does. A failed example run's error clears on returning to Start. An upload with an open drawer and an incomplete day gives the four deposit sentences: still open (`2026-09-29-R1`), no count (`2026-09-25-R1`), counted but day incomplete (`2026-09-25-R2`, $5,473.47 counted), and complete (`2026-09-03-R1`, $1,198.75). |
| Budgets | PASS: CSS and JavaScript together 39,517 bytes against 60 KB. |

Screenshots are in `docs/screenshots/2026-10-23-m8-block3-repair/` (6 images,
about 1.4 MB). Block 4 will extend the 320 px check to all 60 drawers once
every drawer has an address. Block 4 waits for **next**.

## M8 block 4: Navigation and states

- Built: `#/` addresses for every view, so Back, Forward, refresh, and copied
  links work; date and level filters that replace the address; report
  downloads made in the browser from the response; Cancel, a slow-start notice,
  and a time limit with "Try again"; and drawer links on whole-day leads plus
  an All drawers section, so every drawer can be opened.
- Learned: Cancel has to end the wait itself, not wait for the network to give
  up, and any answer that arrives afterwards must be ignored. A copied link is
  a promise the page may not be able to keep, so it needs an honest message
  ("Results are not saved") rather than an empty screen.
- Interview question: How do you make a single-page app's Back button,
  refresh, and copied links behave the way visitors expect when nothing is
  saved on the server?

The user authorized block 4 on 2026-10-23. Same local environment as block 3.
The browser checks used real pointer clicks and, for waiting, a deliberately
slowed `fetch` in the page that ignores Cancel, so late answers really arrive.

| Command or check | Result |
| --- | --- |
| `.venv/bin/pytest -q` | PASS: 684 tests in 11.7 seconds; a new page test checks the timing attributes against `web.py`, one download button per report, `#/` view links, and the waiting and missing-results wording. |
| `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .` | PASS: both clean. |
| `node --check src/drawercheck/static/app.js` | PASS. |
| Addresses and history in Firefox | Observed: the example run adds one history entry and lands on `#/results` with focus on its heading. Choosing "Needs review" and then September 16 changes the address to `#/results?date=2026-09-16&show=review` with no new history entries and shows 1 lead with links to both of that day's drawers. Following a link opens `#/drawer/2026-09-16-R1` with the day's deposit lead; the browser's Back returns to the filtered results and Forward to the drawer. A "Note" filter on that date shows the empty state; "Show all leads" restores all 16 and moves focus to the date list. A bad filter address falls back to `#/results`. |
| Missing results and odd addresses | Observed: reloading on a drawer address and opening a copied results link both show Start with "Results are not saved" at `#/`; a copied `#/prepare` link works. `#/drawer/NOPE-123` shows the missing-drawer view; `#main` leaves the view alone; `#/no-such-page` becomes `#/`. |
| Downloads | Observed: all three files are identical to the response's report strings with the right names and types. Firefox saved `drawercheck.html`, `.csv`, and `.txt` to disk (24,718, 1,899, and 11,950 bytes); the saved HTML report opened from disk with its title, no scripts, and no external files. |
| Waiting | Observed: after 0.3 seconds (shortened for the test) the button reads "Checking the example...", is marked busy, and shows Cancel and the slow-start sentence. Cancel restores the button and focus at once and announces "Stopped waiting."; the late answer arrived 2.5 seconds later and was ignored. A 1-second limit (shortened) shows "The demo server did not answer in time." with "Try again", which then succeeds. Leaving for Prepare files while waiting also ignores the late answer. A connection failure on Prepare files shows beside the button with "Try again", not in the file error summary. |
| Layout and targets | Observed: all 60 drawers, opened by address at 320 px, are exactly 320 px wide with the right page titles; filtered Results is also 320 px. No link, button, summary, radio label, or select is under 24 x 24 px on Results, Drawer details, the missing-drawer view, or Start after a time-out. Light and dark runs gave identical results. |
| Budgets | PASS: CSS 19,584 bytes and JavaScript 32,857 bytes (52,441 together) against 60 KB. |

Screenshots are in `docs/screenshots/2026-10-23-m8-block4/` (12 images, about
2.6 MB). Screen-reader announcements, 200% text, 400% zoom, and an automated
accessibility scan remain block 5. No hosted CI or deployment result is
claimed. Block 5 waits for **next**.

## M8 block 5: Accessibility and browser checks

- Built: An automated WCAG 2.2 AA scan of every view and state in Chrome and
  WebKit, both themes and both widths, plus scripted keyboard, zoom, text-size,
  motion, announcement, and request checks. Fixed the Drawer details row-header
  names, the WebKit date-list height, the two-column drawer layout at large
  text, and the notice landmark; added a favicon and ignored Playwright's
  snapshot folder.
- Learned: A clean automated scan is not the whole story. axe passed while the
  accessibility tree showed tape rows named only "Minus", and Safari's engine
  sized the drop-down differently from Chrome. Reading the tree and testing a
  second engine found what the scanner could not.
- Interview question: Your site passes an automated accessibility scan. What
  else would you check before calling it accessible, and why?

The user authorized block 5 on 2026-10-23 after restarting to load the
Playwright plugin, installing Google Chrome, and choosing to download WebKit.
Tools: Playwright 1.64 (the plugin's copy), Google Chrome 156, Playwright WebKit
26.6, and axe-core 4.14.0 with its registry checksum verified. Same Python,
Flask, Gunicorn, pytest, and Ruff versions as earlier blocks.

| Command or check | Result |
| --- | --- |
| `.venv/bin/pytest -q` | PASS: 684 tests in 11.1 seconds; page tests now check the drawer tape's row-header names and that the stylesheet's only non-font `url()` is an inline SVG image. |
| `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .` | PASS: both clean. |
| axe-core WCAG 2.0 to 2.2 A/AA scan, final page | PASS: 0 violations and 0 best-practice findings in 136 scans (17 views and states x 2 themes x 2 widths x 2 engines). First run: 0 violations, 1 best-practice finding (the notice outside a landmark), fixed. |
| Keyboard | PASS in Chrome (Tab) and WebKit (Option+Tab): skip link first, a solid 3 px ring at every stop, and the example, filters, drawer links, line meanings, back link, download, error links, and Cancel all work by keyboard. Typing "Septem" on the date list selects September 3 and filters. |
| Reflow, zoom, and text | PASS: every scanned view is 320 px wide at 320 px, and 320 px at 400% zoom (320 x 200 CSS px). With 200% text at 1,280 px, no view widens or clips; Drawer details first measured 1,469 px wide and was fixed. |
| Motion, announcements, and requests | PASS: transitions go from 0.15 s to 0 s under reduced motion; the live region announces readiness, waiting, the slow start, and Cancel; every request went to the local site only. |
| Accessibility tree review | Found and fixed: Drawer details tape rows were named "Plus", "Minus", or "Equals" without the label; they now read, for example, "Minus Cash refunds $12.00" in both engines. |
| WebKit date list | Found and fixed: 25 px tall in WebKit against 44 px in Chrome; now 44 px in both. |
| Console | Only the deliberate 400 and blocked-request messages, plus one WebKit message about its own select styling under the strict style policy (accepted; the list works). |
| Budgets | PASS: CSS 20,466 bytes and JavaScript 32,857 bytes (53,323 together) against 60 KB. |

Screenshots are in `docs/screenshots/2026-10-23-m8-block5/` (24 images, about
7.3 MB). Not done: a real screen reader (VoiceOver or NVDA) and a usability
check with someone new to the project. The check scripts live outside the
repository. No hosted CI or deployment result is claimed. Block 6 (hosting)
waits for **next**.

Correction (2026-10-24): two WebKit screenshots showed Start, and WebKit's 400%
zoom row above measured Start for three views. See the block 5 repair below.

## M8 block 5 repair: checks that confirm the view

- Built: Reran every block 5 browser check with a guard that confirms the
  expected view and address before each scan, measurement, and screenshot,
  and replaced the two WebKit screenshots that showed Start by mistake. No
  site code changed.
- Learned: The same test step can mean different things in different
  browsers. Opening the address the page was already on did nothing in Chrome
  but reloaded the page in WebKit, which cleared the results, so the check
  quietly measured Start. A check should prove it is looking at the right
  thing before it reports a pass.
- Interview question: Your browser test passed in two browsers, but in one of
  them it was testing the wrong page. How would you design tests so that
  cannot happen silently?

The user authorized the repair on 2026-10-24 after an outside review of block
5. Each claim was checked before any change. Same tools as block 5: Playwright
1.64, Google Chrome 156, WebKit 26.6, and axe-core 4.14.0.

| Command or check | Result |
| --- | --- |
| `.venv/bin/pytest -q` | PASS: 684 tests in 17.1 seconds. |
| `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .` | PASS: both clean. |
| Review claim 1: two WebKit screenshots | Confirmed: `results-webkit-light-390.png` and `drawer-2026-09-03-R1-webkit-light-390.png` in the block 5 folder are byte-identical (SHA-256 starting `e8768f12`) and both show Start with "Results are not saved". |
| Cause | Reproduced: after the example run, opening `#/results` again with Playwright's `page.goto` kept Results in Chrome (1 page load) but reloaded in WebKit (2 loads). The reload cleared the in-memory results, so the router showed Start, as designed. |
| What it affected | WebKit's 400% zoom figures for Results, Drawer details, and the missing-drawer view, and the two screenshots. Not affected: every Chrome check, the 136 axe scans, keyboard, 200% text, the accessibility tree, and the one-off date-list, layout, and row-name checks, none of which reopened the address already open. |
| Guard test | PASS: with the new view check, the old step now fails in WebKit instead of passing silently; changing the address's `#` part inside the page passes in both engines. |
| Rerun, axe | PASS: 136 scans, 0 violations, 0 best-practice findings, each on its confirmed view (Start, Prepare files, Results, Drawer details, or the missing-drawer view). |
| Rerun, 400% zoom | PASS in Chrome and WebKit: Start, Results, Drawer details, Prepare files, and the missing-drawer view are each confirmed and 320 px wide. |
| Rerun, keyboard, text, motion, announcements | PASS: keyboard results are identical to block 5 in both engines; with 200% text all four views stay 1,280 px wide with nothing clipped; reduced motion and the live region behave as before. |
| Console and requests | Same as block 5: the deliberate 400 and blocked request, WebKit's select styling message, and local requests only. |
| Review claim 2: "Minus" read twice | Partly confirmed: in both engines each Drawer details row header is named, for example, "Minus Cash refunds" and also contains the hidden word "Minus". Not changed: whether a listener hears it twice depends on the screen reader, and removing the word could leave a reader that reads cell contents saying "Cash refunds" with no operator. Decide after a VoiceOver check. |

Screenshots are in `docs/screenshots/2026-10-24-m8-block5-repair/` (4 images,
about 0.9 MB). The block 5 folder is unchanged, as the screenshot rule
requires; its index row now notes the two wrong files. The repair scripts are
scratch files outside the repository, as in block 5. No hosted CI or
deployment result is claimed. Block 6 (hosting) waits for **next**.

## M8 block 6: Render Blueprint and hosting setup

- Built: Added `render.yaml` for Render's free Python web service (`drawercheck`,
  Python 3.13.5, `pip install ".[web]"`, and Gunicorn with 1 worker, 4 threads,
  and a 30-second timeout), plus a test that checks the Blueprint and runs
  `gunicorn --check-config` with those exact options.
- Learned: Render's free web service has 0.1 CPU, 512 MB RAM, and an ephemeral
  filesystem that resets on idle spin-down. Running one Gunicorn worker with
  four threads keeps memory inside 512 MB while still serving concurrent
  requests in separate temporary folders.
- Interview question: Why run one Gunicorn worker with multiple threads instead
  of several worker processes on a 512 MB free hosting instance?

The user authorized block 6 on 2026-10-24 and chose to commit locally first,
then push to GitHub and create the Render service from their dashboard.
Rechecked Render's official Flask guide, Free tier limits, Python version
documentation, and Blueprint YAML specification on 2026-10-24.

| Command or check | Result |
| --- | --- |
| `.venv/bin/pytest -q` | PASS: 685 tests, including `test_render_blueprint_matches_stateless_gunicorn_contract`. |
| `.venv/bin/pytest --collect-only -q` | PASS: 685 tests collected. |
| `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .` | PASS: both clean. |
| `.venv/bin/python -m gunicorn --check-config --bind 127.0.0.1:0 --workers 1 --threads 4 --timeout 30 "drawercheck.web:create_app()"` | PASS: Gunicorn validates the exact command and flags from `render.yaml`. |
| Local Gunicorn subprocess smoke check (`--workers 1 --threads 4 --timeout 30`) | PASS: `GET /` returned 200 with `Content-Security-Policy`, `POST /api/demo` returned 60 drawers and 16 leads, and `GET /examples/shifts.csv` matched `data/demo/shifts.csv`. |
| Hosted GitHub Actions [run 40075833849](https://github.com/GutsJr75/DrawerCheck/actions/runs/40075833849) on `0ec9baf` | PASS: [Python 3.12](https://github.com/GutsJr75/DrawerCheck/actions/runs/40075833849/job/120818848226), [Python 3.13](https://github.com/GutsJr75/DrawerCheck/actions/runs/40075833849/job/120818848034), and [Python 3.14](https://github.com/GutsJr75/DrawerCheck/actions/runs/40075833849/job/120818848224) jobs all succeeded. |
| Live public URL check at `https://drawercheck.onrender.com` (HTTP + Playwright Chromium) | PASS: `GET /` returned 200 with all four security headers and cold-start messaging; `POST /api/demo` and `POST /api/check` returned identical results (60 drawers, 4 needing review, 16 leads, 2 deposit-lead days); all seven `/examples/<file>` CSVs matched `data/demo/*.csv` byte-for-byte; browser upload and `.html`/`.csv`/`.txt` downloads matched local CLI output; a fresh tab on `#/drawer/2026-09-03-R1` redirected to `#/` with `"Results are not saved"`; zero console errors and zero third-party requests. |
| Source and document checks | PASS: `git diff --check`, no prohibited punctuation, and `AGENTS.md` under 150 lines. |

Screenshots of the live Render site are in `docs/screenshots/2026-10-24-m8-block6/`
(6 images, each verified by SHA-256 and dimensions). Block 6 is complete.
Block 7 (wrap-up: README screenshots and interview notes) waits for **next**.

## M8 block 6 review (2026-10-24)

- Built: Recorded the requested code review and debug session in
  `docs/M8_BLOCK6_REVIEW.md`, with five new dated screenshots. No runtime or
  deployment configuration changes were made, and block 7 has not started.
- Learned: Gunicorn switches to its threaded worker with `--threads 4`.
  `--timeout 30` checks worker liveness and does not guarantee an individual
  request finishes within 30 seconds. A local controlled comparison confirmed
  the distinction; the processing-deadline follow-up remains open.
- Interview question: Why does a browser timeout or Cancel button not guarantee
  that work on the server has stopped?

Verification: 685 local tests passed in 18.38 seconds, both Ruff checks passed,
and hosted run 40075833849 was observed passing on Python 3.12, 3.13, and 3.14.
The live demo, direct seven-file upload, all example downloads, bundled assets,
and all three actual browser report downloads passed comparison with the local
core. Drawer navigation, refresh recovery, and missing-file guidance worked.
The native file chooser could not be completed by automation, so this run does
not claim a full browser upload. Cold-start timing, traffic capacity, Render
memory usage, and full accessibility checks were not rerun. See the review for
the exact scope and remaining medium-priority concern.

## M8 block 6 repair (2026-10-24)

- Built: Replaced threaded hosting with two single-threaded sync workers and
  added a real Gunicorn timeout, cleanup, concurrent-visitor, and recovery
  regression test to optional-web CI. Renamed the upload action and added the
  refresh reminder, with four new dated screenshots. See `M8_BLOCK6_REPAIR.md`.
- Learned: A worker's heartbeat timeout and a request's processing limit differ
  when threads are involved. Sync workers let the server stop stalled work;
  two independent workers preserve concurrent service. Local memory evidence
  supports the choice but cannot establish Render's actual peak usage.
- Interview question: How would you test that a timed-out check really stopped
  and cleaned up, rather than only testing that the browser stopped waiting?

Verification: the new integration test failed against the old command, then
the targeted server/page run passed all 18 tests. The full suite passed 686
tests in 22.19 seconds, and both Ruff checks and `git diff --check` passed.
Two concurrent combined workloads of 1,000 drawers each succeeded in 2.36 and
2.30 seconds locally, with a sampled 152.6 MiB sum of server-process RSS.
Browser checks covered the local example, the two messages at desktop and
320 px, keyboard activation of the upload link, and missing-file recovery.
The generic frontend static audit still reports eight pre-existing findings;
its limitations and raw output are recorded in the repair notes. No new
hosted CI success, Render deployment, full accessibility audit, or Render
memory measurement is claimed. Block 7 still waits for **next**.

## M8 block 7: README screenshots and interview wrap-up (2026-10-26)

- Built: Updated README with the public-demo entry point, temporary-run and
  hosting limits, two inspected existing screenshots with local/public captions,
  and plain explanations of the tools. Updated interview pitches, core and web
  questions, three resume options, and suggested repository description/topics.
  Added `M8_CHECKLIST.md`, refreshed current plan status, and recorded the
  repair's deployment follow-up without rewriting earlier verification history.
- Learned: A deployment source SHA, startup worker logs, a passing CI run, and
  a working browser flow answer different questions. Keep their evidence
  separate, especially when some checks were reported by the user. Automated
  accessibility checks also cannot replace a real screen reader or a person
  unfamiliar with the project.
- Interview question: What evidence would you show to explain what your public
  demo can do, what has been tested, and which claims you are not making?

The user authorized block 7 after supplying Render screenshots identifying
repair commit `332f01b`, `Using worker: sync`, and two workers (PIDs 59/60) on
the same instance at 03:17:27 PDT on 2026-10-24. The images were reviewed on
2026-10-26 and remain conversation attachments. The other step-by-step repair
checks were reported complete by the user; they were not replayed in a browser
by the agent during this documentation block.

GitHub's connected API independently showed that
[run 40085196045](https://github.com/GutsJr75/DrawerCheck/actions/runs/40085196045)
on `332f01b39d2b822c2171fd5e3d48ed0b78503409` completed successfully on
2026-10-24. All job steps, including the optional web/server tests, were
inspected on 2026-10-26:

- [Python 3.12](https://github.com/GutsJr75/DrawerCheck/actions/runs/40085196045/job/120846585681)
- [Python 3.13](https://github.com/GutsJr75/DrawerCheck/actions/runs/40085196045/job/120846585714)
- [Python 3.14](https://github.com/GutsJr75/DrawerCheck/actions/runs/40085196045/job/120846585706)

| Command or check | Result |
| --- | --- |
| `.venv/bin/pytest -q`, initial sandbox run | FAIL: 685 passed; the local Gunicorn test could not start its Unix socket under sandbox restrictions. |
| `.venv/bin/pytest -q`, with local-socket permission | PASS: 686 tests in 13.51 seconds. No source change was needed. |
| `.venv/bin/pytest --collect-only -q` | PASS: 686 tests collected. |
| `.venv/bin/ruff check .` | PASS: all checks clean. |
| `.venv/bin/ruff format --check .` | PASS: 56 files already formatted. |
| `.venv/bin/drawercheck --help` | PASS: installed command prints its six subcommands. |
| Documentation links, embedded image paths, and punctuation | PASS: relative file links and heading targets in changed Markdown resolve; embedded images exist and were visually inspected; no prohibited punctuation in the changed documents; AGENTS.md stays below 150 lines. |
| `git diff --check` | PASS: no whitespace errors. |

No runtime, UI, workflow, or hosting configuration changed. Existing screenshot
folders were reused without modification, so there is no new screenshot folder.
No push, deployment, or hosted CI result for this documentation commit is
claimed. On 2026-10-26 the user confirmed that no unfamiliar participant has
tried the site and deferred a possible friend check. A real screen-reader
session, including checking whether the tape operator is spoken twice, also
remains unverified. All seven M8 delivery blocks are complete with these manual
validation gaps recorded; this is not a claim that every acceptance check passed.
No further feature milestone is started.

## M9 block 1: possible swapped-digit hint (2026-10-26)

- Built: Added R03 as an info-level heuristic for known whole-dollar differences
  of at least $9 divisible by nine, in either direction. Reused saved evidence,
  all reports, and server-owned public labels. Updated the exact demo table,
  sample report, documentation, and tests; added three dated local screenshots.
  Bumped policy version to 5 so old saved runs cannot silently mix rule sets.
- Learned: A number pattern can suggest a check without proving its cause.
  The unchanged $45 and $9 demo shortages now add two notes, so the demo has
  18 leads while its amounts and original 16 leads stay unchanged. Counts in
  tests, reports, screenshots, and walkthroughs must move together.
- Interview question: Why is a difference divisible by nine only a hint, and
  how would you avoid presenting that clue as proof of a typing mistake?

| Command or check | Result |
| --- | --- |
| `.venv/bin/pytest -q`, final run with Unix-socket permission | PASS: 708 tests in 13.59 seconds. Earlier development failures and corrections are recorded in `M9_BLOCK1.md`. |
| `.venv/bin/ruff check .` | PASS. |
| `.venv/bin/ruff format --check .` | PASS. |
| Local browser, native Chrome | PASS within scope: example, 18-lead summary, Note filtering, new labels/messages, drawer details, Back preserving filters, and Tab/Enter activation. Console showed zero messages when inspected. |
| Local 320 px viewport | PASS within scope: new drawer hint, message, and rule code wrap without clipping inside the panel, dark mode. |
| Golden sample | PASS: all 18 date/shift/rule/severity tuples match docs, CSV, and the committed HTML sample apart from its generation timestamp. |
| Strict frontend audit | Exit 2: same eight baseline findings, documented limitations; raw JSON retained in `M9_BLOCK1_AUDIT.json`. |
| Relative links, punctuation, screenshot inspection, and `git diff --check` | PASS. |

See [M9 block 1 evidence](M9_BLOCK1.md) and the new screenshot timeline row.
No hosted CI, push, deployment, or fresh full accessibility audit is claimed.
R06 and R07 are later blocks. Stop here for review and **next** before R06.

## M9 block 1: published verification records (2026-10-26)

- Built: Refreshed current deployment statements in README, plan, web plan,
  interview notes, and M9 evidence after the user pushed and deployed R03.
  Linked passing hosted run 40426134663 and recorded today's direct public
  HTTP checks. Runtime code, tests, demo CSVs, and decision 71 are unchanged.
- Learned: "Deployment pending" must be refreshed after actual hosted and
  public results are observed. A live API check establishes its response
  behavior without claiming a fresh browser or accessibility pass.
- Interview question: How would you distinguish a passing CI run from evidence
  that the deployed application is actually serving the new behavior?

GitHub run 40426134663 for `c5af7a4` was independently observed passing on
Python 3.12/3.13/3.14, including both Ruff checks, core tests, CLI help, and
optional web/server tests. On the public URL, the homepage passed its four
header checks, the example and seven-file synthetic upload both returned the
expected 18-lead results, all seven example downloads matched repository bytes,
and the three report contents included R03. Exact results and limits are in
[the public follow-up](M9_BLOCK1.md#public-verification-follow-up-2026-10-26).
The +$27 over case remains deliberately covered by a focused rule test rather
than added to the unchanged demo data. Documentation link/punctuation checks,
`git diff --check`, and both local Ruff checks passed. The test suite was not
rerun for this documentation-only correction. No new push or deployment was
performed by the agent; no new browser screenshot was taken. R06 has not begun.

## M10 redesign proposal finalized (2026-10-26, documentation only)

- Built: Finalized `REDESIGN_PLAN.md` from the supplied concept and archived
  review. Specified compact Results, secondary downloads, accurate drawer/day
  counts, qualified ticks, filter and next-drawer behavior, required states,
  Python-owned display data, and seven proposed work areas. Results and Drawer
  details precede Start polish. Added the planning status and decision 72 to
  `PLAN.md`; optional review checkboxes and report restyling stay deferred.
- Learned: Grouping changes the units a summary must describe. The current
  demo has 16 drawer leads across nine drawers plus two whole-day leads, not
  18 drawer leads. Filtering individual leads before grouping keeps a Note
  visible even when its drawer also has a higher-level lead.
- Interview question: How would you redesign a review list without hiding
  lower-level leads or making its summary disagree with the underlying data?

Verification: relative document links and prohibited punctuation checks passed;
a fresh local `POST /api/demo` confirmed 60 drawers, nine with leads, 51 with
none, 16 drawer leads, two whole-day leads on two dates, and the documented
severity counts. The initial one-off count check used a null shift-code test;
the corrected check used the actual nullable `shift_id` (whole-day web codes
are empty strings) and passed. Both Ruff checks passed, with 61 files already
formatted. Font licence references were checked against the Google Fonts OFL
files. `git diff --check` passed.

The user authorized finalizing the plan only. M10 implementation and changing
the milestone order still require explicit approval. No runtime, test, demo
data, visual asset, or canvas content changed. No new screenshots were needed;
the earlier concept review remains historical evidence. The full pytest suite
and browser checks were not rerun for this documentation block. No push,
deployment, or new hosted CI result is claimed.

## M10 block 1: shared Tick and tie design (2026-10-26)

- Built: Applied the approved shared ledger palette, Atkinson fonts, responsive
  type/spacing, drawer logo, header, wrapping footer, breadcrumbs, and scrollbar
  styles to the existing views. Added colour-guide drift coverage, font licence
  packaging, a canonical-owner audit manifest, and 35 dated screenshots with
  initial and verified states. No financial or routing JavaScript changed.
- Learned: Two variable fonts can cover all needed weights with fewer assets.
  The shipped fonts total 51,748 bytes, and package-data checks must include
  their licences. A reused navigation role can preserve filters in breadcrumbs
  without a second state system. Restart a cached local template before final
  screenshot acceptance.
- Interview question: How would you change a site's shared visual identity
  while preserving its calculations, navigation state, and accessibility cues?

Final checks: 709 pytest tests passed in 15.46 seconds with local-socket
permission; the targeted page suite passed 18 tests; both Ruff checks passed
(62 files formatted in the final check). Chrome passed the 16-case view/theme/width matrix and
the recorded controls, filter-preserving keyboard return, fake upload, downloads,
cancellation, error/retry, and refresh checks. Fonts loaded locally, no page-wide
horizontal overflow occurred, and the matrix recorded no external resources or
page-error events. Combined CSS/JS is 54,788 bytes, below 60,000.

The generic strict audit retains seven pre-existing external-handler detection
findings; all flagged buttons were exercised successfully. The native-select
ownership finding is resolved. Official DESIGN.md lint had zero errors and one
Markdown-only warning; the new project test checks exact colour-table drift.
The attempted headless native-popup key sequence did not select a date; explicit
native selection passed, without a new OS-popup keyboard claim. Development
packaging/format issues and the preview-cache correction are recorded in
[block 1 evidence](M10_BLOCK1.md), along with screenshots and raw check records.

No new hosted CI or deployment result, WebKit/zoom pass, screen-reader session,
or beginner usability pass is claimed. Stop for `next` before M10 block 2.

## M10 block 2: Results summary and layout (2026-10-26)

- Built: Added the Full run Results slip, qualified no-leads tick, responsive
  side column, secondary downloads, and a closed detailed-count disclosure.
  Python supplies separate drawer/day counts and shared weekday labels.
  Preserved the flat list, report contents, core arithmetic, and all caps.
- Learned: One drawer can have several leads, so drawer counts must use its
  highest own level while whole-day leads stay separate. Date labels also need
  opening/closing clock dates for overnight shifts. CSS columns can preserve
  a single meaningful DOM and keyboard order without duplicated controls.
- Interview question: How would you show a useful summary without confusing
  the number of records with the number of issues found in those records?

Final checks: 716 pytest tests passed in 15.71 seconds with local-socket
permission; the targeted web/page suites passed 119 tests before the final
summary tick addition. Both Ruff checks passed (63 files formatted), and
`git diff --check` passed. Chrome passed the final 20-case view/theme/width
matrix, keyboard/filter restoration, exact report-download hashes, real fake
uploads for no-leads and bank-only states, Cancel, error/retry, and refresh.
The summary tick passed once-per-run, reduced-motion, and zero-drawer checks.

Combined CSS/JS is 56,141 bytes; fonts remain 51,748 bytes. The combined capped
workload returns 8,620,061 bytes without increasing the 10 MB limit. The generic
strict audit retains seven known external-handler detection findings, with
actual button behavior exercised. DESIGN.md lint had zero errors and one
Markdown-only warning. There are 34 new dated screenshots, retaining initial
and intermediate captures; final Results filenames show the shipped tick.
A 959 px light PNG with repeated header pixels was retained and replaced in
the final evidence by a settled capture, with one header verified in the DOM.
See [block 2 evidence](M10_BLOCK2.md) for raw records and limits.

No new hosted CI, deployment, WebKit/zoom, screen-reader, unfamiliar-user, or
OS-popup keyboard pass is claimed. Stop for `next` before M10 block 3 grouping.

## M10 block 3: grouped Results (2026-10-27)

- Built: Grouped Results by unique drawer and whole-day date, with server-counted
  severity sections, linked human titles, exact outcomes, filter-aware ordering,
  rule-code disclosures, More detail previews, and required empty states.
  Reused one lead-row renderer and retained full reports and core calculations.
- Learned: Filter leads before grouping, then use each drawer's full-run level
  and order so lower-level notes remain findable. A visible unique code matters
  when register/date titles repeat. Native disclosure toggle events need time
  to fire before checking lazily rendered rows. Shared rendering keeps the
  fixed code budget viable; only 557 bytes remain for later blocks.
- Interview question: How can a filter show a matching note without losing the
  higher-priority context of the drawer it belongs to?

Final checks: 717 pytest tests passed in 13.63 seconds with local-socket
permission; the targeted page suite passed 20 tests. Both Ruff checks and
`git diff --check` passed. Chrome checked the 20-case view/theme/width matrix,
48 date/level combinations, exact grouping and outcomes, keyboard/Back and
breadcrumb restoration, seven synthetic upload cases, all report hashes under
filters, both Cancel flows, error/retry, reduced motion, forced colors, and
refresh recovery. Unsupported object-property filter names normalize safely.

Combined CSS/JS is 59,443 bytes; fonts remain 51,748 bytes. The combined workload
returns 8,620,061 bytes under the unchanged 10 MB cap. A first budget check
failed while both list implementations existed; final shared-row cleanup passes.
The generic strict audit retains its seven external-handler detection findings;
actual button behavior passed. DESIGN.md lint had zero errors and one existing
Markdown-only warning. There are 34 new dated screenshots, with initial and
mid-animation captures retained. See [block 3 evidence](M10_BLOCK3.md).

No new hosted CI, deployment, WebKit/zoom, OS-popup keyboard, screen-reader, or
unfamiliar-user pass is claimed. Stop for `next` before M10 block 4, Drawer details.

## M10 block 4: Drawer details (2026-10-27)

- Built: Added human titles, an exact outcome strip, qualified availability
  ticks, a supplied-zero row toggle, applicable Python rule limits, and Next
  through the active filtered drawer list without wrapping. Preserved full
  own/day leads, reports, source count rows, and all resource ceilings.
- Learned: All-zero counts and absent counts need different displays. Checking
  whether supplied quantities are positive is a presentation choice; adding
  their money in the browser would duplicate the core. Rule limits should use
  saved policy evidence, and table scrolling must stay inside named regions.
  Keep the code budget explicit: 385 bytes remain after shared-style cleanup.
- Interview question: How would you simplify a count sheet without hiding a
  real zero count or confusing a missing record with $0.00?

Final checks: 727 pytest tests passed in 13.81 seconds with local-socket
permission; the targeted web/page suites passed 130 tests. Both Ruff checks
and `git diff --check` passed. Chrome checked all 60 example drawers, full
and Note-filtered Next sequences, no-wrap and outsider/member entry cases,
keyboard row disclosure/Next, seven synthetic count/input cases, long identities,
overnight/multi-year dates, exact report hashes under filters, and refresh.
The 20-case view/theme/width matrix recorded no page overflow, page errors,
or external resources. Large tape/count values stay in internal scroll regions.

CSS/JS totals 59,615 bytes; fonts remain 51,748 bytes. The combined workload
returns 8,701,107 bytes under the unchanged 10 MB cap. The generic strict audit
retains seven known external-handler detection findings; DESIGN.md lint has
zero errors and one existing Markdown-only warning. There are 35 new dated
screenshots, retaining initial captures and adding a settled tape close-up.
See [block 4 evidence](M10_BLOCK4.md) for raw checks and limits.

No new hosted CI, deployment, WebKit/zoom, OS-popup keyboard, screen-reader,
or unfamiliar-user pass is claimed. Stop for `next` before block 5, Start.

## 2026-10-28: M10 block 5, Start

- Built: a shorter Start introduction with both actions before the example
  description, qualified shared input ticks, and a native Count, Compare,
  Review sequence. Removed the always-on hosting hint while preserving slow
  notices, Cancel, retry, upload, keyboard navigation, and refresh recovery.
- Learned: a clear process can reuse existing spacing and native list numbers
  without adding cards or saved state. Theme transitions also need time to
  settle before screenshots; preserve initial captures and add dated final
  evidence. CSS/JS is 59,870 bytes, leaving 130 under the unchanged budget.
- Interview question: Why do available input records not prove that a drawer
  balances, and how would you keep that distinction clear in the interface?

Verification: 728 tests passed in the full suite; 22 page tests passed after
the final test-selector cleanup. Both Ruff checks and `git diff --check`
passed. Chrome covered 20 view/theme/width cases, 18 interaction cases, and
ten final settled captures. Example and seven-file upload each returned 60
drawers and 18 leads. The real five-second notice and an accelerated browser
timeout fixture were checked separately. There are 48 new screenshots across
the October 27 and 28 folders, retaining all initial captures.

The generic strict audit retains seven external-handler detection findings,
and official DESIGN.md lint reports zero errors and one Markdown-only warning.
No new hosted CI, deployment, WebKit/zoom, screen-reader, or unfamiliar-user
pass is claimed. See [block 5 evidence](M10_BLOCK5.md). Stop for `next` before
block 6, Prepare files.
