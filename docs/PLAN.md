# DrawerCheck plan

Status: M0 prepared for review. Wait for the user's **go** before M1.

## Purpose and boundaries

DrawerCheck is a personal learning project using fictional data for **Demo Store #001**. It compares a closing drawer count with POS records, flags differences for human review, and later compares daily cash with simplified bank deposits. It must be simple enough to explain in a job interview.

Build an offline Python command-line tool with SQLite, integer cents, and text, HTML, and CSV reports. Runtime dependencies are standard library only. Development tools are pytest and Ruff. Use Python 3.12-compatible code, a `src` layout, setuptools, and the `drawercheck` console command.

Do not build a web application, integrations, accounts, cloud services, machine learning, compliance features, additional currencies, tips, payroll, or bank file formats. R03, R06, and R07 are optional and require a later request. Flags describe records, never conclusions about people. Do not claim business use, loss reduction, professional expertise, or compliance with a standard.

## Working agreement

- M0 creates only this file. No application code, dependency installation, or generated data. Review the plan and stop for **go**.
- Starting with M1, complete one milestone, run the tests and both Ruff checks, add the learning-log entry, and commit that milestone. Summarize in at most five lines and stop for **next**.
- Each learning-log entry has three bullets: what was built, what was learned, and one interview question. Record M0's learning entry during M1 so M0 still creates only this file.
- Explain decisions briefly in plain English. Use small functions, descriptive names, type hints, and a one-line docstring on each public function. Use frozen dataclasses where practical. Do not use em dashes or middle dots.
- Choose the simplest reasonable option and update Decisions below. Ask only when blocked. Do not silently add features or weaken required checks.
- Treat 10 to 20 hours as the user's planning estimate, not a promise. The work blocks below target 30 to 60 minutes each. Split any growing block before continuing; defer optional polish instead of dropping required correctness checks.

## Milestones, files, and completion checks

Paths below are relative to the repository root. Each milestone includes relevant tests and a learning-log update, except M0.

| Milestone | Work blocks, each intended to fit within one hour | Main files | Completion check |
| --- | --- | --- | --- |
| M0: Plan | Read references; identify gaps; write and review this plan. | `docs/PLAN.md` only | Plan covers milestones, files, risks, decisions, and reference access. Stop for **go**. |
| M1: Skeleton | Package and help command; money and errors; connection helper and tests. | `pyproject.toml`, `.gitignore`, `LICENSE`, `README.md`, `AGENTS.md`, `CLAUDE.md`, `src/drawercheck/{__init__,cli,money,errors,db}.py`, `tests/{test_money,test_db,test_cli}.py`, `docs/LEARNING_LOG.md` | Editable installation works; `drawercheck --help` works; money parsing rejects invalid forms; connection closes on success and failure; pytest and Ruff pass. |
| M2: Database and imports | STRICT schema and `init-db`; deterministic demo generator; row validation and inserts; rollback, duplicate, and CSV edge tests. | `db.py`, `demo.py`, `importer.py`, `cli.py`, `errors.py`, `data/demo/*.csv`, `tests/{test_demo,test_importer}.py`, `docs/DEMO_SCENARIOS.md` | `demo-data` and `import` work; all seven files import together; any failure rolls back; identical files are skipped; malformed-CSV tests pass. Scenario expectations are documented but later rules are clearly marked pending. |
| M3: Core reconciliation | Config, models, and formulas; R01/R02/R05; R09 and missing-data handling; saved flags and `explain`. | `config.toml`, `src/drawercheck/{config,models,reconcile,rules}.py`, updates to `db.py`, `cli.py`, `errors.py`, `tests/{test_config,test_reconcile,test_rules}.py`, `docs/HOW_IT_WORKS.md` | Worked example gives 51,875 expected cents, -2,000 variance cents, and 119,875 deposit cents. S1, S2, S4, S7, and S8 pass. Repeated reconciliation gives the same flags. |
| M4: Reports and usable demo | Shared report data and text output; escaped HTML; safe CSV, CLI errors, and README demo. | `src/drawercheck/reports/{__init__,text,html,csv_out}.py`, `csv_safety.py`, updates to `cli.py`, `errors.py`, `tests/{test_reports,test_csv_safety}.py`, `examples/sample_report.html`, `README.md` | All three formats work; CSV protects every cell; HTML is offline and readable; README has three demo steps and a clearly marked screenshot placeholder. Sample report honestly says pattern and deposit rules arrive in M5. |
| M5: Patterns and deposits | R04 and its history tests; R08 and matching edge cases; full demo expectations and refreshed sample. | Updates to `rules.py`, `reconcile.py`, reports, `tests/{test_deposits,test_golden}.py`, `docs/{DEMO_SCENARIOS,HOW_IT_WORKS}.md`, `examples/sample_report.html` | Every required rule has triggered and not-triggered tests. Full S1 to S8 expected flag set matches exactly; S9 preserves all row counts. Deposit matching limits are demonstrated. |
| M6: Polish and delivery | README and concept docs; tested troubleshooting; CI and fresh-install verification; interview material and final checklist. | `README.md`, `docs/{HOW_IT_WORKS,TROUBLESHOOTING,INTERVIEW_NOTES,LEARNING_LOG}.md`, `.github/workflows/ci.yml`, `tests/test_troubleshooting.py` | Documentation matches actual messages and output; local checks pass; report GitHub CI status only after observing it. Deliver three resume bullet options, repository description/topics, and five interview questions with honest answers. |
| M7: Optional | Plan and implement only the stretch rules explicitly requested later. | Relevant rule, demo, test, and documentation files | Not authorized by this plan. |

## Intended structure

Keep the data flow visible: CSV files enter `importer.py`, records are stored through `db.py`, `reconcile.py` prepares the calculations, `rules.py` returns flags, and report modules display the results. `cli.py` connects these steps without containing the business math.

| File or folder | Responsibility |
| --- | --- |
| `money.py` | Strict dollar-string parsing and the single cents-to-currency formatter. |
| `errors.py` | Application exception classes and all user-facing error templates. Also hold the documented informational notices for skipped files and missing config. |
| `db.py` | Connection setup, schema, fixed SQL statements, and database reads/writes. No ORM or migration framework. |
| `importer.py` | Exact headers, row validation, duplicate detection, SHA-256 checks, and one import transaction. |
| `models.py` | `Shift`, `ShiftResult`, and `Flag` dataclasses. Evidence is a small dictionary serialized as JSON. |
| `config.py` and `config.toml` | Defaults, TOML loading, and validation of configurable thresholds. |
| `reconcile.py` | Expected cash, counted cash, variance, daily deposit totals, rule inputs, and atomic replacement of flags. |
| `rules.py` | Small pure rule functions, which return flags without reading files or changing the database. Register rules in `RULES`; call the daily deposit rule once for its daily context. |
| `demo.py` | Reproducible fictional CSVs and deliberately chosen scenarios. |
| `reports/` and `csv_safety.py` | Text, self-contained HTML, and protected CSV exports. Reuse the same calculation helpers. |
| `tests/` | Unit tests, temporary-database tests, CLI smoke tests, and the full-demo expected-output test. |
| `docs/` and `examples/` | The math, learning log, scenarios, troubleshooting, interview notes, and an actual generated HTML report. |

## Decisions

These choices resolve gaps in the brief without adding a larger product. Revisit a choice only when implementation evidence requires it.

1. **Development environment.** An existing Python 3.13.5 installation reports SQLite 3.47.1, satisfying both requirements. Its executable is `/Users/mdamdadhossain/.local/share/uv/python/cpython-3.13.5-macos-aarch64-none/bin/python3.13`. Use it to create `.venv` in M1. Do not rely on the system Python, which reports 3.9.6. Document generic setup commands for other machines rather than this personal path in README.

2. **Money input is deliberately strict.** Accept ASCII dollar strings with exactly two decimal digits, with an optional minus sign in the general parser. Reject exponent notation, commas, currency symbols, spaces, NaN, infinity, and different decimal lengths. Construct `Decimal` from the validated string, then convert to cents. Enforce each input column's nonnegative or positive requirement separately. Reject values outside SQLite's signed 64-bit integer range before insertion. Format negative values as `-$20.00`, using integer arithmetic.

3. **Percentage thresholds never use binary floats.** Load TOML using `parse_float=Decimal`. Convert the configured percentage to an exact integer numerator and denominator. Calculate percentage cents with integer division, rounding down to a whole cent. The review threshold is `max(warn_cents, min(review_cents, percentage_cents))`. At zero cash sales the floor remains `warn_cents`. Validate nonnegative tolerances, `within_tolerance_cents < warn_cents <= review_cents`, a positive finite percentage, and sensible history settings. Test boundary cents explicitly. [TOML documentation](https://docs.python.org/3/library/tomllib.html)

4. **Preserve all supplied defaults.** Use 100 cents tolerance, 500 warn, 2,000 review, 1.0 percent, three short shifts within ten, 2,000 cents for verifier/note requirements, 20,000 retained cents per register, and three calendar days of deposit lag. Keep the 40,000-cent drop setting documented as inactive until R06 is requested. A missing config uses defaults with one informational line; a malformed existing config is an error. These are example policies, not standards.

5. **Connections and transactions have different jobs.** `db.connect(path)` first checks SQLite >= 3.37.0. Open with `autocommit=True`, set `PRAGMA foreign_keys = ON` and `sqlite3.Row`, then set `autocommit=False` before returning. This enables foreign keys before opening a transaction. Close the connection if setup fails. Every caller uses `with closing(db.connect(path)) as con:` and an inner `with con:` for a transaction. Bind values with `?`; never format SQL. Avoid `executescript` inside the import transaction. [Python transaction documentation](https://docs.python.org/3.13/library/sqlite3.html), [SQLite foreign-key setting](https://www.sqlite.org/pragma.html#pragma_foreign_keys)

6. **Use the supplied schema with one small bookkeeping addition.** Keep the nine supplied tables and indexes on shift business date and cashier. Enforce the allowed denominations during import and with a database CHECK constraint. Add a small STRICT `reconciled_dates` table in M3, recording each processed date, the config snapshot, and completion time. This distinguishes a successful run with zero flags from a run that never happened. No general audit system or schema migration tool.

7. **Imports use a fixed, readable contract.** Require the seven named CSV files and their exact column names; column order may vary. Reject duplicate header names and rows with missing or extra fields. Use `utf-8-sig`, `newline=""`, and strict CSV parsing. Ignore fully blank records. Empty files are errors; header-only files import zero rows. Keep physical source line numbers, including both locations in duplicate errors. Validate dates and timestamps in the exact specified forms; allow blank optional fields only.

8. **Import everything or save nothing.** Import cashiers and registers before shifts, then dependent records and deposits, inside one transaction including `import_log`. Hash the raw bytes that are actually parsed. Skip already-recorded hashes without changing rows. Detect duplicate business keys in a file, including cashier/register IDs, shift codes, POS shift codes, and count shift/denomination pairs. For drops and deposits, reject exact repeated records. Changed files do not silently update existing records: explain conflicts and use a fresh demo database for regenerated datasets. No upsert or data-repair command in MVP. `import` can initialize an absent database so the required demo command chain works without a separate `init-db` step.

9. **Incomplete data is not zero cash.** No count rows means counted cash and variance are unknown, with R09 review. Count rows whose quantities are all zero mean a real zero count. Missing POS totals likewise produce an explicit R09 review and unknown expected cash. Do not run variance-dependent rules on an unknown variance, include it in a cashier shortage total, or claim a complete deposit total for that day. Reports show an incomplete status/count. Invalid timestamp ordering is accepted as well-formed input so R09 can flag S8; it does not erase otherwise available monetary calculations.

10. **Keep exact variance and tolerance status separate.** Preserve the signed difference in cents even when it is within tolerance. Reports classify such a drawer as balanced within tolerance and still show its actual difference in details. R01 alone has the tolerance exemption. R02 independently checks its six listed bill amounts, including $1. Ordinary demo noise will stay strictly below $1 so it does not create unplanned R02 flags.

11. **Keep reconciliation repeatable and reports current.** Replace flags and completion markers for the requested inclusive date range in one transaction. A successful import of any new rows clears previously calculated flags and markers in the same transaction; skipped files do not. Store the effective config so reports and `explain` use the same settings. If a later reconciliation changes settings, clear prior results before saving the new range rather than mixing policies. A zero-flag completed date can be reported. If a requested date containing shifts has not been reconciled, print the required text: `No flags found. Run \`drawercheck reconcile\` first.`

12. **Date ranges must not change the underlying evidence.** An omitted endpoint uses the relevant earliest or latest stored date, never today's date. Reject reversed ranges. Load earlier cashier shifts for R04 even when they fall before `--from`. Evaluate register overlaps against surrounding shifts too. Order history by business date, opening time, and shift code, including the current shift and excluding later shifts. Retain incomplete shifts in the history window but do not count them as short. Report the actual window size when fewer than ten shifts exist. R04 can flag a later balanced shift if its rolling window still qualifies; document all such expected occurrences.

13. **One closing shift per register/day remains the supported model.** Do not silently sum multiple closing counts as if they were independent drawers. If this assumption is violated, add R09 review and mark that day's deposit calculation incomplete. Detect actual register overlaps separately; adjacent shifts where one ends exactly when the next starts do not overlap. Open shifts are listed as open and excluded from closing arithmetic; a day with an open or uncounted drawer is incomplete for deposits.

14. **Fill the one missing deposit branch conservatively.** Process positive expected deposits by business date. Search inclusive windows through `D + max_lag_days`. Choose an exact match first, breaking ties by deposit date then ID. With exactly one nonmatching candidate, consume it and flag the difference, using its absolute size for severity. With no candidate, flag missing. If multiple candidates exist but none matches exactly, issue a review flag saying no unique match was found and leave them unmatched. Remaining unmatched deposits receive info flags. Do not guess an amount-based match or combine deposits.

15. **Deposit matching uses the full imported history.** Recompute greedy matching in memory across all available business dates and deposits, then save flags whose business date falls in the selected range. Attribute unexpected deposits to their deposit date. This prevents a filtered run from borrowing a deposit already consumed by an earlier day. No persistent matches table is needed. An incomplete day's expected deposit is unknown, so it cannot be matched; any remaining bank entry must remain visibly unmatched. Missing-deposit flags describe the imported dataset, with no claim that the real-world waiting period has elapsed.

16. **Choose demo inputs to exercise the actual algorithm.** Fix the start at 2026-09-01 and use `random.Random(seed)` with integer draws. Apply explicit scenario overrides after normal data generation. Assign S3 and S4 to R1 where the brief omits the register, and control cashier_03's schedule so S3 remains inside the ten-shift window. Choose enough sales for S4's $5 difference to be warn rather than review. For S5, omit the September 16 deposit and put the separate September 17 to 19 deposits on September 20, keeping the missing day's search window empty. For S6, keep only its mismatched deposit inside September 21 to 24 by moving September 22 to 24 deposits to September 25. Each later deposit remains within its own allowed lag. Omit the September 25 day's own deposit because S7 makes its expected total unknown. Keep ordinary deposit amounts distinct. These are deliberately constructed examples, documented as such. Shorter `--days` runs include only scenarios whose shift dates exist; positive day counts are required.

17. **Explain the matching limitation with concrete numbers.** Suppose September 1 and 2 each expect $500. The only imported $500 deposit, dated September 2, actually belongs to September 2. Greedy matching assigns it to September 1 and reports September 2 missing. Amount/date alone cannot identify ownership. Also document combined multi-day deposits, overlapping windows, weekends/holidays, and incomplete records as limitations. Do not silently replace the specified simple algorithm with a complex matcher.

18. **Make CLI behavior consistent.** Keep all requested subcommands. Add `--db PATH` to `report` and `explain` so every database command can use the same temporary or user-selected database. Default to `./drawercheck.db`. Report defaults to text on stdout; `--out` writes the selected format to a file. `--date` cannot combine with range arguments. `main(argv)` returns 0 or 1, with help returning 0. Override argparse's default error handling to use exit 1 and an error template from `errors.py`. Translate expected input, configuration, SQLite, unknown-shift, and output-path failures without Python tracebacks. [argparse documentation](https://docs.python.org/3/library/argparse.html)

19. **Reports stay safe and easy to explain.** HTML contains inline CSS, semantic tables, a viewport tag, light/dark styles, a generated-on line, the demo banner, and written severity labels. Escape every displayed dynamic value with `html.escape`; no JavaScript or remote assets. Apply `sanitize_cell` to every CSV header and data cell after converting it to text, preserving and protecting all six specified dangerous first characters. Test rendering with hostile-looking strings. Pass a fixed generation timestamp in tests so only the actual report uses the current clock.

20. **Use evidence-based wording and documentation.** R04 will say that repeated shortages need review and recounting, without presenting the example's unsupported claim about the most common cause as a measured fact. Required troubleshooting entries will quote actual `errors.py` messages and have tests that trigger them. Choose ten genuine errors, including money format, denomination, unknown shift, old SQLite, locked database, read-only database, unwritable report path, report before reconciliation, bad CSV headers, and invalid config. Describe skipped imports and missing config as informational notices, not failures. Keep source/product names only in attributed reading and tooling references; all business examples and identities remain fictional.

21. **Keep instruction files and delivery lightweight.** `AGENTS.md` stays under 150 lines and includes the project summary, commands, conventions, stop points, and documentation links. `CLAUDE.md` contains only `@AGENTS.md`. Ignore `.venv/`, caches, build output, `*.db` and SQLite sidecar files, and `data/private/`. Use an MIT license attributed to DrawerCheck contributors rather than inventing a personal legal name. Commit milestones locally; publishing or claiming remote CI success is a separate observable step.

22. **Recheck CI versions during M6.** The supplied GitHub tutorial currently shows `actions/checkout@v6` and `actions/setup-python@v5`, while the official latest-release pages currently show v7.0.1 and v7.1.0 respectively. Follow the tutorial's structure, use supported current action releases after checking again, and document that update rather than claiming its examples are current. Test Python 3.12, 3.13, and 3.14. Add the badge once the actual repository/workflow URL is confirmed. [GitHub tutorial](https://docs.github.com/en/actions/tutorials/build-and-test-code/python), [checkout release](https://github.com/actions/checkout/releases/tag/v7.0.1), [setup-python release](https://github.com/actions/setup-python/releases/tag/v7.1.0)

## Math and test commitments

All monetary values below are integer cents internally:

- Expected drawer = opening float + cash sales + paid-ins - cash refunds - paid-outs - safe drops.
- Counted drawer = sum of denomination cents multiplied by quantity.
- Variance = counted drawer - expected drawer.
- Expected daily deposit = total counted cash + total safe drops - retained float multiplied by registers closed, only when the day's required inputs are complete.
- Worked example: 20,000 + 125,075 - 1,200 - 2,000 - 90,000 = 51,875 expected; 49,875 counted gives -2,000 variance; 49,875 + 90,000 - 20,000 = 119,875 deposit.

The count sheet stays independent of POS totals. Explain blind counting as a human practice, without pretending code can prove when someone looked at the expected total. Card sales are imported but excluded from cash calculations.

Use the supplied denomination list: 10000, 5000, 2000, 1000, 500, 200, 100, 50, 25, 10, 5, and 1 cents. R02 uses only 100, 500, 1000, 2000, 5000, and 10000 cents.

The test suite must cover:

- Money parsing/formatting, `0.10`, negative display, invalid precision, exponent rejection, and no float-based money arithmetic.
- Parameterized formulas and threshold boundaries; triggered/not-triggered cases for every implemented rule.
- BOM, missing/wrong/extra/duplicate headers, empty/header-only files, blank lines, quoted commas, multiline records, Windows line endings, invalid row widths, exact file/line/column errors, duplicate locations, and transaction rollback.
- Hash-based repeated imports with no row-count changes; fresh-data imports invalidating old results; repeated reconcile with identical output; partial date ranges with earlier history.
- Connections closed normally and on failure. Set pytest `addopts = "-W error::ResourceWarning"`; only change the warning strategy if demonstrated flaky, keeping explicit closure tests and recording why.
- Deposit exact/mismatch/missing/unexpected/ambiguous outcomes, inclusive lag boundaries, tied amounts, the documented greedy failure, and incomplete days.
- Each translated CLI error through `main(argv)` and temporary paths; no network or dependence on today's date. Simulate permission failures where OS behavior would otherwise vary.
- HTML escaping and all six CSV danger prefixes: `=`, `+`, `-`, `@`, tab, and carriage return.
- A full-demo test asserting the complete expected flag set by date, shift, rule, and severity, not merely that selected flags exist. S1 must lack R05, S2 must include it, S3 must include R04 on September 14 and 18, S4 must remain warn, S5 must be missing, S6 must be a review mismatch, and S7/S8 must have their intended integrity findings.

## Risks and how to contain them

| Risk | Planned response |
| --- | --- |
| Import validation grows beyond the time budget. | Separate header handling, value parsers, and explicit per-file handlers. Avoid a generic import framework. |
| One error creates misleading follow-on flags. | Preserve unknown values; suppress calculations that need missing inputs; show incomplete days explicitly. |
| Demo expectations fight the greedy deposit rule or history window. | Pin scenario dates, cashier assignments, deposit timing, and expected flags. Test the complete generated output in M5. |
| Partial runs reuse deposits or miss prior cashier history. | Calculate against full required context before filtering stored/output dates. |
| Reporting zero flags incorrectly means no reconciliation. | Store completion separately from flags and test a clean, balanced dataset. |
| A documentation example is mistaken for a standard. | Attribute references and label thresholds, matching, and demo data as learning examples. |
| Python or SQLite behavior differs by machine. | Check SQLite at startup; use the verified local interpreter; test supported Python versions in CI. |
| CI cannot be observed locally. | Finish the workflow and local verification, report the exact remote access limitation, and do not mark remote CI as passing without a real run. |

## Verification and milestone handoff

README and AGENTS.md will include these commands, with Python 3.12 or newer as a prerequisite and 3.13/3.14 recommended for development:

```text
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
ruff check . && ruff format --check .
drawercheck --help
```

After each implementation milestone, record the commands actually run and their outcomes, add its three-bullet learning entry, commit only the milestone files, and stop. M0 has no tests or linter yet, so its verification is a document and scope review, not a claimed test pass.

At M6, test a clean checkout with a new environment and run the exact required demo chain:

```text
drawercheck demo-data && drawercheck import --dir data/demo && drawercheck reconcile && drawercheck report --from 2026-09-01 --to 2026-09-30
drawercheck explain 2026-09-03-R1
drawercheck report --from 2026-09-01 --to 2026-09-30 --format html --out examples/sample_report.html
```

Print PASS or FAIL for each definition-of-done item, with an explanation for anything not verified. Do not describe an unrun check as passing. The checklist covers the fresh install and quality checks, demo chain, S1 explanation, complete expected flags, tested troubleshooting messages, CSV safety, and observed GitHub CI plus the finished README. Count tests with an actual collection command before using a number in career material.

## Reference review

Reviewed on 2026-10-22. Concept references were consulted before the implementation plan. Their broader accounting, staffing, and security guidance does not expand this project's scope. The supplied brief remains the implementation contract.

### Reconciliation concepts

| Supplied reference | Access and use |
| --- | --- |
| [Drawer reconciliation](https://docs.wcpos.com/reports/reconciliation) | Read. Confirms the float, cash sales, refunds, drops, and payouts relationship. |
| [Balancing a cash drawer](https://www.shopify.com/blog/balancing-a-cash-drawer) | Read. Supports independently counting before comparison and documenting cash movements. |
| [End-of-day close and three-way reconciliation](https://beancount.io/blog/2026/09/14/end-of-day-close-z-reports-cash-drawer-daily-sales-reconciliation-guide) | Read. Background for blind counts and separate POS, physical cash, and bank comparisons. |
| [Daily sales and bank deposits](https://beancount.io/blog/2026/10/12/daily-sales-reconciliation-cash-heavy-business-pos-till-bank-deposit-guide) | Read. Background for preserving the prepared deposit amount through the bank handoff. Use the brief's explicit float/refund/payout formula. |
| [Example cash-handling checklist](https://app.manifest.ly/public/checklists/cash-handling-checklist) | Read. Example thresholds and second-person review only; does not establish industry standards or validate every DrawerCheck default. |
| [Supplied cash-count article](https://help.hotschedules.com/hc/en-us/articles/4404885792781) | Direct retrieval failed and the exact article was not located. Read this official replacement: [Mobile Cash Reconciliation](https://help.hotschedules.com/hc/en-us/articles/28816788225293-MacromatiX-Mobile-Cash-Reconciliation), which describes blind counts and required variance comments. Do not claim the original page was read. |
| [Cash over and short](https://www.accountingtools.com/articles/what-is-the-cash-over-and-short-account.html) | Read. Background for recording differences; no ledger posting or professional accounting claims will be added. |

### Python, database, and tooling references

| Reference | Detail used in the plan |
| --- | --- |
| [sqlite3](https://docs.python.org/3/library/sqlite3.html) | Parameters, row objects, explicit transaction behavior, and connection ownership; also checked the Python 3.13 page. |
| [Decimal](https://docs.python.org/3/library/decimal.html) | Construct from strings and avoid float conversion; enforce the CSV spelling separately. |
| [argparse](https://docs.python.org/3/library/argparse.html) | Subcommands and deliberate override of the normal usage-error exit code. |
| [csv](https://docs.python.org/3/library/csv.html) | Correct newline handling, readers/writers, and physical line tracking. |
| [tomllib](https://docs.python.org/3/library/tomllib.html) | Binary file loading and `parse_float=Decimal`. |
| [dataclasses](https://docs.python.org/3/library/dataclasses.html) | Readable records with frozen fields where appropriate. |
| [random](https://docs.python.org/3/library/random.html) | A dedicated seeded generator for fake data, independent of global state. |
| [html](https://docs.python.org/3/library/html.html) | Escaping text and quoted values. |
| [contextlib](https://docs.python.org/3/library/contextlib.html) | `closing()` reliably closes owned connections. |
| [SQLite STRICT tables](https://www.sqlite.org/stricttables.html) | Minimum SQLite version and stricter storage types. |
| [pytest getting started](https://docs.pytest.org/en/stable/getting-started.html) | Assertions and isolated temporary paths. |
| [Ruff](https://docs.astral.sh/ruff/) | Linting and formatting configured in `pyproject.toml`. |
| [GitHub Python CI tutorial](https://docs.github.com/en/actions/tutorials/build-and-test-code/python) | Matrix workflow structure; official action release pages were checked separately as recorded in Decision 22. |
| [Claude instruction files](https://code.claude.com/docs/en/memory) | A `CLAUDE.md` file can import the shared `AGENTS.md`. |
| [AGENTS.md guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | Project conventions and instruction-file scope. |

The rolling `/3/` Python links may show newer APIs than the supported minimum. During implementation, verify any unfamiliar API against the Python 3.12 or 3.13 documentation rather than adopting a newer-only feature.
