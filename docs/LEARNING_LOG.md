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
