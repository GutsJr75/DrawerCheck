# DrawerCheck

DrawerCheck is a personal learning project for checking end-of-shift cash drawers
with fictional data from **Demo Store #001**. It imports CSV files, compares
counted cash with POS totals, flags differences for human review, and explains
each shift. It exports terminal text, a self-contained HTML report, and a CSV
of review flags.

**Current milestone: M5, patterns and deposits complete.** Installation, exact
money handling, database tables, fake demo generation, validated imports, cash
calculations, six required review rules, shift explanations, and three report
formats are implemented, including repeated-shortage checks and simplified bank
matching. M6 core polish is next.

A public browser demo is now planned after the core is complete. Visitors will
be able to run the built-in fake-data example or upload synthetic CSVs, inspect
the results, and download reports. This frontend is not implemented yet; see the
[approved web plan](docs/WEB_PLAN.md).

## Why I am building it

I worked two POS registers at a busy convenience store and counted cash at close.
I compared the cash in my register with transaction records.
This project lets me practice those careful checks in code and explain the work
in a job interview.

## Set up and check the project

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
development tools requires internet access during initial setup. The command-line
core makes no network calls. The planned public web layer will be a separate
optional installation that handles browser requests.

Running `drawercheck` without arguments also prints help. An invalid argument
prints a short error and returns exit code 1; successful help returns 0.

## Try it in 3 steps

Start in the project folder with Python 3.12 or newer. All inputs below are fake.

1. Install the command in a virtual environment:

   ```sh
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

2. Generate, import, and reconcile the demo in a fresh example database:

   ```sh
   drawercheck demo-data
   drawercheck import --dir data/demo --db demo-m4.db
   drawercheck reconcile --db demo-m4.db
   ```

3. Create the HTML report, then open the file in a browser:

   ```sh
   drawercheck report --db demo-m4.db --from 2026-09-01 --to 2026-09-30 --format html --out demo-report.html
   ```

The [committed sample report](examples/sample_report.html) contains the same
60 shifts and 16 review flags. It works offline, with no external assets or scripts.
The file includes daily summaries, review leads, cashier totals, and shift
calculations, including repeated-shortage and bank-deposit review leads. It
explains the limits of simplified bank matching.

**Screenshot placeholder:** a real report screenshot will be added after a
browser capture is available. The M4 browser preview was blocked by the tool's
local-file security policy; no screenshot or visual verification is claimed.

## Generate and import demo inputs

After setup, run:

```sh
drawercheck init-db
drawercheck demo-data
drawercheck import --dir data/demo
```

The default generator writes 30 days starting at 2026-09-01, with seed 42 and two
registers. It writes the seven named CSVs in `data/demo`; existing files with
those names are replaced. Unrelated files in the folder are preserved.
`init-db` preserves existing records and is optional because `import` also
creates tables when needed. The default database is `./drawercheck.db`.

Run the import command again to see an `already imported; skipped` line for
each file. Identical inputs add no duplicate records and do not change the log.

For a separate dataset, choose a different folder and database path:

```sh
drawercheck demo-data --out data/another-demo --days 7 --seed 17
drawercheck import --dir data/another-demo --db another-demo.db
```

See the [demo scenarios](docs/DEMO_SCENARIOS.md) for the deliberately constructed
shortages, overage, deposit inputs, and incomplete records. M2 verified the
input conditions; M5 verifies all 16 required flags, including patterns and
deposit exceptions, with no unexpected extras.

## Reconcile and explain a shift

After importing the demo data:

```sh
drawercheck reconcile
drawercheck explain 2026-09-03-R1
```

The worked shift shows $518.75 expected, $498.75 counted, and a -$20.00
difference. It receives a variance review flag and a single-bill hint. Both its
verifier and note are present, so it has no missing-verification flag.

`reconcile` accepts `--from`, `--to`, `--db`, and `--config`. `explain` accepts
`--db` and uses the settings saved during reconciliation. For example:

```sh
drawercheck reconcile --from 2026-09-01 --to 2026-09-03 --db another-demo.db
drawercheck explain 2026-09-03-R1 --db another-demo.db
```

`config.toml` contains example policies. A missing file uses defaults with an
informational notice; an invalid existing file is an error. Repeating a run
replaces that range's results. Changing settings clears earlier results so
different policies cannot be mixed. New imported records also clear results.
Percentages must be greater than 0 and at most 100, with at most six decimal
places. Deposit lag must be a whole number from 0 through 31 days. These are
project limits. An empty date selection gives a specific error and preserves
saved results. A database without the required tables gives import guidance.

After updating from M3/M4 or the initial M5 release, run `drawercheck reconcile`
again without date filters to refresh all saved results under policy version 4.

Missing counts remain unknown, while an actual count of zero stays zero. Open
shifts are excluded from closing calculations. Daily expected deposit amounts
are calculated only for complete days. Bank matching compares positive expected
amounts with imported entries using the configured calendar-day lag.
For this demo, every register listed in `registers.csv` is expected on every
business date present in the shift inputs. A missing register's shift makes
the daily deposit unknown and produces a date-level R09 review flag.
See [how it works](docs/HOW_IT_WORKS.md) for formulas and rule explanations.

## Export reports

```sh
drawercheck report --db demo-m4.db
drawercheck report --db demo-m4.db --date 2026-09-03
drawercheck report --db demo-m4.db --format csv --out flags.csv
drawercheck report --db demo-m4.db --format text --out review.txt
```

The default format is text on the terminal. `--out` writes a file; its parent
folder must already exist. CSV contains one row per saved flag, with a blank
shift code for a date-level flag. Every CSV cell is protected against the
specified spreadsheet-formula prefixes, and quoted commas/newlines are retained.

The text and HTML formats share one report dataset. They show daily
balanced/over/short/incomplete/open counts and flags by severity, then all review
leads, exact cashier totals, and individual shift amounts. Unknown cash stays
unknown. Cashier totals include known differences within tolerance and exclude
unknown/open shifts; the number of known records is shown alongside each total.

Reports use the saved reconciliation settings, even if `config.toml` changes.
Every selected business date containing shifts must already be reconciled. A
clean completed date is reportable; an unchecked date produces the documented
`Run drawercheck reconcile first` guidance and names the first unchecked date.
`--date` cannot combine with `--from` or `--to`. Reports never run reconciliation
or change saved flags.

Report files are written atomically, so a failed replacement preserves the
previous file. Output paths cannot replace the database or its SQLite sidecars.
New files respect the caller's umask; replacements keep the existing report's
permission bits.
The HTML file has inline CSS, light/dark preference, semantic tables, keyboard
section links, and print styling. Narrow tables have labelled scroll regions.

A real terminal excerpt for the worked shift's review leads:

```text
[review] 2026-09-03 2026-09-03-R1 R01_VARIANCE: Short by $20.00. Recount recommended.
[info] 2026-09-03 2026-09-03-R1 R02_SINGLE_DENOMINATION: Variance equals one $20 bill. Check for a miscounted or misplaced bill.
```

## CSV import behavior

- Supply all seven files with the exact column names in the
  [input contract](docs/PROJECT_BRIEF.md#5-csv-input-contract-and-import-rules-folder-datademo).
  Column order may vary. Missing, extra, and duplicate headers are errors.
- UTF-8 files may include an Excel byte-order mark. Quoted commas, quoted
  newlines, Windows line endings, and fully blank records are supported.
- IDs and shift codes must not have surrounding whitespace, line breaks, or
  tabs. Unsafe control and invisible formatting characters are rejected in
  text fields. Multiline free text is preserved; terminal output displays its
  line breaks and tabs as visible escapes, so a note cannot fake output lines.
- Money must use exactly two decimal places. Quantities must be nonnegative
  whole numbers, and counts may use only the specified bills and coins.
- Each validation error names the file, physical starting line, column, and
  reason. Header-only files are valid and report zero imported rows; an empty
  file is an error.
- All files and their import-log entries are saved in one transaction. A failed
  import leaves existing data unchanged. An unsuccessful first import may leave
  an empty database file, with no saved tables or records.
- File hashes compare exact bytes. A changed file is checked again, even if its
  only change is line endings. Existing records cannot be silently overwritten.
  Use new-record-only files or a fresh database for regenerated demo data.
- New imported records clear old flags and any completion markers. Identical
  skipped imports leave results unchanged.

## Foundation decisions

- Money is stored and calculated as integer cents. `parse_dollars("0.10")`
  returns the integer `10`, and `format_cents(125075)` returns `"$1,250.75"`.
- Dollar inputs require exactly two decimal places. The shared parser accepts
  negative amounts; import handlers enforce each column's sign rule.
- Database connections enable foreign keys and return rows accessible by column
  name. Use `contextlib.closing` to close a connection, with a separate inner
  transaction block to save or roll back changes.
- Tests treat leaked-connection warnings as errors.

## Limitations and progress

This is a learning project using fake data, not a tool for real cash control.
Flags are neutral leads for human review. The project does not claim
banking, compliance, or accounting expertise, and it is not accounting or legal
advice. Configurable thresholds are examples,
not industry standards.

The supported closing model is one shift per listed register per imported
business date. There is no register operating schedule or store calendar;
a day absent from the shift inputs cannot be inferred automatically.
Bank matching is deliberately simplified. It first reserves exact matches for
all days, then reviews unresolved days against the remaining entries. Each pass
processes dates in order and consumes each matched entry once. This helps show
an ordinary one-cent difference as one warning when later days have their own
exact matches. Equal-amount days and overlapping windows can still assign an
entry to the wrong day. For example, if September 1 and 2 each expect $100.00 and
the only $100.00 entry is dated September 2, the earlier day takes it, even if its
reference names September 2. The later day is then flagged as missing.
Combined deposits, several deposits added together, and real banking calendars
are outside the MVP. Weekends and holidays use calendar-day lag. Missing-deposit
flags describe the imported dataset, not a real-world overdue payment. There
are no real POS or bank integrations.

See the [milestone plan](docs/PLAN.md) for scope and decisions, and the
[learning log](docs/LEARNING_LOG.md) for completed work and verification.
The [original project brief](docs/PROJECT_BRIEF.md) preserves the input contracts
and scenario requirements for future work. Its original web/hosting exclusions
were superseded by the public-frontend amendment in the current plan.
M5's required rules are complete. M6 core polish and the M7/M8 public app remain
future work.
