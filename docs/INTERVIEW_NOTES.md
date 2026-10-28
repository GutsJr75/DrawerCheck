# Interview and project-sharing notes

DrawerCheck is a personal learning project with fictional data. These notes
describe the core, M9 block 1 R03 heuristic, and M10 redesigned website.
Final local M10 checks cover all screens in Chrome and WebKit. Block 6 has
observed passing hosted CI and matching public assets; two local block 7
fixes still need publication and hosted verification. The public example and
fake upload both returned 18 leads on 2026-10-28.
[Open the public demo](https://drawercheck.onrender.com), or use the
offline sample report if the free server is waking up. The
[core checklist](CORE_CHECKLIST.md) and [M10 checklist](M10_CHECKLIST.md) record
what was tested, how it was checked, and what remains unverified.

## A 30-second pitch

I built DrawerCheck, a Python command-line tool and public web demo that compare
fictional cash counts with sales and bank-deposit records. Visitors can run an
example or upload seven demo CSV files, inspect review leads, and download
reports. Both interfaces use the same whole-cent calculations and SQLite-backed
checks. It is a learning project, not a system used by a real business.

## A two-minute walkthrough

I open the public site and choose **Try the example**. It checks 30 fixed
business dates and two registers: 60 drawers, 4 needing review, and 18 leads in
total. Every person and record is fictional. The other entry point,
**Upload demo CSVs**, takes seven files. The importer validates and saves them
within one transaction, so an invalid row rolls the import back. Errors name
the file, physical CSV line, and field where available.

The cash calculation starts with the opening float, adds cash sales and paid-ins,
then subtracts cash refunds, paid-outs, and safe drops. Card sales stay separate
because they do not add physical cash to the drawer. The independent cash count
is compared with that expected amount. Money stays in integer cents throughout.

The required rules cover cash differences, possible single-bill miscounts,
repeated shortages, missing verification, deposit exceptions, and incomplete or
inconsistent records. A flag is a lead for review, never a finding about a person.
Missing counts stay unknown instead of becoming a misleading zero. M9 adds
a swapped-digit hint for whole-dollar differences divisible by nine, such as
$27. This is a heuristic, a rough clue only, and cannot prove what caused a
difference.

For deposits, one pass reserves exact matches across all days. A second pass
checks the remaining candidates. This remains a simplified date-and-amount
method; equal amounts can be assigned to the wrong day, combined deposits are
not handled, and the lag uses calendar days.

I open drawer **2026-09-03-R1**: $518.75 expected, $498.75 counted, and $20.00
short. The tape explains each amount and the count sheet shows each bill and
coin. A possible single-bill hint is a suggestion to check, not proof of a cause.

Finally, I download a text, HTML, or CSV report. The HTML works offline. Public
checks use separate temporary databases, and the browser loses its results on
refresh or close. The command-line tool can keep its own local database. Both
interfaces reuse the Python core; JavaScript only handles the interaction.

## Eight likely questions with honest answers

The first five also form a short practice set for a code walkthrough.

1. **Why integer cents instead of floating-point amounts?**
   Whole cents make addition and comparison exact. Input dollars are checked for
   exactly two decimal places and parsed with Decimal before becoming cents.

2. **Why store sales and cash counts separately?**
   They are different records: the sales system says what should be there, and
   the count says what was recorded physically. Keeping them separate supports
   comparison; it cannot prove that someone counted without seeing the total.

3. **What stops repeated imports from duplicating records?**
   SHA-256 hashes identify identical files, and record keys reject duplicate or
   conflicting records. The import and its log entries share one transaction.
   A changed file is checked again; it does not silently overwrite old records.

4. **How do repeated or filtered checks stay consistent?**
   Rules use the full needed history before results are selected by date. The
   selected flags and completion markers are replaced in one transaction. Saved
   settings and a policy version keep later explanations consistent with the run.

5. **What are the limits of bank matching?**
   Dates and amounts cannot establish which day a deposit really belongs to.
   Exact matches are reserved first, but equal amounts and overlapping windows
   can still be assigned wrongly. The demo does not combine deposits or model
   real bank calendars, and a missing flag refers only to imported records.

6. **Why keep rules separate from database reads and reports?**
   A rule receives records and returns review leads. It does not open files or
   write the database. This makes its decisions easier to test and explain,
   while all report formats reuse the same saved results and calculation helpers.

7. **What would you do differently for a real application?**
   First establish the real input contracts, operating schedule, deposit
   ownership, and review process with domain experts. This project intentionally
   leaves those production questions unresolved. It is not ready for real cash
   control simply because the fictional examples pass.

8. **Is the website built or the project fully deployed?**
   Yes, the public learning demo is on Render. It supports the example, seven
   demo CSV uploads, drawer explanations, filters, and three report formats.
   M9 block 1 commit `c5af7a4` passed hosted checks on Python 3.12, 3.13, and
   3.14 in [run 40426134663](https://github.com/GutsJr75/DrawerCheck/actions/runs/40426134663).
   Deployment screenshots confirm two sync workers. The
   [M8 checklist](M8_CHECKLIST.md) records the live checks and their evidence.
   The free server can sleep, and no public run history is saved. This does not
   establish production readiness.

## Five questions about the web implementation

1. **How do the website and command line agree on cash amounts?**
   Both call the same Python core. The server sends amounts, summary counts,
   count-sheet totals, and public labels; JavaScript displays them and handles
   navigation, so there is no second cash calculation to keep in sync.

2. **How are different visitors kept separate?**
   Each request gets its own temporary directory and SQLite database. Its
   results and report contents are prepared before the workspace is removed.
   Tests cover independent requests and cleanup on success and failure. A
   forced process kill can prevent Python cleanup, so I do not claim otherwise.

3. **Does pressing Cancel stop the server's calculation?**
   Cancel stops the browser waiting and ignores a late response. Separately,
   Gunicorn's sync-worker watchdog can replace a stalled worker after roughly
   30 seconds. Wake-up and queue time are separate from that processing limit.

4. **How did you verify the timeout repair?**
   A real local Gunicorn test uses the deployment settings with a shortened
   timeout and deliberately stalls one demo. It checks that another visitor
   succeeds, the stalled work stops, its workspace is removed, a replacement
   worker starts, and a later request succeeds. The test failed with the old
   threaded configuration and passed with sync workers.

5. **What do the accessibility checks establish?**
   The recorded scans found no violations in the tested states, and browser
   checks covered keyboard access, narrow screens, and 200% text resizing.
   M10 scanned 27 states in two engines, two themes, and two widths, for 216
   scans with no detected violations after fixing two issues. A 320 x 200
   viewport checks equivalent reflow; actual 400% browser zoom remains open.
   No real screen-reader session is recorded, and a friend usability check is
   deferred until later.
   These checks do not establish full WCAG compliance; the possible repeated
   spoken operator in the drawer tape still needs a screen-reader check.

## Three questions about the redesign

1. **Why group the review list by drawer?**
   A drawer can have several leads. Grouping lets someone open it once and
   see the full story. The example's 18 leads belong to nine drawers and two
   whole-day dates. Filters select individual leads before grouping, so a
   Note on a higher-priority drawer still appears.

2. **What do the ticks mean?**
   They have a written, limited meaning in each place: an added file, an
   available calculation input, or no leads found by these checks. They do
   not prove an audit passed or that a person reviewed anything. Review
   checkboxes are deliberately deferred.

3. **How did you prevent a visual redesign changing the cash results?**
   Python still owns every financial calculation. A comparison against the
   pre-redesign snapshot checks all 60 underlying drawer records, all 18
   global flags, and all report formats. Browser checks compare displayed
   amounts with the Python response and exercise filtering and navigation.
   [Block 7 evidence](M10_BLOCK7.md) records results and remaining gaps.

## Three resume bullet options

Choose wording you can explain and adapt it to the space available:

- Built a Python cash-reconciliation CLI and public Flask demo with synthetic
  CSV uploads, integer-cent calculations, and isolated SQLite request databases.
- Implemented seven explainable review rules, transactional imports, repeatable
  reconciliation, and text, standalone HTML, and protected CSV reports.
- Tested malformed inputs, rollback, duplicate imports, temporary-file cleanup,
  matching boundaries, and server timeout recovery with pytest; verified hosted
  checks on Python 3.12, 3.13, and 3.14.

These options describe project features, not employment results. No measured
business improvement or production-use claim is implied.

## Suggested GitHub description and topics

**Description:** Python cash-drawer reconciliation CLI and public Flask demo
with synthetic CSV uploads, explainable review leads, and downloadable reports.

**Topics:** `python`, `flask`, `sqlite`, `cli`, `csv`, `pytest`,
`cash-reconciliation`, `learning-project`.

These are suggested text only; they have not been applied to repository settings.

## Things I would not claim

- Real-business adoption, operational reliability, or real financial data.
- Theft detection, loss reduction, or conclusions about a cashier's actions.
- Banking, accounting, legal, compliance, or professional security expertise.
- Compliance with an industry standard; the thresholds are example policies.
- User accounts, real POS or bank integrations, or saved public run history.
- Guaranteed uptime, traffic capacity, or a measured Render peak memory limit.
- Full WCAG compliance, a real screen-reader pass, or a new-participant usability
  pass based only on automated scans and developer checks.
- Passing remote CI, a Python-version matrix, browser checks, or deployment
  unless the specific result has actually been observed and recorded.
