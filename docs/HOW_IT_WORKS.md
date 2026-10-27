# How DrawerCheck works

DrawerCheck is a personal learning project for **Demo Store #001**, using only
fictional records. It compares expected closing cash with an independent cash
count and saves neutral leads for review. Reports are available as text, HTML,
and CSV. M5 adds repeated-shortage checks and simplified bank-deposit matching.

Reconciliation means comparing independently recorded amounts and checking the
differences. For setup, see the [README](../README.md); for exact error messages
and fixes, see [troubleshooting](TROUBLESHOOTING.md). The
[core checklist](CORE_CHECKLIST.md) records what was actually verified.

## Follow the cash

The opening float is the cash left in a register to make change. POS totals are
the sales system's records. Paid-ins add cash outside sales; refunds and paid-outs
remove it. A safe drop moves cash from the drawer to the safe during a shift.
Card sales are stored but do not put physical cash in the drawer.

The importer stores POS totals and count sheets separately. Reconciliation then
reads them, calculates the difference, applies the rules, and saves any flags.
Money is calculated as whole cents so decimal rounding cannot change a result.

```text
Expected drawer = opening float + cash sales + paid-ins
                  - cash refunds - paid-outs - safe drops
Counted drawer  = sum of denomination x quantity
Variance        = counted drawer - expected drawer
```

A negative variance is short; a positive variance is over. A zero variance is
exactly balanced. With the default tolerance, an absolute difference of up to
$1.00 is classified as balanced within tolerance. The exact difference remains
available: -$0.75 stays -75 cents, rather than being replaced with zero.

Blind counting means counting before looking at the expected total. That is a
human practice. Separate input records support the comparison, but code cannot
prove when someone looked at the expected number.

## Worked example: September 3, register R1

| Item | Amount |
| --- | ---: |
| Opening float | $200.00 |
| Cash sales | $1,250.75 |
| Paid-ins | $0.00 |
| Cash refunds | $12.00 |
| Paid-outs | $20.00 |
| Safe drops | $900.00 |
| Expected drawer | $518.75 |
| Counted drawer | $498.75 |
| Variance | -$20.00 |

The exact arithmetic is `20000 + 125075 + 0 - 1200 - 2000 - 90000 = 51875`
cents. The independent count gives `49875 - 51875 = -2000` cents.

R01 requests review of the $20.00 difference. R02 suggests checking for a single
$20 bill. R05 does not appear because both a verifier and a note are present.
These are review leads, not findings about a person.

## Required rules

**R01_VARIANCE:** No variance flag is generated within tolerance. Above tolerance
but below the warning amount, the flag is info. At the warning amount it becomes
warn, and at the review threshold it becomes review. The review threshold is
`max(warn_cents, min(review_cents, percentage_cents))`. The percentage is loaded
exactly, converted to a fraction, and multiplied using integers. Fractional cents
are rounded down. For $1,250.75 in cash sales, 1 percent becomes 1,250 cents, or
$12.50. At zero sales, the warning floor remains in effect.

**R02_SINGLE_DENOMINATION:** An info flag suggests checking a single bill when
the absolute difference is exactly $1, $5, $10, $20, $50, or $100. This rule is
independent of R01: an exact $1 difference is within the default tolerance and
can still receive the bill hint. It does not identify the actual cause.

**R05_MISSING_VERIFIER_OR_NOTE:** A difference of at least the configured amount,
default $20.00 in either direction, requires both a verifier and a nonblank note.
Missing either produces a review flag describing what is absent. A smaller
difference does not trigger this rule merely because those fields are blank.

**R04_REPEAT_SHORT:** With the defaults, a warn lead appears when at least three
of a cashier's last ten shifts were short by $5.00 or more. Include the current
shift, order by business date, opening time, and shift code, and exclude later
shifts. Use the actual window size if fewer shifts exist. Unknown/open shifts
occupy places in the window but do not count as shortages. A later balanced,
over, or unknown shift can still show the lead because its recent history
qualifies. Evidence lists the window's shift codes and each qualifying shortage.
This is a request to check counts and records, not a conclusion about a person.

**R09_DATA_INTEGRITY:** Review flags identify a closed shift without count rows
or POS totals, a closing time not after opening, overlapping register shifts,
negative expected cash, or multiple closing shifts on one register/day. Each
issue has separate evidence. Adjacent shifts do not overlap. An open shift can
overlap a later shift because its ending time is unknown. An invalid closed
interval receives its own timestamp flag and is excluded from overlap checks.
The daily check also flags any expected register with no shift on that date.
That flag belongs to the date, with no invented shift or cashier.

The thresholds are configurable example policies, not industry standards.
**R03_TRANSPOSITION_HINT (M9 block 1):** An info-level hint appears when the
known difference, in either direction, is a whole-dollar amount of at least
$9 and divisible by 9. For example, typing $52 instead of $25 creates a $27
difference. This is a heuristic: a rough clue that can also match unrelated
differences, not proof that a typo occurred or a reconstruction of the original
amount. Fractional dollars, amounts below $9, and unknown differences do not
qualify. The rule uses exact integer cents and adds no new calculation in the
browser. R06 and R07 remain unimplemented. R08 is described below.

## Missing records and open shifts

No count rows means counted cash and variance are unknown. Count rows with zero
quantities mean a real count of zero. Missing POS totals mean expected cash and
variance are unknown. Rules that need a variance do not run on an unknown value.
An invalid closing-time order does not erase otherwise available cash amounts.

An open shift has status `open` and no closing arithmetic. It does not receive a
missing-closing-count or missing-POS flag merely because it is still open.
Other integrity checks, such as overlapping register use, still apply.

## Expected deposits and bank matching

M3 calculates the cash expected to be prepared for deposit:

```text
Daily expected deposit = total counted drawers + total safe drops
                         - retained float per register x registers closed
```

For the worked shift, `49875 + 90000 - 20000 = 119875` cents, or $1,198.75.
This is that register's contribution. The daily total also includes R2.
Keeping money as integer cents applies to these sums and products too.

The supported model is one closing shift per register per business day. If a
day includes open shifts, unknown required amounts, or duplicate closing shifts,
its expected deposit is unknown. Drawer totals are not silently added twice.
An invalid timestamp alone preserves the available monetary calculation.

For this demo, `registers.csv` lists every register expected on each business
date present in the shift inputs. If R2 has no shift on a date, R1's amount
cannot stand in for the whole day: the deposit and displayed contribution are
unknown, with a date-level R09 review flag identifying R2. Real stores can have
inactive registers; that needs an operating schedule, which is outside this
demo. A date with no imported shifts at all is not inferred as a business day.

**R08_DEPOSIT:** Calculate expected amounts first, then compare them with all
imported bank entries using this simplified algorithm:

1. First reserve exact matches for all eligible business dates, in date order.
   Skip unknown, zero, and negative expected amounts. Search unmatched bank
   entries from each date through the configured lag, inclusive. Clamp the end
   to December 31, 9999 to avoid calendar overflow. Break exact-match ties by
   bank-entry date, then database ID. Consume the entry once, with no flag.
2. Then process unresolved business dates in order. Search the same windows
   using only entries left after the entire exact-match pass.
3. With exactly one remaining candidate, consume it and flag the signed
   difference, recorded minus expected. Use review at or above `review_cents`
   in absolute value, otherwise warn. Sales percentages do not set this threshold.
   Messages say how much less or more was recorded; evidence retains the signed
   difference for inspection.
4. With no candidates, produce a review flag for a missing deposit in the
   imported records. This does not claim a real-world deadline has passed.
5. With multiple nonmatching candidates, produce a review flag for an ambiguous
   match and leave them available. Do not combine amounts or guess a candidate.
6. Remaining entries produce info flags on their bank-entry dates, including
   dates with no shifts. An incomplete day's bank entry can remain unexpected
   because the program cannot establish a matching expected amount.

Matching always uses the full imported history before selecting flags to save
for a date range. This prevents a filtered run from reusing an entry consumed
by an earlier day. References are retained as evidence for unexpected entries;
they are not interpreted as authoritative matching instructions.

This two-pass policy was approved on 2026-10-22 and supersedes the original
brief's per-date matching order. For example, September 2 expects $2,489.98 in
the fake demo. Changing its recorded deposit to $2,489.99 now produces one
$0.01 mismatch warning after later days reserve their own exact entries. Under
the original policy, that early day's window held four nonmatching entries,
producing an ambiguous review plus an unexpected-entry note. The new policy
still uses greedy choices within each pass and cannot prove deposit ownership.
The second pass does not revisit an earlier ambiguous day after processing later
unresolved days.

### A concrete greedy-matching limitation

Suppose September 1 and 2 each expect $100.00. There is only one $100.00 bank
entry dated September 2, whose reference says it belongs to September 2. With
a three-day lag, the algorithm gives it to September 1 first and flags
September 2 as missing. A person may know the reference means September 1 was
actually the missing day. The program does not establish that ownership.

Overlapping windows can similarly pair a unique mismatch with the wrong day.
One deposit covering two days is not handled, and multiple smaller deposits
are not added together. Weekends and holidays use calendar-day lag only. Real
bank reconciliation requires more context than this demo provides.

## Settings and repeatable runs

`config.toml` contains all supplied defaults. A partial config overrides just
the settings present; unknown sections/keys, wrong types, negative settings,
invalid threshold ordering, and invalid history windows are errors. A missing
file uses defaults with one informational notice. An unreadable or malformed
existing file does not silently fall back.
Percentages must be greater than 0 and at most 100, with at most six decimal
places after removing redundant trailing zeros. The stored Decimal is reduced
before any fixed-point formatting or fraction conversion, so enormous exponents
cannot inflate settings snapshots or calculations. Deposit lag is a whole
number from 0 through 31 days. Numeric parsing failures use the shared config
error. These limits are project choices, not industry standards.

The `reconciled_dates` table records each selected date containing shifts or bank entries,
the effective settings, and a completion time. This makes a checked day with
zero flags distinguishable from an unchecked day. An empty date selection
reports `No shifts match the requested date range.` without changing saved
results. Only explicitly reversed endpoints receive the reversed-range error.
Missing date endpoints
come from the earliest/latest imported shift or bank-entry dates, never today's
date. Bank-only dates can be checked and reported with zero shifts and an
unavailable expected amount labelled `Not calculated (no shifts)`. Incomplete
closing days still show `unknown`; a counted zero still displays as $0.00.
Bank-only dates do not create inferred business days or missing-register
flags, and they are not counted as incomplete closing days in the HTML summary.

Flags and markers for the inclusive selected range are replaced in one
transaction. A failure restores the previous run. Repeating the same inputs and
settings gives the same calculations and flag content without duplicates.
Overlap checks include imported shifts outside the selected date range.

A run with different settings clears earlier results before saving its range,
so results cannot silently mix policies. New imported records also clear all
saved results; identical skipped imports preserve them. `explain` uses the saved
settings and flags, rather than rereading a possibly changed config file. It
recalculates the displayed amounts from the imported records under those saved
settings. Existing M2 databases gain the completion table on successful
reconciliation, without changing imported data.
Snapshots now include review-policy version 4. Earlier M3/M4 and initial M5 results need a fresh
`reconcile` before `explain` can use them. The next successful reconciliation
clears old-policy results even if the numeric settings are unchanged. Run it
without date filters after updating to refresh the full imported history.

## Safe text and identifiers

ID and shift-code columns reject surrounding whitespace, tabs, and line breaks
in both defining rows and references. Values are rejected rather than trimmed,
so the importer never silently merges different records. Ordinary spaces within
free text and quoted multiline names or notes remain valid.

Text fields reject terminal controls, including escape codes, and invisible
formatting or line-separator characters. Free-text LF, CR, and tab characters
are kept in the database. The shared `terminal_text` helper renders them as
visible `\n`, `\r`, and `\t` escapes on one output line. CLI errors and existing
database text also pass through this protection. Text reports reuse the helper;
HTML escaping and CSV formula protection remain separate checks.

## Try the new commands

After installation, use a separate database for this fake-data example:

```sh
drawercheck import --dir data/demo --db demo-m3.db
drawercheck reconcile --db demo-m3.db
drawercheck explain 2026-09-03-R1 --db demo-m3.db
```

Use `--from 2026-09-01 --to 2026-09-03` to select an inclusive range on
`reconcile`, or `--config path/to/policy.toml` to choose settings. `explain`
requires that the shift's business date has already been reconciled.
Its output places any saved R08 leads under `Daily deposit review for YYYY-MM-DD`
beside the daily expected deposit, including severity, message, and
evidence. These leads apply to the whole date, not just the selected register.
Other daily record leads remain separate, and no deposit flag is printed twice.
The full default demo produces 18 flags, including two R03 hints. See [demo scenarios](DEMO_SCENARIOS.md)
for the complete verified expectations.

## Reports from saved results

`report` reads the imported records and the completed dates' saved settings and
flags in one database transaction. It reuses the closing/deposit calculation
helpers without running reconciliation or changing results. A range containing
an unchecked date is refused; zero flags on a completed date remain a valid
result. Old policy versions and mixed saved settings are also refused.

Text and HTML share daily status/severity counts, all saved flags, cashier
over/short totals, and the exact per-shift amounts. Cashier money totals include
every known signed difference, including differences within tolerance. Open
and incomplete shifts are counted separately and excluded from those totals.
A cashier with no known variance shows unknown totals. Daily deposit amounts
remain unknown when the expected-register roster is incomplete.

HTML escapes every dynamic value, contains inline CSS and no JavaScript or
external assets, and labels severity in words. CSV exports only the saved flag
rows, with date, shift code, rule, severity, and message. `sanitize_cell` protects
every header and data cell starting with `=`, `+`, `-`, `@`, tab, or carriage
return by prefixing one quote. The CSV module preserves commas and multiline
cells. Text rendering uses `terminal_text` to make embedded controls visible.

`--date` selects one business date and cannot combine with range arguments.
Missing range endpoints come from imported dates; empty selections do not
produce a report. `--out` writes the selected format atomically to an existing
folder. A failed write preserves the previous report and cleans temporary
output. Database paths, aliases, and SQLite sidecars are protected from being
used as the output file. By default the selected format goes to stdout.

Reports include R04 and R08 leads alongside the original rules. Daily expected
deposits remain calculated amounts; the bank flags describe matching exceptions.
The report notice explains that matching reserves all exact matches first,
uses calendar-day windows, and does not combine entries. Reports load saved
flags without rerunning matching.
