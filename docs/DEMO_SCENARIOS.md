# Demo scenarios

These are deliberately constructed fictional records for **Demo Store #001**.
The default command is `drawercheck demo-data --days 30 --seed 42`.
The business dates are fixed at September 1 through September 30, 2026.

M9 block 1 checks the exact set of 18 flags: the original 12 core flags,
two repeated-shortage flags, two bank-deposit flags, and two R03 hints. The full pipeline test
compares every date, shift, rule, and severity below and rejects extra flags.
S9 also checks repeated imports after reconciliation, including saved results.

## Generated inputs

| File | Default data rows |
| --- | ---: |
| `cashiers.csv` | 5: cashier_01 through cashier_04, plus manager_01 |
| `registers.csv` | 2: R1 and R2 |
| `shifts.csv` | 60: one closing shift per register per business day |
| `pos_totals.csv` | 60 |
| `safe_drops.csv` | 60 |
| `cash_counts.csv` | 708: 12 denominations for each of 59 counted shifts |
| `bank_deposits.csv` | 28 |

The counts above were confirmed by generation and a full import during M2.
Every generated name, label, bag number, and deposit reference is fictional.
The generator uses its own `random.Random(seed)` and integer amounts. It does
not use today's date or change the application's global random state.

Counts are written to their own CSV and stored separately from POS totals.
The generator calculates inputs to create known differences for tests. This
does not prove that a human followed blind-count practice.

## Scenario inputs

- **S1:** `2026-09-03-R1`, cashier_02. Opening float $200.00, cash sales
  $1,250.75, cash refunds $12.00, paid-outs $20.00, paid-ins $0.00, and safe
  drops $900.00. Expected drawer $518.75; counted $498.75; short $20.00.
  Verifier manager_01 and a note are present, so R05 must not appear.
  This shift contributes $1,198.75 to the day's expected deposit; the day's
  bank entry also includes R2.
- **S2:** `2026-09-08-R2`, cashier_01. Short $45.00, with no verifier or note.
- **S3:** cashier_03 on R1 is short $6, $8, $7, and $9 on September 5, 9, 14,
  and 18. Their ten shifts through September 14 include the first three
  shortages. Their last ten through September 18 include all four. This cashier
  has no later demo shift, avoiding additional qualifying rolling windows.
- **S4:** `2026-09-12-R1`, cashier_04. Over exactly $5.00. Sales are large enough
  that the review threshold stays above $5.00, making R01 a warn flag.
- **S5:** September 16 has no bank deposit. The individual September 17 to 19
  deposits are dated September 20. Each meets its own three-day lag, and no
  deposit falls inside September 16's search window of September 16 to 19.
- **S6:** September 21's deposit is $100.00 below expected. September 22 to 24
  deposits are dated September 25, leaving exactly one candidate in September
  21's search window. Each delayed deposit is still within its own allowed lag.
- **S7:** `2026-09-25-R1` has no cash-count rows. This is unknown cash, not a zero
  count. September 25 has no deposit for its own business day because the day's
  expected total is incomplete. The deposits dated September 25 belong to
  September 22 to 24 and match those earlier days.
- **S8:** `2026-09-27-R2` opens at 08:00 and closes at 07:00 on the same date.
  The timestamp strings are well formed, so import accepts them. R09 flags
  their ordering during reconciliation. Available cash amounts still match the
  corresponding bank entry; the timestamp problem remains a separate review lead.
- **S9:** Importing identical files twice leaves all table counts, the import
  log, and any saved results unchanged. This behavior is already tested in M2.

Ordinary differences are strictly less than $1.00 in either direction, so they
do not accidentally create a one-dollar R02 hint. The deliberately increasing
fictional sales amounts keep deposit amounts distinct. These are test-design
choices, not claims about real sales or cash-handling policies.

## Complete expected flags with default settings

Each row is one expected flag through M9 block 1. The rule-milestone column records when
the rule was introduced. Date-only deposit flags have no shift. S9 is an import
check rather than a reconciliation flag. Tests check both the complete set and
this table. The default totals are 4 info, 7 warn, and 7 review flags.

| Scenario | Business date | Shift code | Rule code | Severity | Rule milestone |
| --- | --- | --- | --- | --- | --- |
| S1 | 2026-09-03 | 2026-09-03-R1 | R01_VARIANCE | review | M3 |
| S1 | 2026-09-03 | 2026-09-03-R1 | R02_SINGLE_DENOMINATION | info | M3 |
| S2 | 2026-09-08 | 2026-09-08-R2 | R01_VARIANCE | review | M3 |
| S2 | 2026-09-08 | 2026-09-08-R2 | R03_TRANSPOSITION_HINT | info | M9 block 1 |
| S2 | 2026-09-08 | 2026-09-08-R2 | R05_MISSING_VERIFIER_OR_NOTE | review | M3 |
| S3 | 2026-09-05 | 2026-09-05-R1 | R01_VARIANCE | warn | M3 |
| S3 | 2026-09-09 | 2026-09-09-R1 | R01_VARIANCE | warn | M3 |
| S3 | 2026-09-14 | 2026-09-14-R1 | R01_VARIANCE | warn | M3 |
| S3 | 2026-09-14 | 2026-09-14-R1 | R04_REPEAT_SHORT | warn | M5 |
| S3 | 2026-09-18 | 2026-09-18-R1 | R01_VARIANCE | warn | M3 |
| S3 | 2026-09-18 | 2026-09-18-R1 | R03_TRANSPOSITION_HINT | info | M9 block 1 |
| S3 | 2026-09-18 | 2026-09-18-R1 | R04_REPEAT_SHORT | warn | M5 |
| S4 | 2026-09-12 | 2026-09-12-R1 | R01_VARIANCE | warn | M3 |
| S4 | 2026-09-12 | 2026-09-12-R1 | R02_SINGLE_DENOMINATION | info | M3 |
| S5 | 2026-09-16 | none | R08_DEPOSIT | review | M5 |
| S6 | 2026-09-21 | none | R08_DEPOSIT | review | M5 |
| S7 | 2026-09-25 | 2026-09-25-R1 | R09_DATA_INTEGRITY | review | M3 |
| S8 | 2026-09-27 | 2026-09-27-R2 | R09_DATA_INTEGRITY | review | M3 |

These expectations assume the default thresholds and all required rules.
R03 is now active: the existing -$45 and -$9 differences qualify as whole-dollar
multiples of nine. It adds notes without changing the input CSVs or the 16
original leads. The +$27 over example is covered in a focused rule test. This
pattern does not prove that digits were swapped. R06 and R07 are not implemented.

All 28 bank entries are consumed exactly once. Twenty-seven match exactly;
the September 21 entry is consumed as the single mismatched candidate. September
16 produces the missing-deposit flag. September 25 has unknown expected cash,
so it is not matched. There are no ambiguous or unexpected entries in the default
demo; separate deposit tests cover those branches and the greedy limitations.

The approved two-pass M5 repair preserves the original 16 leads. It reserves exact
matches for every day before reviewing remaining candidates. A separate
regression changes only September 2's bank amount by one cent in either
direction: the expected $2,489.98 then receives one warn mismatch, with no
ambiguous or unexpected flag for that date. All other demo flags stay unchanged.

R04 windows contain ten shifts on September 14 and September 18, with three and
four qualifying shortages respectively. Earlier cashier shifts remain available
when a report or reconciliation selects only one of those dates. In other
datasets, later balanced or unknown shifts can retain the pattern lead while
their rolling window still has enough known shortages. Unknown/open shifts
occupy places in the window but do not count as shortages.

## Smaller runs and changed seeds

`--days` controls the number of business dates starting at 2026-09-01.
Only scenarios whose dates exist are included. A delayed deposit can fall up
to three days after the final generated shift. `--seed` changes ordinary input
amounts while preserving the specified scenario differences.

Regenerating the same inputs produces identical bytes. Generating a different
seed or date range can change records that already exist in a database; use a
fresh `--db` path for that dataset instead of expecting updates or merges.
