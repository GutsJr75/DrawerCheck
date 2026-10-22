# How DrawerCheck works

DrawerCheck is a personal learning project for **Demo Store #001**, using only
fictional records. M3 compares expected closing cash with an independent cash
count and saves neutral leads for review. Reports arrive in M4. Repeated-shortage
checks and bank-deposit matching arrive in M5.

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

## M3 rules

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

**R09_DATA_INTEGRITY:** Review flags identify a closed shift without count rows
or POS totals, a closing time not after opening, overlapping register shifts,
negative expected cash, or multiple closing shifts on one register/day. Each
issue has separate evidence. Adjacent shifts do not overlap. An open shift can
overlap a later shift because its ending time is unknown. An invalid closed
interval receives its own timestamp flag and is excluded from overlap checks.
The daily check also flags any expected register with no shift on that date.
That flag belongs to the date, with no invented shift or cashier.

The thresholds are configurable example policies, not industry standards.
R03, R06, and R07 are optional and remain unimplemented. R04 and R08 are M5 work.

## Missing records and open shifts

No count rows means counted cash and variance are unknown. Count rows with zero
quantities mean a real count of zero. Missing POS totals mean expected cash and
variance are unknown. Rules that need a variance do not run on an unknown value.
An invalid closing-time order does not erase otherwise available cash amounts.

An open shift has status `open` and no closing arithmetic. It does not receive a
missing-closing-count or missing-POS flag merely because it is still open.
Other integrity checks, such as overlapping register use, still apply.

## Expected deposits, before bank matching

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

The helper calculates expected amounts only. It does not yet compare them with
bank entries. M5 adds simplified matching over calendar-day windows. Combined
deposits, weekends, holidays, and ownership of equal-amount deposits will remain
limitations of that simplified model.
The M5 date-window calculation must also handle dates near the end of the
supported calendar; a small lag alone does not prevent date overflow.

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

The `reconciled_dates` table records each selected date containing shifts,
the effective settings, and a completion time. This makes a checked day with
zero flags distinguishable from an unchecked day. An empty date selection
reports `No shifts match the requested date range.` without changing saved
results. Only explicitly reversed endpoints receive the reversed-range error.
Missing date endpoints
come from the earliest/latest imported shift dates, never today's date.

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
Snapshots now include review-policy version 2. Earlier M3 results need a fresh
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
database text also pass through this protection. M4's text output must reuse
the helper; HTML escaping and CSV formula protection remain separate checks.

## Try the new commands

After installation, use a separate database for this fake-data example:

```sh
drawercheck import --dir data/demo --db demo-m3.db
drawercheck reconcile --db demo-m3.db
drawercheck explain 2026-09-03-R1 --db demo-m3.db
```

Use `--from 2026-09-01 --to 2026-09-03` to select an inclusive range on
`reconcile`, or `--config path/to/policy.toml` to choose settings. `explain`
requires that the shift's business date has already been reconciled. The full
default demo currently produces 12 M3 flags. See [demo scenarios](DEMO_SCENARIOS.md)
for the exact current and future expectations.
