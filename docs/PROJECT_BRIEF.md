# PROJECT BRIEF: DrawerCheck

## 0. How to work with me
- I am a recent computer science graduate. I know Python, SQL, SQLite, Git, and basic pytest. I must be able to explain every line of this project in a job interview. Write simple, readable code. Explain things in short, plain English. If you use a technical term, add a one-line explanation.
- FIRST read the links in section 15. Then write docs/PLAN.md (milestones, files, risks, and a "Decisions" list). Show me the plan and WAIT for my "go" before writing any code. In Claude Code, use plan mode. In Codex, write the plan file and stop.
- Work one milestone at a time (section 12). After each milestone: run the tests and the linter, make a git commit, summarize in 5 lines or fewer, add an entry to docs/LEARNING_LOG.md, then stop and wait for me to say "next".
- Ask me a question only if you are truly blocked. Otherwise choose the simplest option and write it down under "Decisions" in docs/PLAN.md.
- Scope guard: this should be finishable in about 10 to 20 hours of work (that is my own estimate). If a task looks bigger than 1 hour, split it or cut it. Items marked STRETCH are optional. Do not start them until I ask.
- Never invent facts, numbers, or sources. If you are unsure how a library works, read its documentation link instead of guessing.

## 1. What we are building
DrawerCheck is a local, offline command-line tool that reconciles end-of-shift cash drawers for a small cash business such as a convenience store.

It reads CSV files (shifts, POS totals, safe drops, cash counts by denomination, bank deposits), stores them in SQLite, calculates the expected cash for each shift, compares it with the counted cash, flags unusual results for human review, and produces a report in three formats: terminal text, a single-file HTML page, and a CSV of flags.

Why this project: I worked two POS registers at a busy convenience store, counted cash, and reconciled my register against transaction records. I want to show I can do the same careful checking with code. The people reading my GitHub will be recruiters and hiring managers for bank teller, service desk, and junior developer jobs.

Out of scope (do not build): web UI, real POS or bank integrations, user accounts, cloud services, machine learning, anti-money-laundering or Bank Secrecy Act features, bank file formats (OFX, BAI2), multi-currency, tips, payroll.

## 2. Rules that must always hold
Tech:
- Python 3.12 or newer. Develop on 3.13 or 3.14. Runtime uses the standard library only. Dev tools: pytest and ruff.
- Use src layout, pyproject.toml, setuptools, and a console script called `drawercheck`.
- No network calls at runtime. No external fonts, scripts, or CDNs in the HTML report.

Money:
- Store and calculate all money as INTEGER CENTS. Never use float for money.
- Parse CSV dollar strings with decimal.Decimal, require exactly 2 decimal places, and reject anything else with a clear error. Format cents back to "$1,234.56" in one helper function (src/drawercheck/money.py).

Database:
- sqlite3 from the standard library. Use STRICT tables (needs SQLite 3.37 or newer). At startup, check sqlite3.sqlite_version_info. If it is older than (3, 37, 0), print a clear error and exit.
- Always bind values with ? placeholders. Never build SQL with string formatting.
- Run PRAGMA foreign_keys = ON on every connection and set connection.row_factory = sqlite3.Row.
- IMPORTANT: `with connection:` only commits or rolls back a transaction. It does NOT close the connection (see the sqlite3 docs). Write one helper, db.connect(path), and always use it like this: `with closing(db.connect(path)) as con:` (contextlib.closing), then use `with con:` inside it for each transaction. Never leave a connection open.
- Make leaked connections fail the tests: in pyproject.toml set pytest addopts to "-W error::ResourceWarning". If this turns out flaky, instead add explicit tests that prove the helper closes the connection, and record that decision in docs/PLAN.md.

Safety and tone:
- Demo data only. Fake names, fake IDs, fake store ("Demo Store #001"). No real brand names, logos, people, or business data anywhere in the repo.
- Escape every value that goes into HTML with html.escape.
- Flag messages must be neutral and factual: "Short by $20.00. Recount recommended." Never use words like theft, fraud, stealing, or suspicious. Flags are leads for a manager to review, not conclusions.
- Keep every user-facing error message in one file, src/drawercheck/errors.py, so docs/TROUBLESHOOTING.md can quote the exact text (section 14).

Code style:
- Small functions, type hints, a one-line docstring on each public function, descriptive names, no clever tricks. Use dataclasses (frozen where possible) for Shift, ShiftResult, and Flag.
- ruff check and ruff format must pass. Keep AGENTS.md under 150 lines.

## 3. Domain primer (the math)
Expected cash in the drawer at close:
  expected = opening_float + cash_sales + paid_ins - cash_refunds - paid_outs - safe_drops_total
Variance = counted_cash - expected
  negative = SHORT, positive = OVER, zero = BALANCED.
Counted cash = sum of (denomination x quantity) from the count sheet. Denominations in cents: 10000, 5000, 2000, 1000, 500, 200, 100 (bills) and 50, 25, 10, 5, 1 (coins). Reject any other value.
"Blind count" practice: the cash is counted first and the expected number is calculated after. Store the counts independently of POS totals and calculate variance only afterwards. This is a process practice, so explain it in the docs and do not try to enforce it in code.
Expected bank deposit for a business day D:
  expected_deposit = sum over that day's shifts of (counted_cash + safe_drops_total) - (retained_float x number of registers closed that day)
When the retained float equals the opening float, this equals net cash sales plus variance.

Worked example (use it in docs/HOW_IT_WORKS.md and as a test):
- opening float $200.00, cash sales $1,250.75, cash refunds $12.00, paid-outs $20.00, paid-ins $0.00, safe drops $900.00
- expected = 200.00 + 1,250.75 - 12.00 - 20.00 - 900.00 = $518.75
- counted = $498.75, so variance = -$20.00 (SHORT $20.00)
- expected deposit = 498.75 + 900.00 - 200.00 = $1,198.75
- check: net cash sales 1,250.75 - 12.00 - 20.00 = 1,218.75, and 1,218.75 - 20.00 variance = 1,198.75

The "three-way match" idea: POS expected = cash counted = bank deposit. A mismatch between the first two points to a register problem. A mismatch between the last two points to a deposit problem. We implement the first two fully and the bank side in simplified form (section 7).

Default thresholds (config.toml, all configurable). These come from example policies in public cash-handling checklists. They are examples, not industry standards, so say so in the README:
```toml
[tolerance]
within_tolerance_cents = 100        # up to $1.00 counts as balanced
warn_cents = 500                    # $5.00 and above: warn
review_cents = 2000                 # $20.00 and above: review
review_percent_of_cash_sales = 1.0  # or 1 percent of cash sales, whichever is LOWER, but never below warn_cents
[repeat_short]
min_shifts = 3
window = 10
[verification]
require_verifier_and_note_at_or_above_cents = 2000
[drops]
suggest_drop_if_cash_sales_cents = 40000   # STRETCH rule only
[deposits]
retained_float_per_register_cents = 20000
max_lag_days = 3
```
Use integer math for the percent rule and document the rounding. Read the file with tomllib. If config.toml is missing, use built-in defaults and print one info line saying so.

## 4. Data model (SQLite, STRICT tables)
```sql
CREATE TABLE cashiers (id TEXT PRIMARY KEY, display_name TEXT NOT NULL) STRICT;
CREATE TABLE registers (id TEXT PRIMARY KEY, label TEXT NOT NULL) STRICT;
CREATE TABLE shifts (
  id INTEGER PRIMARY KEY,
  shift_code TEXT NOT NULL UNIQUE,              -- e.g. 2026-09-14-R1
  business_date TEXT NOT NULL,                  -- YYYY-MM-DD
  register_id TEXT NOT NULL REFERENCES registers(id),
  cashier_id TEXT NOT NULL REFERENCES cashiers(id),
  opened_at TEXT NOT NULL,                      -- ISO 8601 local time, no timezone
  closed_at TEXT,
  opening_float_cents INTEGER NOT NULL CHECK (opening_float_cents >= 0),
  verifier_id TEXT REFERENCES cashiers(id),
  variance_note TEXT
) STRICT;
CREATE TABLE pos_totals (
  shift_id INTEGER PRIMARY KEY REFERENCES shifts(id),
  cash_sales_cents INTEGER NOT NULL CHECK (cash_sales_cents >= 0),
  card_sales_cents INTEGER NOT NULL CHECK (card_sales_cents >= 0),
  cash_refunds_cents INTEGER NOT NULL CHECK (cash_refunds_cents >= 0),
  paid_outs_cents INTEGER NOT NULL CHECK (paid_outs_cents >= 0),
  paid_ins_cents INTEGER NOT NULL CHECK (paid_ins_cents >= 0),
  void_count INTEGER NOT NULL CHECK (void_count >= 0),
  no_sale_count INTEGER NOT NULL CHECK (no_sale_count >= 0)
) STRICT;
CREATE TABLE safe_drops (
  id INTEGER PRIMARY KEY,
  shift_id INTEGER NOT NULL REFERENCES shifts(id),
  amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
  dropped_at TEXT NOT NULL,
  bag_number TEXT
) STRICT;
CREATE TABLE cash_counts (
  shift_id INTEGER NOT NULL REFERENCES shifts(id),
  denomination_cents INTEGER NOT NULL,
  quantity INTEGER NOT NULL CHECK (quantity >= 0),
  PRIMARY KEY (shift_id, denomination_cents)
) STRICT;
CREATE TABLE bank_deposits (
  id INTEGER PRIMARY KEY,
  deposit_date TEXT NOT NULL,
  amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
  reference TEXT
) STRICT;
CREATE TABLE flags (
  id INTEGER PRIMARY KEY,
  shift_id INTEGER REFERENCES shifts(id),
  business_date TEXT NOT NULL,
  rule_code TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('info','warn','review')),
  message TEXT NOT NULL,
  evidence_json TEXT NOT NULL
) STRICT;
CREATE TABLE import_log (
  id INTEGER PRIMARY KEY,
  file_name TEXT NOT NULL,
  sha256 TEXT NOT NULL UNIQUE,
  rows_imported INTEGER NOT NULL,
  imported_at TEXT NOT NULL
) STRICT;
```
Add sensible indexes (shifts by business_date and by cashier_id).

## 5. CSV input contract and import rules (folder: data/demo/)
All money columns are dollar strings with exactly 2 decimals, like 1250.75. Dates are YYYY-MM-DD. Date-times are YYYY-MM-DDTHH:MM:SS.
- cashiers.csv: cashier_id, display_name
- registers.csv: register_id, label
- shifts.csv: shift_code, business_date, register_id, cashier_id, opened_at, closed_at, opening_float, verifier_id, variance_note
- pos_totals.csv: shift_code, cash_sales, card_sales, cash_refunds, paid_outs, paid_ins, void_count, no_sale_count
- safe_drops.csv: shift_code, amount, dropped_at, bag_number
- cash_counts.csv: shift_code, denomination, quantity (denomination as dollars, for example 20.00 or 0.25)
- bank_deposits.csv: deposit_date, amount, reference

Import rules:
- Read files with encoding "utf-8-sig" so a leading byte-order mark (BOM) from Excel does not break the first header.
- Check headers first: missing columns, unexpected extra columns, and an empty file each get a clear error. A header-only file imports zero rows and says so. Skip fully blank lines.
- Validate every row. On a bad row, raise ImportValidationError with the file name, line number, column, and a plain-English message. The CLI prints it and exits with code 1. Import is all-or-nothing in one transaction: if any file fails, nothing is saved.
- Duplicate rows inside one file (same shift_code, or the same shift_code and denomination) are an error that names both line numbers.
- Import is idempotent: compute the SHA-256 of each file and record it in import_log. If the same file was already imported, skip it and say so. shift_code is UNIQUE, so duplicates cannot slip in.

## 6. Rules engine (src/drawercheck/rules.py)
Each rule is a small pure function that takes the shift data, the config, and the history it needs, and returns a list of Flag objects. A RULES list registers them. Every Flag has: rule_code, severity, a neutral message, and evidence (a dict that is stored as JSON: numbers, dates, shift codes).

MVP rules (must build):
- R01_VARIANCE: if |variance| is at most within_tolerance, no flag. Between within_tolerance and warn: info. At or above warn: warn. At or above the review threshold (the lower of review_cents and review_percent_of_cash_sales, never below warn_cents): review.
- R02_SINGLE_DENOMINATION: info flag when |variance| exactly equals one denomination from {$1, $5, $10, $20, $50, $100}. Message: "Variance equals one $20 bill. Check for a miscounted or misplaced bill."
- R04_REPEAT_SHORT: warn when the same cashier was short by at least warn_cents in at least min_shifts of their last window shifts (up to and including this shift). Evidence lists the shift codes and amounts. Message example: "Short in 3 of the last 10 shifts for this cashier. Pattern for manager review. Counting errors are the most common cause."
- R05_MISSING_VERIFIER_OR_NOTE: review when |variance| is at or above require_verifier_and_note_at_or_above_cents and the verifier or the note is missing (dual-control practice).
- R08_DEPOSIT: see section 7.
- R09_DATA_INTEGRITY: review for: shift has no cash count rows ("not counted"); closed_at is not after opened_at; two shifts overlap on the same register; expected cash is negative.

STRETCH rules (ask me first):
- R03_TRANSPOSITION_HINT: info when the variance is a whole number of dollars at least $9 and divisible by 9. Message: "Could be two digits swapped when typing a total. Hint only." Label it a heuristic in the docs and the code.
- R06_NO_SAFE_DROP: info when cash sales are at or above suggest_drop_if_cash_sales_cents and no safe drop was recorded.
- R07_SHORT_WITH_UNUSUAL_REFUNDS_OR_VOIDS: warn when the shift is short and cash refunds or void_count are at least 3 times the cashier's median over their last 10 shifts and at least 5 (for voids) or $20 (for refunds).

Each rule needs at least one triggered test and one not-triggered test.

## 7. Reconcile and deposit logic
Reconcile (for a date range):
1. For each shift with a closed_at, compute counted, expected, and variance (integers).
2. Run all rules that exist at the current milestone. Delete old flags for that date range and insert the new ones, so running reconcile twice gives the same result.
3. Assume ONE shift per register per business day (the closing shift). Document this as a limitation.

Deposit matching (R08), simplified on purpose:
1. For each business date D with expected_deposit > 0, look at bank deposits with deposit_date from D to D + max_lag_days that are not yet matched.
2. Exact amount match: matched, no flag.
3. No exact match but exactly one unmatched deposit in the window: flag the mismatch with the difference (warn, or review if the difference is at least review_cents).
4. No deposit in the window: flag "missing deposit" (review).
5. Deposits left unmatched at the end: info "unexpected deposit".
6. Process dates in order and match greedily.

Known limitations (write them down concretely in HOW_IT_WORKS.md and the README "Limitations", with one short worked example where the matching gets it wrong):
- Greedy matching can pair the wrong deposit when two days have the same amount or when the date windows overlap.
- One bank deposit that covers two days is not handled.
- Weekends and holidays are only approximated by max_lag_days.
- Real bank reconciliation is more complex than this.

## 8. Command-line interface (argparse subcommands)
- drawercheck init-db [--db PATH]
- drawercheck demo-data [--out data/demo] [--days 30] [--seed 42]
- drawercheck import --dir data/demo [--db PATH]
- drawercheck reconcile [--from DATE] [--to DATE] [--db PATH] [--config PATH]
- drawercheck report [--date DATE | --from DATE --to DATE] [--format text|html|csv] [--out PATH]
- drawercheck explain SHIFT_CODE  (prints the step-by-step math and every flag for one shift, in the same style as the worked example in section 3)
Default db path: ./drawercheck.db (git-ignored). Exit codes: 0 success, 1 usage or validation error. Print helpful errors, never Python tracebacks. Catch and translate these cases into short messages from errors.py: sqlite3.OperationalError (database locked or read-only), OSError when the report path cannot be written, an unknown shift code, and `report` run before `reconcile` ("No flags found. Run `drawercheck reconcile` first.").

## 9. Demo data (src/drawercheck/demo.py)
- Deterministic: use random.Random(seed). Fixed date range starting 2026-09-01 (never use today's date). 2 registers (R1, R2), one closing shift per register per day, cashiers cashier_01 to cashier_04, verifier manager_01. Store: "Demo Store #001".
- Most shifts are balanced or within $1.00.
- Inject these known scenarios and document them in docs/DEMO_SCENARIOS.md. Tests must confirm each expected flag appears:
  - S1 2026-09-03 R1 cashier_02: short exactly $20.00, verifier and note present. Expect R01 review and R02. No R05.
  - S2 2026-09-08 R2 cashier_01: short $45.00, no verifier, no note. Expect R01 review and R05.
  - S3 cashier_03 short by $6, $8, $7, $9 on 09-05, 09-09, 09-14, 09-18. Expect R04 on 09-14 and 09-18.
  - S4 2026-09-12 cashier_04: over by exactly $5.00. Expect R01 warn and R02.
  - S5 2026-09-16: no bank deposit. Expect R08 missing.
  - S6 2026-09-21: bank deposit is $100.00 less than expected. Expect R08 mismatch review.
  - S7 2026-09-25 R1: no cash count rows. Expect R09 not counted.
  - S8 2026-09-27 R2: closed_at earlier than opened_at. Expect R09.
  - S9 running import twice does not change any row counts.
  - STRETCH: a +$27.00 over (R03), a high-sales day with no safe drop (R06), a refund spike with a short drawer (R07).

## 10. Reports (src/drawercheck/reports/)
- text: a daily summary table (date, shifts, balanced, over, short, flags by severity), then the flags list with severity, shift code, and message, then an over/short log by cashier for the date range (managers review this by cashier to spot patterns).
- html: ONE self-contained file with inline CSS and no JavaScript. Semantic tables, a visible "DEMO DATA ONLY" banner, a generated-on line, light and dark colors through prefers-color-scheme, a viewport meta tag, and severity shown by text labels (not by color alone). Use html.escape on all values.
- csv: all flags (date, shift_code, rule_code, severity, message). Use the csv module. Spreadsheet-formula protection is REQUIRED, not optional: write one function, sanitize_cell() in src/drawercheck/csv_safety.py, that prefixes a single quote to any cell that starts with =, +, -, @, a tab, or a carriage return. Use it for every cell in the CSV export.

## 11. Tests (pytest, in tests/)
- money: parse and format, rejects 3 decimals, rejects values like "1e3", handles "0.10", never uses float.
- formulas: table-driven tests with pytest.mark.parametrize, including the worked example in section 3 (expected 518.75, variance -20.00, deposit 1,198.75).
- every rule: one triggered and one not-triggered case.
- import and data reliability:
  - a bad row gives the right file, line, and column
  - a failure in any file leaves the database unchanged (transaction rollback)
  - re-importing the same file changes nothing (idempotent)
  - duplicate rows inside one file are rejected
  - malformed CSV cases: UTF-8 BOM, missing header, wrong header, extra column, empty file, header-only file, blank lines, quoted commas, Windows line endings
- connections: a test that proves db.connect plus closing really closes the connection, and the suite runs with ResourceWarning as an error.
- CSV safety: sanitize_cell tests for each dangerous first character and for normal text.
- deposit matching: matched, mismatch, missing, unexpected, and the "same amount on two days" case that shows the known limitation.
- CLI smoke tests that call main(argv) with tmp_path databases, including each translated error in section 8.
- golden test: run demo-data, import, and reconcile, then assert every flag in docs/DEMO_SCENARIOS.md appears and nothing unexpected appears.
- No test may depend on today's date or on the network.

## 12. Milestones (stop after each)
- M0 Plan: docs/PLAN.md only. Wait for my "go".
- M1 Skeleton: pyproject.toml, src layout, ruff config, pytest config (with the ResourceWarning setting), `drawercheck --help`, money.py with tests, errors.py, db.connect helper with a test, AGENTS.md and CLAUDE.md (section 13), .gitignore, LICENSE (MIT), README stub. Done when pytest and ruff pass.
- M2 Database, demo data, import: init-db, demo-data, import (idempotent, BOM, header checks, rollback), and the malformed-CSV tests.
- M3 Reconcile core: expected, counted, variance, rules R01, R02, R05, R09, the `reconcile` command storing flags, and `explain`. Tests, including S1, S2, S4, S7, S8 from the demo data.
- M4 Reports: text, html, csv (with sanitize_cell), the report command, and examples/sample_report.html. After M4 the project must already be demo-ready: the README has a "Try it in 3 steps" section (install, then generate and import and reconcile demo data, then produce the HTML report) and a clearly marked screenshot placeholder.
- M5 Patterns and deposits: R04 and R08, and the golden test for S1 to S8. Regenerate examples/sample_report.html so it shows every rule.
- M6 Polish: README, docs (including TROUBLESHOOTING.md and the concrete deposit limitation example), GitHub Actions CI, the final checklist, and the resume and interview material (section 14).
- M7 STRETCH rules, only if I ask.

## 13. Repo layout, tooling, instruction files, CI
```
drawercheck/
  AGENTS.md
  CLAUDE.md              (contains only the line: @AGENTS.md)
  README.md  LICENSE  pyproject.toml  config.toml  .gitignore
  src/drawercheck/  __init__.py cli.py config.py money.py errors.py db.py importer.py
                    reconcile.py rules.py models.py demo.py csv_safety.py
                    reports/{text,html,csv_out}.py
  tests/
  data/demo/         (generated fake CSVs, committed)
  docs/  PLAN.md HOW_IT_WORKS.md DEMO_SCENARIOS.md LEARNING_LOG.md INTERVIEW_NOTES.md TROUBLESHOOTING.md
  examples/sample_report.html
  .github/workflows/ci.yml
```
Setup commands to put in README and AGENTS.md:
```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
ruff check . && ruff format --check .
drawercheck --help
```
AGENTS.md (under 150 lines): one-line project summary, the commands above, the conventions in section 2, the milestone workflow in section 0, and links to docs/. Keep CLAUDE.md as just `@AGENTS.md` so Claude Code and Codex share one set of instructions.
CI: start from the GitHub Actions Python example in section 15. Matrix Python 3.12, 3.13, 3.14. Steps: checkout, setup-python, pip install -e ".[dev]", ruff check, ruff format --check, pytest. Use the action versions shown in the GitHub docs page, and check that they are current. Add a README status badge.

## 14. Documentation and career deliverables
- README.md: what it does, why I built it (3 sentences, no brand names), a "Try it in 3 steps" section, a quick start that works from a fresh clone, a sample of the terminal report, a link to examples/sample_report.html, a screenshot (leave a clearly marked placeholder for me), a "How it works" summary, a "Limitations" section (one shift per register per day, the deposit matching limits in section 7, thresholds are examples not standards, demo data only, not for real cash control, not accounting or legal advice), and "Further reading" with the section 15 concept links.
- docs/HOW_IT_WORKS.md: the primer, the worked example, the deposit algorithm with its worked failure example, and each rule in one paragraph.
- docs/TROUBLESHOOTING.md: 8 to 10 entries. Each entry has Symptom (the EXACT message the tool prints, copied from errors.py), Likely cause, How to check, and Fix. Include ONLY errors the tool really produces, and write a test that triggers each one so the guide always matches the code. Candidates: bad money format, unknown denomination, unknown shift code, file already imported, SQLite version too old, missing config (defaults used), database locked or read-only, report path not writable, `report` before `reconcile`, shift not counted, deposit missing.
- docs/LEARNING_LOG.md: after each milestone, 3 bullets: what I built, what I learned, and one question an interviewer might ask.
- docs/INTERVIEW_NOTES.md: a 30-second pitch, a 2-minute walkthrough, 8 likely questions with honest answers (including "what would you do differently" and "what are the limits"), and a "things I would not claim" list.
- At the end give me: (a) 3 resume bullet options that describe only what exists, with no invented numbers (you may state the number of tests only after running a command that counts them), (b) a GitHub repo description and topics, (c) 5 questions an interviewer could ask about the code, with honest answers.

## 15. Links to read before you plan
Reconciliation concepts (read these first):
- https://docs.wcpos.com/reports/reconciliation (expected drawer formula)
- https://www.shopify.com/blog/balancing-a-cash-drawer
- https://beancount.io/blog/2026/09/14/end-of-day-close-z-reports-cash-drawer-daily-sales-reconciliation-guide (blind count, three-way match)
- https://beancount.io/blog/2026/10/12/daily-sales-reconciliation-cash-heavy-business-pos-till-bank-deposit-guide (deposit intact)
- https://app.manifest.ly/public/checklists/cash-handling-checklist (example variance thresholds, dual control, exception review)
- https://help.hotschedules.com/hc/en-us/articles/4404885792781 (blind count, variance explanation required)
- https://www.accountingtools.com/articles/what-is-the-cash-over-and-short-account.html
Python standard library:
- https://docs.python.org/3/library/sqlite3.html
- https://docs.python.org/3/library/decimal.html
- https://docs.python.org/3/library/argparse.html
- https://docs.python.org/3/library/csv.html
- https://docs.python.org/3/library/tomllib.html
- https://docs.python.org/3/library/dataclasses.html
- https://docs.python.org/3/library/random.html
- https://docs.python.org/3/library/html.html
- https://docs.python.org/3/library/contextlib.html
SQLite, testing, tooling:
- https://www.sqlite.org/stricttables.html
- https://docs.pytest.org/en/stable/getting-started.html
- https://docs.astral.sh/ruff/
- https://docs.github.com/en/actions/tutorials/build-and-test-code/python
Agent instruction files:
- https://code.claude.com/docs/en/memory
- https://learn.chatgpt.com/docs/agent-configuration/agents-md

## 16. Honesty and ethics (apply to code, docs, and anything you write about me)
- Say plainly that this is a personal learning project with fake data.
- Never claim it reduces theft or loss, was used by a real business, or follows any bank or legal standard.
- Never claim banking, compliance, or accounting expertise on my behalf.
- Flags are review leads. They are not findings about any person.
- Do not commit any real data. Add data/private/ and *.db to .gitignore.

## 17. Definition of done
- Fresh clone, then the setup commands, then `pytest -q` all green (with ResourceWarning as an error), and `ruff check` clean.
- `drawercheck demo-data && drawercheck import --dir data/demo && drawercheck reconcile && drawercheck report --from 2026-09-01 --to 2026-09-30` works end to end.
- `drawercheck explain 2026-09-03-R1` prints the S1 walkthrough.
- The golden test passes and DEMO_SCENARIOS.md matches the output.
- Every error in TROUBLESHOOTING.md has a test that triggers it, and the message in the guide matches errors.py.
- CSV export passes the sanitize_cell tests.
- CI is green on GitHub and the README is complete (3-step demo, limitations, screenshot placeholder).
- Print this checklist with PASS or FAIL next to each line, based on commands you actually ran.