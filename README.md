# DrawerCheck

[![Core checks](https://github.com/GutsJr75/DrawerCheck/actions/workflows/ci.yml/badge.svg)](https://github.com/GutsJr75/DrawerCheck/actions/workflows/ci.yml)

DrawerCheck checks end-of-shift cash drawers. It compares the cash a register
should hold, based on its sales records, with the cash that was actually
counted. Differences become review leads for a person to look at, and the
results can be saved as a text, web page (HTML), or spreadsheet (CSV) report.

It is a personal learning project. Every store, person, and amount comes from
the fictional **Demo Store #001**.

**[Try the public demo](https://drawercheck.onrender.com)** without installing
anything. Select **Try the example**, open a drawer from the results, and
download a report. The example checks 60 drawers.
To try uploads, select **Upload demo CSVs** and use the seven example files
provided on that screen. Use fictional data only.

Results disappear when you refresh or close the page. Download a report to keep
a copy. The free server may take about a minute to wake up after inactivity.

**The redesigned screens are implemented:** grouped drawer review, exact cash
outcomes, and two-step file preparation. On 2026-10-28 the public assets
matched block 7 commit `62650f9`, including its two QA fixes. Chrome and WebKit
each passed the public example, fake upload, reports, and refresh checks.
See the [redesign checklist](docs/M10_CHECKLIST.md) for remaining manual checks.
R06 and R07 remain later M9 blocks.

## Why I am building it

I worked two POS registers at a busy convenience store and counted cash at close.
I compared the cash in my register with transaction records.
This project lets me practice those careful checks in code and explain the work
in a job interview.

## Project status

| Part | Status |
| --- | --- |
| Command-line tool: imports, checks, explanations, and reports | Done |
| Seven review rules, including the R03 swapped-digit heuristic | Done; R03 verified locally, on GitHub, and live |
| Web request layer, website screens, public hosting, and documentation | Delivered through M8 block 7; live at [drawercheck.onrender.com](https://drawercheck.onrender.com) |
| M10 Tick and tie redesign | All views implemented; local and hosted checks recorded, with manual validation gaps listed below |
| Remaining optional rules (R06, R07) | Later M9 blocks; stop for review after each block |

**Automated checks:** [GitHub Actions run 40706484429](https://github.com/GutsJr75/DrawerCheck/actions/runs/40706484429)
for block 7 commit `62650f9` passed on Python 3.12, 3.13, and 3.14, including
both Ruff checks and optional web/server tests, observed on 2026-10-28.
It includes both block 7 fixes. That block's local checks passed 729 tests and 216
Chrome/WebKit accessibility scans with no detected violations. Actual 400%
browser zoom, a real screen reader, and first-time-user usability remain
unverified. No full accessibility certification is claimed; the
[M10 checklist](docs/M10_CHECKLIST.md) separates passes and open checks.

The [October 29 upload repair](docs/M10_UPLOAD_REPAIR.md) stops an old check
from updating replaced files. It adds opt-in, repeatable browser regression
checks and is verified locally only; the hosted result above predates it.
The full local suite with optional browser checks enabled passes 731 tests.

## Try the command line in 3 steps

You need Python 3.12 or newer. All inputs below are fake.

1. Install the command in a virtual environment:

   ```sh
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

2. Create the example data, load it, and run the checks:

   ```sh
   drawercheck demo-data
   drawercheck import --dir data/demo --db demo.db
   drawercheck reconcile --db demo.db
   ```

3. Create the web page report, then open the file in a browser:

   ```sh
   drawercheck report --db demo.db --from 2026-09-01 --to 2026-09-30 --format html --out demo-report.html
   ```

For an offline example, open the
[committed sample report](examples/sample_report.html). It covers the same 60
shifts and 18 review leads, and works offline with no external files or scripts.

## Screenshots

M10 local Results, captured in Chrome on 2026-10-28 in light mode:

![Results grouping 18 leads into nine drawers and two whole-day dates](docs/screenshots/2026-10-28-m10-block7/2026-10-28-m10-block7-results-results-fixed-chrome-light-1280.png)

M10 local Drawer details, captured on the same date in light mode.
The worked drawer expected $518.75 and counted $498.75:

![Drawer outcome, calculation tape, and count sheet showing a twenty-dollar shortage](docs/screenshots/2026-10-28-m10-block7/2026-10-28-m10-block7-drawer-drawer-fixed-chrome-light-1280.png)

These are pictures of the interactive app. The downloadable HTML report has
its own layout. See the [screenshot timeline](docs/screenshots/README.md) for
Start, upload guidance, narrow screens, and earlier versions.

## What the checks look for

**Expected cash** = opening float + cash sales + paid-ins - cash refunds -
paid-outs - safe drops. Card sales are not physical cash, so they are left out.

**Counted cash** = each bill or coin value times how many were counted.

**Difference** = counted cash - expected cash. Below zero means short; above
zero means over.

Each lead has a severity: **info** (worth a note), **warn** (worth checking),
or **review** (needs a person to review it). The amounts below are the example
settings in `config.toml`, not industry standards.

| Rule | What it looks for |
| --- | --- |
| R01 Cash difference | A difference over $1.00. It becomes warn at $5.00, and review at $20.00 or 1% of cash sales, whichever is lower (but never below $5.00). |
| R02 Single bill | A difference of exactly $1, $5, $10, $20, $50, or $100, which may be one miscounted bill. |
| R03 Possible swapped digits | A whole-dollar difference of at least $9, in either direction, divisible by 9. This is a rough clue only; it does not prove a typo. |
| R04 Repeated shortages | A cashier short by $5.00 or more in at least 3 of their last 10 shifts. |
| R05 Missing sign-off | A difference of $20.00 or more without both a verifier and a written note. |
| R08 Bank deposit | Each day's expected deposit compared with bank entries dated that day or up to 3 days later: a missing deposit, a different amount, or an entry that matches no day. |
| R09 Missing or inconsistent records | A shift with no cash count or sales totals, impossible times, overlapping shifts, two closing shifts for one register and day, negative expected cash, or a register with no shift that day. |

Flags are leads for review, not findings about a person. Missing information
stays "unknown" instead of being treated as zero. For the formulas, a worked
example, and each rule in detail, see [how it works](docs/HOW_IT_WORKS.md).

## Using the command line

### Create and import data

```sh
drawercheck demo-data
drawercheck import --dir data/demo --db demo.db
```

`demo-data` writes 30 days starting on 2026-09-01, for two registers, using
seed 42. It replaces the seven demo CSV files in `data/demo` and leaves other
files alone. For a separate dataset, choose another folder and database:

```sh
drawercheck demo-data --out data/another-demo --days 7 --seed 17
drawercheck import --dir data/another-demo --db another-demo.db
```

Importing the same files again prints `already imported; skipped` and adds
nothing. The [demo scenarios](docs/DEMO_SCENARIOS.md) list the deliberately
planted problems and the 18 leads they produce. If you leave out `--db`, the
database is `./drawercheck.db`.

### Run the checks and explain one shift

```sh
drawercheck reconcile --db demo.db
drawercheck explain 2026-09-03-R1 --db demo.db
```

This example shift expected $518.75, counted $498.75, and is $20.00 short. It
gets a cash-difference lead and a single-bill hint. It has a verifier and a
note, so there is no missing sign-off lead.

- `reconcile` accepts `--from`, `--to`, `--db`, and `--config`. Running it again
  replaces earlier results for those dates.
- `config.toml` holds the example settings. If the file is missing, built-in
  defaults are used and a notice says so. Changing settings, or importing new
  records, clears earlier results so different settings are never mixed.
- `explain` uses the settings saved when the checks ran, and also shows that
  day's bank-deposit leads.
- After upgrading from an older version, run `drawercheck reconcile` once without
  dates to refresh saved results.

### Export reports

```sh
drawercheck report --db demo.db
drawercheck report --db demo.db --date 2026-09-03
drawercheck report --db demo.db --format csv --out flags.csv
drawercheck report --db demo.db --format html --out review.html
```

Text on the terminal is the default. Reports never rerun the checks; every
date you ask for must already be checked, or the error names the first
unchecked date. `--date` cannot be combined with `--from` or `--to`.

Real output from the demo, shortened:

```text
DAILY SUMMARY
Date       | Shifts | Balanced | Over | Short | Incomplete | Open | Info | Warn | Review | Expected deposit
-----------+--------+----------+------+-------+------------+------+------+------+--------+-----------------
2026-09-01 | 2      | 2        | 0    | 0     | 0          | 0    | 0    | 0    | 0      | $2,100.61
2026-09-02 | 2      | 2        | 0    | 0     | 0          | 0    | 0    | 0    | 0      | $2,489.98
2026-09-03 | 2      | 1        | 0    | 1     | 0          | 0    | 1    | 0    | 1      | $2,698.27

REVIEW FLAGS
[review] 2026-09-03 2026-09-03-R1 R01_VARIANCE: Short by $20.00. Recount recommended.
[info] 2026-09-03 2026-09-03-R1 R02_SINGLE_DENOMINATION: Variance equals one $20 bill. Check for a miscounted or misplaced bill.
```

All formats share the same data:

- **Text and web page:** a daily summary, every review lead, totals by
  cashier, and each shift's amounts. Days with only bank entries show
  `Not calculated (no shifts)` for expected cash.
- **Web page:** a single offline file with light and dark modes, print
  styling, and tables that scroll on narrow screens.
- **Spreadsheet (CSV):** one row per lead. Every cell is protected so a
  spreadsheet cannot run it as a formula.

Report files are replaced safely: if writing fails, the previous file is kept.
A report can never overwrite the database.

## Preparing your own CSV files

DrawerCheck needs seven files with the exact column names in the
[input contract](docs/PROJECT_BRIEF.md#5-csv-input-contract-and-import-rules-folder-datademo):
`cashiers.csv`, `registers.csv`, `shifts.csv`, `pos_totals.csv`,
`safe_drops.csv`, `cash_counts.csv`, and `bank_deposits.csv`.

- Money uses exactly two decimal places, such as `1250.75`.
- Cash counts use one row per bill or coin value, with a whole-number quantity.
- Column order can vary. Missing, extra, or repeated column names are errors.
- Files saved from Excel as UTF-8 work, including quoted commas, quoted line
  breaks, and Windows line endings.
- IDs and shift codes cannot start or end with spaces. Invisible control
  characters are rejected so text cannot disguise the output.
- Each error names the file, line, column, and problem. A failed import changes
  nothing, because all seven files are saved together or not at all.
- Records already in the database cannot be overwritten. Import only new
  records, or use a fresh database.

The [troubleshooting guide](docs/TROUBLESHOOTING.md) explains ten common error
messages, with checks and fixes.

## Web request layer (for developers)

The public site has four views: Start with the example
button, Prepare files for uploads, Results with filters and report downloads,
and Drawer details. Back, Forward, and copied links work, and results are kept
only while the page is open. M10 checks cover keyboard access, narrow layouts,
200% text, and automated accessibility in Chrome and WebKit. The 320 x 200
reflow test is distinct from actual browser zoom, which remains unverified.
See the [current checklist](docs/M10_CHECKLIST.md) for evidence and limits.
The public demo is deployed from the [Render Blueprint](render.yaml) and live at
[https://drawercheck.onrender.com](https://drawercheck.onrender.com).
The block 6 repair uses two single-threaded sync workers with a 30-second
processing watchdog. User-provided deployment logs show commit `332f01b`,
`Using worker: sync`, and two workers starting. The user reported the other
deployment checks passing on 2026-10-26. See the
[repair notes](docs/M8_BLOCK6_REPAIR.md#public-deployment-confirmation-2026-10-26).
Install the optional packages and run the web tests:

```sh
pip install -e ".[dev,web]"
pytest -q tests/test_web.py tests/test_web_page.py tests/test_web_server.py
```

To look at the page on your own computer, run
`flask --app drawercheck.web:create_app run` and open the address it prints.

Flask handles web requests using the same Python code as the command line.
Gunicorn runs the app on Linux and macOS hosts, and is not installed on Windows.
The app is created by `drawercheck.web:create_app()`.

| Request | Sends | Returns |
| --- | --- | --- |
| `GET /` | Nothing | The website page, with its local styles and fonts |
| `POST /api/demo` | Nothing | Full results for the built-in example |
| `POST /api/check` | The seven CSV files | Full results for those files |
| `GET /examples/<file>` | Nothing | One of the seven example CSVs, to download |

Results come back as one JSON response containing summaries, shift
explanations, review leads, and all three reports. Money is already formatted,
and Python also sends the count-sheet line totals, the results summary counts,
and the plain words for each code, so the browser never does cash arithmetic. Each request uses its own temporary
database, which is deleted before the response is sent. Nothing is saved on the
server.

Limits keep the public demo responsive. They apply only to the website, not the
command line:

| Limit | Value |
| --- | --- |
| Whole upload | 2 MiB |
| Registers / people | 5 / 100 |
| Shifts and sales-total rows | 1,000 |
| Cash-count rows | 12,000 |
| Bank deposits / safe drops | 2,000 each |
| Characters per value | 256 |
| Whole response | 10 MB |

Uploads over a limit get a short, plain error explaining what to change. The
built-in example uses 2 registers, 5 people, and 60 shifts. See the
[request details](docs/WEB_PLAN.md#m7-request-contract-and-handoff) for the
full contract.

## Project setup for development

```sh
git clone https://github.com/GutsJr75/DrawerCheck.git
cd DrawerCheck
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
ruff check . && ruff format --check .
drawercheck --help
```

- Use Python 3.12 or newer (3.13 or 3.14 recommended). If your system calls it
  `python3`, use that name in the `venv` command.
- Python must include SQLite 3.37.0 or newer. DrawerCheck checks this and
  explains how to fix an older version.
- The `[dev]` extra adds the test runner (pytest) and code checker (Ruff). The
  command-line tool itself needs nothing beyond Python and makes no network
  calls.
- Running `drawercheck` with no arguments prints help. Invalid input prints a
  short message, never a Python traceback, and exits with code 1.

Design choices worth knowing:

- Money is stored and calculated as whole cents, never as decimals that can
  round. For example, `parse_dollars("0.10")` returns `10`, and
  `format_cents(125075)` returns `"$1,250.75"`.
- Each run of checks uses the whole imported history before filtering by date,
  so asking for one day gives the same leads as checking the whole month.
- A date with no leads is marked as checked, so "no problems found" can be told
  apart from "never checked".

Libraries and tools, in plain language:

| Tool | Why it is here |
| --- | --- |
| Python standard library and SQLite | Read CSVs, check exact amounts, and save the command-line records in a local database; the core needs no extra runtime packages. |
| Flask and its Jinja templates | Receive uploads and serve the website using the same Python calculations as the command line. |
| Gunicorn | Run Flask on the public host with separate workers that can be replaced if stalled. |
| Bundled JavaScript | Change views, choose files, filter results, and download reports; it does not calculate cash amounts. |
| pytest and Ruff | Run automated checks and check Python code style and formatting. |
| setuptools | Package the Python code and website assets for installation. |

## Limitations

- **Learning project with fake data.** This is not a tool for real cash
  control, and it is not accounting or legal advice. The project claims no
  banking, compliance, or accounting expertise.
- **Example thresholds.** The settings are examples, not industry standards.
- **Temporary public runs.** The website has no accounts or saved run history.
  Request workspaces are normally removed before the response is sent; a forced
  process kill cannot guarantee Python cleanup runs. The free host can sleep,
  and the worker watchdog is not an exact deadline measured from your click.
  Uptime, traffic capacity, and Render peak memory have not been established.
- **One closing shift per register per day.** Every register listed in
  `registers.csv` is expected on every date that has shifts. There is no store
  calendar, so a day missing from the shift files cannot be detected.
- **Simple bank matching.** Exact matches are reserved first for every day;
  remaining days are then compared with the entries left over, in date order.
  Equal amounts and overlapping date windows can still pick the wrong day. For
  example, if September 1 and 2 each expect $100.00 and the only $100.00 entry
  is dated September 2, September 1 takes it, even if its reference names
  September 2. September 2 is then flagged as missing.
- **Not handled:** one deposit covering several days, several deposits added
  together, weekends and holidays (only a calendar-day window is used), and
  real POS or bank connections. A missing-deposit lead describes the imported
  files, not a real overdue payment.

## More documentation

- [Current redesign verification and open checks](docs/M10_CHECKLIST.md)

- [How it works](docs/HOW_IT_WORKS.md): formulas, a worked example, and every rule.
- [Troubleshooting](docs/TROUBLESHOOTING.md): ten exact error messages, with checks and fixes.
- [Demo scenarios](docs/DEMO_SCENARIOS.md): the planted problems and their expected leads.
- [Core checklist](docs/CORE_CHECKLIST.md): what was verified, and how.
- [M8 delivery checklist](docs/M8_CHECKLIST.md): website evidence and remaining manual checks.
- [Interview notes](docs/INTERVIEW_NOTES.md): pitches, honest answers, and resume options.
- [Milestone plan](docs/PLAN.md) and [website plan](docs/WEB_PLAN.md): scope and decisions.
- [Learning log](docs/LEARNING_LOG.md): what was built and checked at each step.
- [Screenshot timeline](docs/screenshots/README.md): dated pictures of the website as each block was built.
- [Original project brief](docs/PROJECT_BRIEF.md): the starting requirements.
  Its website and hosting exclusions were later replaced by the approved
  website plan.

## Further reading

These are background sources, not standards this project implements or is
certified against. The [plan](docs/PLAN.md#reference-review) notes any access
problems and replacements.

- [WCPOS reconciliation reports](https://docs.wcpos.com/reports/reconciliation): expected drawer amounts.
- [Shopify cash-drawer balancing](https://www.shopify.com/blog/balancing-a-cash-drawer): closing practices.
- [Beancount end-of-day close guide](https://beancount.io/blog/2026/09/14/end-of-day-close-z-reports-cash-drawer-daily-sales-reconciliation-guide): background on separate close records.
- [Beancount daily cash and deposit guide](https://beancount.io/blog/2026/10/12/daily-sales-reconciliation-cash-heavy-business-pos-till-bank-deposit-guide): background on the deposit handoff.
- [Manifestly cash-handling checklist](https://app.manifest.ly/public/checklists/cash-handling-checklist): examples of review steps.
- [HotSchedules mobile cash reconciliation](https://help.hotschedules.com/hc/en-us/articles/28816788225293-MacromatiX-Mobile-Cash-Reconciliation): the official replacement reviewed when the original supplied link could not be retrieved.
- [AccountingTools cash over and short](https://www.accountingtools.com/articles/what-is-the-cash-over-and-short-account.html): terminology background.
