# Interview and project-sharing notes

DrawerCheck is a personal learning project with fictional data. These notes
describe the implemented offline core through M6. The public web app remains
planned for M7/M8. Use [the checklist](CORE_CHECKLIST.md) for observed validation;
workflow configuration alone does not prove that GitHub CI passed.

## A 30-second pitch

I built DrawerCheck to practice checking cash-drawer records in Python. It
imports fictional sales, cash counts, and bank deposits, then compares amounts
and flags records for review. It uses whole cents, SQLite, and tests to keep the
calculations repeatable. It can explain an individual shift and export text,
HTML, and spreadsheet-safe CSV reports. It is a learning demo, not a system used
by a real business.

## A two-minute walkthrough

I start with the built-in example: 30 fixed business dates, two registers, and
fictional people and records. The importer checks all seven CSV files before
saving the import as one transaction. If a row is invalid, the error names its
file, line, and field, and the transaction rolls back.

The cash calculation starts with the opening float, adds cash sales and paid-ins,
then subtracts cash refunds, paid-outs, and safe drops. Card sales stay separate
because they do not add physical cash to the drawer. The independent cash count
is compared with that expected amount. Money stays in integer cents throughout.

The required rules cover cash differences, possible single-bill miscounts,
repeated shortages, missing verification, deposit exceptions, and incomplete or
inconsistent records. A flag is a lead for review, never a finding about a person.
Missing counts stay unknown instead of becoming a misleading zero.

For deposits, one pass reserves exact matches across all days. A second pass
checks the remaining candidates. This remains a simplified date-and-amount
method; equal amounts can be assigned to the wrong day, combined deposits are
not handled, and the lag uses calendar days.

Finally, I show the worked shift with $518.75 expected and $498.75 counted,
then export its review leads. Repeating imports or reconciliation does not add
duplicate results. The browser app is future work that will reuse this core.

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
   No. The command-line core and offline reports exist. The approved web plan
   calls for isolated temporary runs and a minimal interface for beginners, but
   implementation and public deployment remain separate future milestones.

## Three resume bullet options

Choose wording you can explain and adapt it to the space available:

- Built an offline Python cash-reconciliation learning demo using fictional
  CSV records, integer-cent calculations, and SQLite STRICT tables.
- Implemented six explainable review rules, transactional imports, repeatable
  reconciliation, and text, standalone HTML, and protected CSV reports.
- Tested malformed inputs, rollback, duplicate imports, resource cleanup,
  matching boundaries, and complete fictional scenarios with pytest and Ruff.

These options describe project features, not employment results. No measured
business improvement or production-use claim is implied.

## Suggested GitHub description and topics

**Description:** Offline Python cash-drawer reconciliation learning demo with
synthetic CSVs, SQLite, explainable review checks, and offline reports.

**Topics:** `python`, `sqlite`, `cli`, `csv`, `pytest`, `cash-reconciliation`,
`learning-project`.

These are suggested text only; they have not been applied to repository settings.

## Things I would not claim

- Real-business adoption, operational reliability, or real financial data.
- Theft detection, loss reduction, or conclusions about a cashier's actions.
- Banking, accounting, legal, compliance, or professional security expertise.
- Compliance with an industry standard; the thresholds are example policies.
- An implemented public website, accounts, integrations, or saved browser history.
- Passing remote CI, a Python-version matrix, browser checks, or deployment
  unless the specific result has actually been observed and recorded.
