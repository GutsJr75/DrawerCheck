# M11 block 3: Input and check contract

Drafted 2026-11-04 under the user's "next" after block 2. This is a contract
for blocks 4 to 8. It adds no application code. **It needs the user's review
before block 4 starts.** Revised the same day after the user's review: the
budget is decided (see the end of this file), and four points were clarified.
The user's reviewer confirmed it ready for block 4 the same day; block 4
implements the parts listed in its row below.
The cases in [M11_BLOCK1.md](M11_BLOCK1.md) are the worked examples.

## Summary of decisions

| Question | Decision |
| --- | --- |
| Closed state without invented times | Ask for the real opening and closing times from the shift slip (the register report header repeats them). No placeholder time is ever filled in. Without the times, this version cannot check the drawer and says so. |
| Rule selection | Run R01, R02, R03, R05, and R09 by name. Report R04 and R08 as "not run". Coverage never comes from "no lead was found". |
| What can be unknown | Only the whole register report can be unknown and still be checked. Missing times or a missing drop log can be marked, but this version then cannot check the drawer and says why. Starting cash and the count are required. |
| A partly printed report | Not supported. If the report is available, all four lines are required (0.00 allowed). Otherwise mark the whole report "not available". |
| Blank versus 0 on the count | Every line needs a number. A blank line is an error, never 0. All zeros is a confirmed empty drawer. |
| Safe drops | A list of individual drops, an explicit "no safe drops", or "drop log not available", which this version cannot check. Python adds them up. |
| Starting cash | Its own required field, separate from the register report. |
| Recount | One optional full second count. The first count is kept; checks use the recount. |
| Page names | "Close a drawer" and "Review a drawer". |
| Fictional-data notice | Shown on Close a drawer itself, above the form. |
| Card sales, voids, no-sale count | Not collected. They are stored as unknown; no calculation reads them. |
| Server storage | None. The check runs in memory; no temporary database or files. |
| Wording for missing report | Keep the core's "Missing POS totals" message for now, with a plain definition beside it. Revisit after participant testing. |

## Fields

Every money amount and count quantity is a JSON string, never a JSON number,
so money never passes through a float. Dates, times, IDs, and text are strings
too. Objects, lists, and `null` keep their normal JSON types. Every key below
is required; unknown or repeated keys are rejected. Labels are what the page
shows.

**Where each figure comes from.** The packet in
[M11_PARTICIPANT_PACKET.md](M11_PARTICIPANT_PACKET.md) has a shift slip for
every drawer, even when the register report is missing. The shift slip gives
the opening and closing times and the starting cash; the register report gives
the four cash figures; the drop log gives the drops; the count sheet gives the
count.

### Drawer

| Key | Label | Meaning | Rule |
| --- | --- | --- | --- |
| `business_date` | Business date | The day this drawer's sales belong to | Required real date, `YYYY-MM-DD` |
| `register_id` | Register | The register's ID, as on the report | Required ID (see Text rules) |
| `cashier_id` | Cashier ID | The ID on the report, not a name | Required ID |
| `opened_at` | Opened | When the drawer was opened, from the shift slip | Required local time, `YYYY-MM-DDTHH:MM`. `null` means not available (see below). |
| `closed_at` | Closed | When the drawer was closed, from the shift slip | Required local time, `YYYY-MM-DDTHH:MM`. May be on a later date. `null` means not available. |
| `opening_float` | Starting cash | Cash put in the drawer at opening, from the shift slip | Required money, 0.00 or more |

Times arrive with minute precision, which is what the slip prints, and are
stored with `:00` seconds. The page offers "Times not available". It sends
`null`, and the server answers with a field message: this version cannot
check a drawer without its opening and closing times, so find the shift slip
or the register report. Nobody is asked to guess a time. A closing time that is not after the opening time
is accepted and produces the existing R09 lead, as the CSV path does. Python
builds the drawer code shown on screen as `<business_date>-<register_id>`.

### Count

| Key | Meaning | Rule |
| --- | --- | --- |
| `counts` | The closing count | Object with exactly the 12 keys `100.00`, `50.00`, `20.00`, `10.00`, `5.00`, `2.00`, `1.00`, `0.50`, `0.25`, `0.10`, `0.05`, `0.01`. Each value is a whole number from 0 to 99,999. |
| `recount` | A second full count, or none | `null`, or an object with the same 12 keys and rules |

There is no "not counted" choice in M11, because counting is the page's main
task. The not-counted R09 check therefore never applies in this path. The
page shows no running total while typing: totals are cash arithmetic, so they
appear only after Python checks the drawer.

### Register report

| Key | Label | Meaning | Rule |
| --- | --- | --- | --- |
| `register_report` | Register report | The report's figures, or not available | `null` means not available. Otherwise an object with the four keys below. |
| `cash_sales` | Cash sales | The report's cash sales total, **before** refunds | Required money, 0.00 or more |
| `cash_refunds` | Cash refunds | Cash given back for returns, entered separately | Required money, 0.00 or more |
| `paid_ins` | Paid in | Cash added that did not come from a sale | Required money, 0.00 or more |
| `paid_outs` | Paid out | Cash taken out to pay for something. **Safe drops never go here.** | Required money, 0.00 or more |

The server cannot tell whether someone netted refunds out of cash sales, or
typed a drop into paid out. The labels and help text carry those two rules,
and participant testing checks whether they work.

### Safe drops

| Key | Meaning | Rule |
| --- | --- | --- |
| `safe_drops` | Cash moved to the safe during the shift | A list of 0 to 20 drops. An empty list means "no safe drops occurred". `null` means "drop log not available". |
| `amount` | One drop | Required money, more than 0.00 |
| `bag_number` | The drop's bag, if recorded | Optional text; empty means not recorded |

Drop times are not collected, because no rule reads them. The page offers
three separate choices: list the drops, "No safe drops this shift", and "Drop
log not available". The last two must never look alike. M11 cannot calculate
with an unknown drop log, because the core stores drops as a known total, so
`null` gets a field message: this version cannot check a drawer without its
drop log; find the log, and choose "No safe drops" only if none were made.
This limitation is accepted for M11.

### Sign-off

| Key | Label | Meaning | Rule |
| --- | --- | --- | --- |
| `verifier_id` | Verifier ID (not checked) | Who confirmed the count | Optional ID; empty means not supplied |
| `variance_note` | Note | What was checked, in factual words | Optional text; empty means not supplied |

A supplied verifier ID is typed text. It is not a login, a signature, or a
check that the person exists. The page says so beside the field.

### Text and money rules

These reuse the CSV importer's rules so both paths agree:

- **Money:** exactly two decimal places, digits only, such as `1316.40`. No
  `$`, commas, or signs. Parsed by `parse_dollars`. Each field and each drop
  is at most 999,999.99, a new limit for this path only.
- **IDs:** no leading or trailing spaces, tabs, or line breaks, and no hidden
  control characters. At most 256 characters, the existing per-value limit.
- **Note and bag number:** no hidden control characters; line breaks are
  allowed in the note. At most 256 characters.
- **Whole numbers:** digits only, no sign or decimal point.

## Request and response

`POST /api/drawer` with `Content-Type: application/json`, a body of at most
32 KiB, and no URL options. Each request is checked from scratch; the server
keeps nothing between requests and never logs submitted values.

```json
{
  "business_date": "2026-11-02",
  "register_id": "R2",
  "cashier_id": "cashier_02",
  "opened_at": "2026-11-02T08:00",
  "closed_at": "2026-11-02T20:00",
  "opening_float": "200.00",
  "counts": {"100.00": "1", "50.00": "3", "20.00": "12", "10.00": "6",
             "5.00": "9", "2.00": "0", "1.00": "47", "0.50": "0",
             "0.25": "72", "0.10": "35", "0.05": "31", "0.01": "60"},
  "recount": null,
  "register_report": {"cash_sales": "1316.40", "cash_refunds": "18.25",
                      "paid_ins": "20.00", "paid_outs": "32.50"},
  "safe_drops": [{"amount": "400.00", "bag_number": "DEMO-BAG-1102-R2-A"},
                 {"amount": "400.00", "bag_number": "DEMO-BAG-1102-R2-B"}],
  "verifier_id": "",
  "variance_note": ""
}
```

A successful response (200) contains:

| Key | Contents |
| --- | --- |
| `notice` | The existing demo notice |
| `labels` | The existing rule, severity, status, and date labels |
| `drawer` | The same shape as one entry of `shifts` in the CSV response: expected, counted, and difference amounts, status, tape values, count lines with Python's line totals, leads with `limit_text`, tolerance, and review threshold. It has **no** deposit fields. It adds `count_basis`: `"first_count"` without a recount, `"recount"` with one. All leads and coverage use this count. |
| `initial_count` | `null` without a recount. With one: the first count's lines and line totals, counted amount, difference, and status, all from Python, labelled `"basis": "first_count, compared with the same expected cash"`. No leads are run on the first count. |
| `safe_drops` | Each drop's amount and bag number, plus Python's total |
| `coverage` | One entry per rule, described below |
| `closing_summary` | `filename`, `media_type`, and `content` of the closing sheet |

Money is already formatted, as in the CSV response. The browser does no cash
arithmetic.

A rejected request (400) returns every field problem at once, so the page can
list them and move focus to the first:

```json
{"error": {"message": "Some entries need fixing. Each one is listed below.",
           "fields": [{"field": "counts.20.00",
                       "message": "Enter how many $20 bills were counted. Write 0 if none."}]}}
```

Field names use dots for nesting (`register_report.cash_sales`,
`safe_drops.1.amount`, counting drops from 1). Every message lives in
`errors.py`. Wrong content type, a body over 32 KiB, malformed JSON, and
unknown or missing keys get one plain message without a field list.

## Check coverage

Block 4 calls the rules one by one. Coverage is decided from the inputs, not
from whether a lead appeared.

| Rule | When it runs | States |
| --- | --- | --- |
| R01 Cash difference | Difference known | Ran, no lead / ran, lead found / not run: difference unknown |
| R02 Single bill | Difference known | Same |
| R03 Possible swapped digits | Difference known | Same |
| R05 Missing sign-off | Difference known | Same. A clear result does not confirm who signed. |
| R09 Missing or inconsistent records | Always, partly | Ran, no lead / ran, lead found, with separate lists of what was checked and what was unavailable (below) |
| R04 Repeated shortages | Never | Not run: no earlier shifts are available |
| R08 Bank deposit | Never | Not run: one drawer is not a whole day with bank records |

Each entry has `rule_code`, `label`, `state` (`ran_no_lead`, `ran_lead`, or
`not_run`), `partial` (true only for R09), and a plain `detail` sentence.
R09 also has `checked` and `unavailable`, two lists of plain sentences that
Python fills from the actual inputs:

| R09 part | With a register report | Without one (case C) |
| --- | --- | --- |
| Register report present | Checked | Checked: lead found |
| Closing time after opening time | Checked | Checked |
| Expected cash not negative | Checked | Unavailable: expected cash is unknown |
| Other drawers on this register overlap | Unavailable: no other drawers | Same |
| A second closing for this register and day | Unavailable: no other drawers | Same |
| A register with no drawer that day | Unavailable: no register list | Same |

## Expected results for block 4 tests

From [M11_BLOCK1.md](M11_BLOCK1.md), confirmed with the CLI:

| Case | Expected | Counted | Difference | Status | Leads |
| --- | ---: | ---: | ---: | --- | --- |
| A, R1 | $520.86 | $520.61 | -$0.25 | balanced | none |
| B, R2 | $685.65 | $665.65 | -$20.00 | short | R01 review, R02 info, R05 review |
| B with `manager_01` and a note | $685.65 | $665.65 | -$20.00 | short | R01 review, R02 info |
| C, R3, report `null` | unknown | $437.80 | unknown | incomplete | R09 review (missing report) |

Block 4 must also show that the manual path and the CSV path give identical
results for these cases.

## What each block delivers

This file is the final M11 contract. Each block builds only its own part;
everything else stays unavailable until its block is approved and done.

| Block | Delivers | Until then |
| --- | --- | --- |
| 4 | `POST /api/drawer`: all validation and field errors, `notice`, `labels`, `drawer` with `count_basis: "first_count"`, `safe_drops`, `coverage`, verifier and note (so R05 can clear), the `PosTotals` change, and tests for cases A, B, B with sign-off, and C, including CSV-path parity | No page uses the request |
| 5 | Close a drawer page, the budget change below, and the performance baseline | Review shows nothing |
| 6 | Review a drawer page with sign-off fields and Check again | |
| 7 | Recount: a non-null `recount`, `initial_count`, and `count_basis: "recount"` | Block 4 requires `recount` to be `null`; anything else gets a plain "not available yet" message. `initial_count` is always `null`. |
| 8 | The closing sheet | `closing_summary` is `null` |
| 9 | End-to-end checks and the performance comparison | |

## Pages and handoff

- **Close a drawer** (`#/close`): the notice, then drawer details (with
  "Times not available"), the count, the register report (with "Not
  available"), safe drops (with "No safe drops this shift" and "Drop log not
  available" as separate choices), and **Check this drawer**. Expected cash is
  not shown on this page.
- **Review a drawer** (`#/review`): the result, coverage, sign-off fields,
  an optional recount, **Check again**, and the closing sheet download.
  Without a result it says there is nothing to review and links to Close a
  drawer.
- Both pages read the same in-memory entries. Going back keeps every entry.
- Any change to an entry discards the old result; the page asks for a new
  check rather than showing stale figures. Only the newest request's reply is
  used, as in the upload repair.
- Entries and results stay in the page's memory only: never browser storage,
  the address, analytics, or server logs. Refreshing loses them, and the page
  says so next to the download.
- One drawer at a time. Starting another drawer clears the entries after a
  confirmation.

## Closing sheet

A self-contained offline HTML file, built by Python with every value passed
through `html.escape`, with print styles. Filename:
`drawercheck-closing-<business_date>.html`; user text never goes in the name.

It contains: the fictional-data notice and generation time; date, register,
cashier ID, and times; starting cash; the report figures or "not available";
each safe drop and the total; the count lines (and the recount, labelled
"First count" and "Recount"); expected, counted, difference, and status;
every lead with its severity and limit; the coverage list; the verifier ID
and note marked "supplied, not verified"; and the example settings used.
Unknown and 0 stay distinct throughout. M11 adds no CSV export; any later CSV
must use `sanitize_cell`.

## Model changes needed in block 4

- `PosTotals.card_sales_cents`, `void_count`, and `no_sale_count` become
  `int | None`. The CSV importer still supplies numbers; the manual path
  supplies `None`. No calculation reads them.
- No change to `Shift`, the rules, the database, or the CSV path.

## CSS and JavaScript budget (decided 2026-11-04)

The site's CSS and JavaScript total **59,977 bytes** against the 60,000-byte
budget in DESIGN.md and `test_static_files_meet_the_performance_budget`. The
user chose **one combined budget of 90,000 bytes**, a project choice rather
than an outside standard, with these conditions:

- **Everything counts.** All application CSS and JavaScript count toward the
  limit, including any new files in any folder under `static/`. Block 5
  widens the test from the top folder to every subfolder.
- **A ceiling, not a target.** New pages reuse existing controls, styles,
  and helpers before adding new ones.
- **Measure, not just weigh.** Before block 5 changes any asset, record a
  local baseline in Chrome: CSS/JS bytes, page load timing, and the time
  from a click to visible results for **Try the example** and opening a
  drawer, as the median of five runs. Block 9 repeats the same measurements.
  A slowdown of more than 20% is investigated before release; the 20% figure
  is also a project choice. It is a trigger to look closer, not an automatic
  failure: repeat the measurements before calling it a regression.
- **Record the conditions with the numbers.** Each measurement records the
  Chrome version, the machine, network settings (throttling or none), cache
  state, whether the server was already running and warmed up, the exact
  start and end of each timing (for example, click until the results heading
  is visibly rendered), and all five timings plus the median in milliseconds.
  Block 9 uses the same conditions and reports milliseconds alongside the
  percentage change.
- **Split loading only if measured.** Separate files are not assumed to be
  faster. Splitting the loading is considered later only if the measurements
  show a benefit.

Block 5 updates DESIGN.md's performance budget and the test together. Block 4
is server-only and does not change the budget.
