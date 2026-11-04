# M11 block 1: Fictional closing walkthrough

Prepared 2026-11-04 under the user's "go for block 1". This block adds no
application code. It prepares a paper closing exercise with known answers,
maps every paper figure to DrawerCheck, and records an agent walkthrough of
the current site. See [M11_PLAN.md](M11_PLAN.md) for the block list.

**Participant status: pending.** No unfamiliar person has tried this exercise
yet, and nobody was contacted on the user's behalf. The observations in this
file come from the agent (Claude), who knows the code, so they are not user
testing. This gap carries into block 9.

**Two documents.** Participants see only the
[participant packet](M11_PARTICIPANT_PACKET.md): drawer descriptions, register
reports, drop logs, a cashier's completed count for drawer C, and blank forms.
This file is the facilitator guide and answer key. Keep it out of view during
a session.

## The cases

Everything describes **Demo Store #001**, business date Monday, November 2,
2026, with three registers. Each register has three papers: a count sheet, a
register report, and a safe drop log. The cases are:

| Case | Register | Cashier ID | What it tests |
| --- | --- | --- | --- |
| A | R1 | cashier_01 | Balanced within tolerance, but not exact |
| B | R2 | cashier_02 | Short by $20.00 with no sign-off, then a manager review |
| C | R3 | cashier_03 | The register report is missing |

All identities, amounts, and bag numbers are fictional.

### Register report layout

This layout is invented for the exercise. It is not any vendor's report. It
deliberately does not print an expected cash amount, so the cashier counts
before seeing what the drawer should hold. Some real register systems do show
expected cash; that difference is a design choice for this exercise.

```text
DEMO STORE #001          END OF DAY REGISTER REPORT
Register: R2             Business date: 2026-11-02
Cashier ID: cashier_02   Opened 08:00   Closed 20:00

SALES BY TENDER
  Card sales                          1,588.15
  Cash sales                          1,316.40
  Total sales (all tenders)           2,904.55

CASH ADJUSTMENTS
  Cash refunds                           18.25
  Paid in                                20.00
  Paid out                               32.50

ACTIVITY
  Voids                                      2
  No sale (drawer opened)                    1
```

| Line | R1 (case A) | R2 (case B) | R3 (case C) |
| --- | ---: | ---: | --- |
| Card sales | 1,210.40 | 1,588.15 | Not printed |
| Cash sales | 842.35 | 1,316.40 | Not printed |
| Total sales (all tenders) | 2,052.75 | 2,904.55 | Not printed |
| Cash refunds | 6.49 | 18.25 | Not printed |
| Paid in | 0.00 | 20.00 | Not printed |
| Paid out | 15.00 | 32.50 | Not printed |
| Voids | 1 | 2 | Not printed |
| No sale | 2 | 1 | Not printed |

For case C, the packet says: "The register report for R3 did not print before
the register was closed." The count sheet and drop log are still available.

### Safe drop log

| Register | Time | Bag number | Amount |
| --- | --- | --- | ---: |
| R1 | 15:30 | DEMO-BAG-1102-R1-A | 500.00 |
| R2 | 13:00 | DEMO-BAG-1102-R2-A | 400.00 |
| R2 | 17:00 | DEMO-BAG-1102-R2-B | 400.00 |
| R3 | 16:00 | DEMO-BAG-1102-R3-A | 300.00 |

### Answer key: completed count sheets (facilitator only)

The count sheet header records the starting cash given at opening: $200.00
for every register. The cashier writes a quantity on every line, including 0.
Drawers A and B are what a correct task 1 produces from the packet's drawer
descriptions. Drawer C is printed in the packet, because cashier_03 counted it.

| Bill or coin | R1 qty | R1 total | R2 qty | R2 total | R3 qty | R3 total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| $100 | 0 | 0.00 | 1 | 100.00 | 0 | 0.00 |
| $50 | 2 | 100.00 | 3 | 150.00 | 2 | 100.00 |
| $20 | 10 | 200.00 | 12 | 240.00 | 8 | 160.00 |
| $10 | 8 | 80.00 | 6 | 60.00 | 7 | 70.00 |
| $5 | 12 | 60.00 | 9 | 45.00 | 10 | 50.00 |
| $2 | 0 | 0.00 | 0 | 0.00 | 0 | 0.00 |
| $1 | 56 | 56.00 | 47 | 47.00 | 38 | 38.00 |
| 50 cents | 0 | 0.00 | 0 | 0.00 | 0 | 0.00 |
| 25 cents | 80 | 20.00 | 72 | 18.00 | 60 | 15.00 |
| 10 cents | 30 | 3.00 | 35 | 3.50 | 28 | 2.80 |
| 5 cents | 20 | 1.00 | 31 | 1.55 | 40 | 2.00 |
| 1 cent | 61 | 0.61 | 60 | 0.60 | 0 | 0.00 |
| **Counted cash** | | **520.61** | | **665.65** | | **437.80** |

How the packet's drawer descriptions become these quantities:

| Line | Drawer A | Drawer B |
| --- | --- | --- |
| $1 | 2 bundles of 25 + 6 loose = 56 | 1 bundle of 25 + 22 loose = 47 |
| 25 cents | 2 rolls of 40 = 80 | 1 roll of 40 + 32 loose = 72 |
| 1 cent | 1 roll of 50 + 11 loose = 61 | 1 roll of 50 + 10 loose = 60 |
| Other lines | Counted directly from the description | Same |
| Receipt in drawer | Paid-out receipt for $15.00: not cash, not counted | Paid-out receipt for $32.50: not cash, not counted |

Lines that the description never mentions ($100 in A, $2, and 50 cents) are 0.

## Field and formula mapping

| Paper figure | DrawerCheck field | Role in the formula |
| --- | --- | --- |
| Count sheet header: starting cash | `shifts.csv` `opening_float` | Plus |
| Register report: Cash sales | `pos_totals.csv` `cash_sales` | Plus. Cash taken for sales, before refunds. |
| Register report: Paid in | `pos_totals.csv` `paid_ins` | Plus |
| Register report: Cash refunds | `pos_totals.csv` `cash_refunds` | Minus. Entered separately, never already netted out of cash sales. |
| Register report: Paid out | `pos_totals.csv` `paid_outs` | Minus. Safe drops are never entered here. |
| Safe drop log: each amount | `safe_drops.csv` `amount` | Minus, summed |
| Count sheet: quantity per line | `cash_counts.csv` `quantity` | Counted cash = value x quantity, added together |
| Register report: Card sales | `pos_totals.csv` `card_sales` | Stored, not used. Cards put no cash in the drawer. |
| Register report: Total sales | Not stored | Not used. It mixes card and cash. |
| Register report: Voids, No sale | `void_count`, `no_sale_count` | Stored, not used by any current rule |
| Report header: cashier ID, times | `shifts.csv` `cashier_id`, `opened_at`, `closed_at` | Identity and status only |

```text
Expected cash = starting cash + cash sales + paid in
                - cash refunds - paid out - safe drops
Difference    = counted cash - expected cash   (below zero is short)
```

## Expected answers

These answers come from the real program, not from hand arithmetic alone.
The packet was written as the seven CSV files, then imported, reconciled, and
explained with the CLI using `config.toml` (see Verification below).

| Case | Expected cash | Counted cash | Difference | Status | Review leads |
| --- | ---: | ---: | ---: | --- | --- |
| A, R1 | $520.86 | $520.61 | -$0.25 | Balanced within the $1.00 tolerance | None |
| B, R2 | $685.65 | $665.65 | -$20.00 | Short | R01 review (limit $13.16), R02 note ($20 bill), R05 review (no verifier or note) |
| B after review | $685.65 | $665.65 | -$20.00 | Short | R01 review and R02 note only |
| C, R3 | Unknown | $437.80 | Unknown | Incomplete | R09 review: "Missing POS totals. Expected cash is unknown." |

Working for the expected cash:

- A: `200.00 + 842.35 + 0.00 - 6.49 - 15.00 - 500.00 = 520.86`
- B: `200.00 + 1,316.40 + 20.00 - 18.25 - 32.50 - 800.00 = 685.65`
- C: cash sales, paid in, refunds, and paid out are unknown, so expected cash
  stays unknown. It must not be worked out with zeros.

Case B's review limit is 1% of $1,316.40 rounded down to $13.16, which is
between the $5.00 floor and the $20.00 cap. "B after review" adds verifier ID
`manager_01` and the note "Recounted with manager. Still short 20.00. Report
and drop log rechecked." The difference does not change; only R05 goes away.

Case A shows why "balanced" needs care: the drawer is 25 cents short, but
within the example tolerance. The exact -$0.25 must stay visible.

### Check coverage for a single drawer

For the planned single-drawer path, the result for every case should also say:

| Check | A | B | C |
| --- | --- | --- | --- |
| R01, R02, R03 | Ran, no lead | Ran; R01 and R02 found leads, R03 none | Not run: difference unknown |
| R05 Missing sign-off | Ran, no lead (under $20.00) | Ran, lead found, then no lead after review | Not run: difference unknown |
| R04 Repeated shortages | Not run: no history | Not run: no history | Not run: no history |
| R08 Bank deposit | Not run: one drawer is not a whole day | Same | Same |
| R09 Records | Partly ran: no problems in supplied facts | Same | Partly ran: register report missing |

## Task script

The facilitator reads one task at a time and records observations on the
sheet below. In the paper version, the facilitator plays the app: after the
participant finishes tasks 1 and 2 for a drawer, the facilitator hands over
that drawer's result card from the next section. The participant does no
arithmetic beyond writing line totals on the count sheet. No real names are
recorded; participants are P1, P2, and so on.

Give the participant the packet's Part 1 and two blank forms for drawer A,
then Part 2 for drawer B, then Part 3 for drawer C. Hand out the review form
at task 5. The packet's figures form offers "not available", so task 6 tests
whether the participant uses it rather than writing 0.

Say at the start: "Everything here is made up. We are testing the papers and
the steps, not you. Think out loud. You can stop at any time."

**Cashier part (case A, then case B):**

1. Using the drawer description, fill in the count sheet. *Done when:* every
   line has a quantity, including 0, and the total matches $520.61 (A) or
   $665.65 (B).
2. Using the register report and drop log, write down the figures DrawerCheck
   needs. *Done when:* all six formula figures are found, card sales and total
   sales are left out, and safe drops are not added to paid out.
3. Read the result card. Say whether the drawer balanced. *Done when:* for A
   they say "balanced, 25 cents short within the limit"; for B, "short $20".

**Manager part (case B, then case C):**

4. For case B, say what you would do next. *Done when:* they mention a recount
   and checking for a misplaced $20 bill. Record whether they also mention the
   missing verifier and note.
5. The recount gives the same quantities. Write a verifier ID and a short
   factual note. *Done when:* the note describes what was checked and blames
   nobody. The new result card shows the same -$20.00 without the sign-off lead.
6. For case C, try to complete the check. *Done when:* they do not write zeros
   for the missing report lines and say the report must be reprinted or found.
7. Using any result card, say which checks did not run and why. *Done when:*
   they name the history check and the bank deposit check.
8. Say what you would keep as a record of this close. *Done when:* they
   mention the counts, report figures, difference, and the note or verifier.

## Result cards (facilitator hands these out)

Cut these out or show them one at a time. Each card stands in for the result
the planned app would show. Do not hand out a card before its task.

```text
RESULT CARD: Drawer A, Register R1, Monday, November 2, 2026
Expected cash      $520.86
Counted cash       $520.61
Difference          -$0.25
Balanced (within $1.00)
Leads to check: none
Checks not run: repeated shortages (no earlier shifts);
  bank deposit (one drawer is not a whole day)
```

```text
RESULT CARD: Drawer B, Register R2, Monday, November 2, 2026
Expected cash      $685.65
Counted cash       $665.65
Difference         -$20.00
Short
Needs review: Short by $20.00. Recount recommended.
Needs review: Missing verifier and variance note for a difference of
  $20.00. Review recommended.
Note: Variance equals one $20 bill. Check for a miscounted or misplaced bill.
Checks not run: repeated shortages (no earlier shifts);
  bank deposit (one drawer is not a whole day)
```

```text
RESULT CARD: Drawer B after review, Register R2, Monday, November 2, 2026
Expected cash      $685.65
Counted cash       $665.65
Difference         -$20.00
Short
Needs review: Short by $20.00. Recount recommended.
Note: Variance equals one $20 bill. Check for a miscounted or misplaced bill.
Verifier ID and note supplied (not checked against any person).
Checks not run: repeated shortages (no earlier shifts);
  bank deposit (one drawer is not a whole day)
```

```text
RESULT CARD: Drawer C, Register R3, Monday, November 2, 2026
Expected cash      unknown (register report not available)
Counted cash       $437.80
Difference         unknown
Missing records
Needs review: Register report figures are missing. Expected cash is unknown.
Checks not run: cash difference checks (difference unknown);
  repeated shortages (no earlier shifts);
  bank deposit (one drawer is not a whole day)
```

The lead wording on the cards follows the current program, except drawer C,
which says "Register report figures" instead of "POS totals" to test the
plainer wording raised in the walkthrough below. Block 3 decides the real text.

## Observation sheet

Copy one per participant. Keep observations separate from assumptions.

| Field | Entry |
| --- | --- |
| Participant | P_ |
| Date | |
| Has counted a cash drawer before | Yes / No |
| Task (1 to 8) | |
| Finished without help | Yes / No |
| Matched the expected answer | Yes / No / Partly |
| Where they hesitated | |
| Questions they asked | |
| Wrong entries or wrong lines used | |
| Their words (no names) | |
| Time taken | |

## Agent walkthrough of the current site

Done 2026-11-04 on the local app (`flask --app drawercheck.web:create_app run`)
in Playwright's Chrome, using the packet's seven CSV files. These are the
agent's observations, not a user test. No screenshots were taken, since this
block does not change how the site looks.

1. **Getting the data in was the hardest part.** Three drawers needed seven
   files and 36 count rows, with each drawer code repeated across four files.
   The agent wrote a script to produce them. A person with only the paper
   packet would struggle here, which supports the plan's manual entry.
2. **The results were correct and clear.** Results said "2 of 3 drawers have
   leads to check" and "1 drawer with no leads". Drawer details for R2 showed
   $685.65, $665.65, and -$20.00 with the full tape, the count sheet, and all
   three leads, matching the CLI.
3. **There is nowhere to act on a lead.** R2 says "Recount recommended" and
   "Missing sign-off", but a manager cannot record a recount, verifier, or note
   in the site. Clearing R05 means editing `shifts.csv` and uploading all seven
   files again. This supports blocks 6 and 7.
4. **"POS totals" is jargon.** Case C reads "Missing POS totals. Expected cash
   is unknown." The unknown is handled correctly, but the paper calls it a
   register report. Block 3 should pick wording a beginner recognizes.
5. **The deposit check's absence is quiet.** With no bank entries and an
   incomplete day, Results shows "0 whole-day leads on 0 dates" without saying
   the deposit check could not run. The single-drawer path must state this.
6. **A balanced drawer is easy to miss.** R1 appears only as a count in the
   summary and inside the closed "All drawers" section. That suits a manager,
   but a cashier checking their own drawer needs to see it directly.

The CLI also showed R1's deposit share as "unknown" even though R1 is
complete. That is by design: a drawer's share is shown only when the whole day
is complete. The single-drawer path should leave the deposit out entirely.

## Questions this adds for block 3

- **A partly printed report.** The core stores the register report as one
  record, so one missing line makes the whole report unknown. Decide whether
  manual entry keeps that rule (simplest and consistent) or allows single
  unknown lines.
- **Blank versus 0 on the count sheet.** On paper a blank line is ambiguous.
  Decide whether every line needs a number or there is an explicit "none
  counted" choice.
- **Drops as a list or a total.** The drop log has one row per bag. Decide
  whether the form takes each drop or one total.
- **Where the starting cash comes from.** Here it is on the count sheet
  header. Confirm the form asks for it separately from the report figures.
- **Recount wording.** Decide what a recount records: new quantities, who
  recounted, or both.

These join the five points already listed in M11_PLAN.md.

## Verification

- The packet's figures were written as the seven CSV files outside the
  repository, then checked with `drawercheck import`, `drawercheck reconcile`,
  and `drawercheck explain` for each drawer, before and after the case B
  review. Reconcile saved 4 review flags before the review and 3 after.
  Every number in Expected answers was copied from that output.
- The same files were uploaded to the local site and produced the same
  results on Results and Drawer details.
- No participant observations exist yet. Participant testing is pending.
