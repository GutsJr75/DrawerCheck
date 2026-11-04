# M11: Fictional closing workflow

Roadmap updated 2026-11-04. The user authorized this plan update, following
their choice to support both cashiers and managers on separate pages.
All nine blocks are complete locally: the [walkthrough](M11_BLOCK1.md), the
README, the reviewed [contract](M11_CONTRACT.md), `POST /api/drawer`,
[Close a drawer](M11_BLOCK5.md), [Review a drawer](M11_BLOCK6.md), the
[recount](M11_BLOCK7.md), the [closing sheet](M11_BLOCK8.md), and
[final verification](M11_BLOCK9.md). Open checks are in the
[M11 checklist](M11_CHECKLIST.md). M12 needs its own approval.
This schedule takes priority over the unfinished M9 R06 and R07 rules.

## Goal and starting assumptions

A person can complete a realistic fictional close without our help: count a
drawer, compare register figures, review a difference, and export the record.
Whether the flow works for an unfamiliar participant remains unverified.

Assume a small US convenience store, US dollars, and one end-of-day closing
count per register/day. A cashier counts and supplies figures; a manager
reviews differences. These are research-informed design assumptions, not
claims about the user's store, observed customer needs, or universal practice.
The user does not currently own a store. Keep all identities and data fictional.

## Two pages, one temporary check

| Page | Main task | Planned content |
| --- | --- | --- |
| Close a drawer | Count and supply register figures | Business date, register and fictional cashier ID, opening float, bill/coin quantities, cash sales before cash refunds, cash refunds, paid-ins, paid-outs, safe drops, and an optional explanation. Confirm the exact required fields in block 3. |
| Review a drawer | Understand and review the same figures | Expected/count/difference, a calculation breakdown, available review leads, check coverage, an optional recount, fictional verifier details and explanation, and a closing-summary download. |

Use action names in navigation. One browser session carries the same inputs
between pages; no repeated entry. Count before revealing expected cash. This
encourages an independent count but cannot prove what someone previously saw.
Count the cash physically present, including float, before the closing cash
removal. Earlier safe drops are recorded separately. Opening float and cash
retained for the next day are different concepts; M11 does not calculate a
whole-day deposit from one isolated drawer.

Both pages are accessible to the same visitor. A page label or typed verifier
ID is not a login, verified signature, or protected manager permission.
Recounts and notes remain temporary; durable review status waits for M12.

## Blocks in order

Each row is a separate approval, work, verification, and local-commit block.
Target 30 to 60 minutes per block; split before expanding an oversized row.
Stop after every block and wait for **next**. Never start the next row just
because the preceding row passed. All nine blocks are **complete locally**.

| Block | Work | Done when |
| --- | --- | --- |
| 1. Fictional closing walkthrough | Prepare one fictional register-report layout, count sheet, cashier-to-manager task script, and a place to record observations. Include balanced, short, and missing-input cases. Use the current site to observe comparison/review friction and a paper walkthrough for the proposed manual-entry path. No application code. | The tasks have expected answers and a documented field/formula mapping. Record any actual participant observations separately from assumptions. If nobody is available, mark participant testing pending, carry that gap into block 9, and stop for the normal next-block review. A prepared script is not a passed user test. Do not contact anyone on the user's behalf. |
| 2. README front page | Put purpose, demo, example outcome, screenshots, and limitations first. Link to detailed status and verification rather than leading with milestone numbers. | Links work, claims describe implemented behavior, and planned pages are not advertised as available. Evidence files and screenshot folders have not been moved, renamed, or deleted. |
| 3. Input and check contract | Finalize fields, fictional report labels, empty/zero rules, money/count limits, transient state, check coverage, and the request/response shape. Document the two-page handoff and closing-export contents. No application code. | Every field has a meaning and a validation rule. Cash sales are explicitly before separately supplied refunds; drops cannot also be counted as paid-outs. Unknown input remains unknown. No fabricated shift times, extra registers, bank entries, or historical shifts are needed to make the core run. Review the contract before implementation. The [points to settle in block 3](#points-to-settle-in-block-3) are resolved. |
| 4. Shared Python one-drawer check | Build the smallest adapter/service around existing money, formula, and applicable rule functions. Add a bounded web request for manual input. Keep rule selection explicit. | Known examples match core results. Missing input, zero count, invalid money/counts, negative expected cash, limits, cleanup, and isolated concurrent requests are covered. An isolated drawer does not generate missing-bank or repeated-shortage conclusions. Existing CLI and full-run behavior still pass. |
| 5. Close a drawer page | Build count-first entry, register-figure entry, field help, validation recovery, and the handoff using block 4. Follow the existing design system and required frontend skills. | A visitor can supply fictional data without seven CSVs, correct an error, and continue without retyping. Blank quantities cannot silently mean a confirmed empty drawer. Python supplies all cash totals. Before any asset change, a local performance baseline is recorded and the CSS/JS budget becomes 90,000 bytes, per the [contract](M11_CONTRACT.md#css-and-javascript-budget-decided-2026-11-04). Capture dated screenshots. |
| 6. Review a drawer page | Show the shared snapshot, explanation, available leads, check coverage, and temporary fictional verifier/note fields. | Back navigation preserves entries. Edits invalidate old results and require a fresh Python check; late replies cannot overwrite a newer check. A supplied note/verifier can change R05's missing-detail lead without changing the cash difference. No saved-review claim. Capture dated screenshots. |
| 7. Recount comparison | Add one optional second count while retaining the initial count in the temporary check. | Both counts and their differences remain labelled; Python recalculates the selected count. Recounting cannot silently overwrite the initial count. If inputs change, the page identifies which snapshot each count belongs to. Capture dated screenshots. |
| 8. Closing summary and printing | Add a self-contained downloadable HTML closing sheet with suitable print styling, reusing existing escaping and report conventions. Include input amounts, initial/recount labels, verifier/note if supplied, example settings, and check coverage. | The sheet works offline and prints legibly; unknown and zero remain distinct. It says fictional data and that supplied reviewer details are unverified. Existing text/HTML/CSV full-run reports remain compatible. Any new CSV cells use sanitize_cell. Capture dated screenshots of app changes. |
| 9. End-to-end verification and handoff | Exercise count, compare, review, recount, export, refresh, correction, cancellation, and failed/late requests. Repeat the fictional task with an unfamiliar participant where available. Update setup/use documentation and evidence. | Core/web checks pass; Chrome/WebKit, keyboard, narrow/large-text, both themes, safe rendering, and limits are verified within recorded scope. Repeat the block 5 performance measurements and compare. Record real screen-reader/zoom/participant gaps honestly. Hosted CI and live checks are separate observed evidence, never inferred from local passes. Stop before M12. |

For every block, run pytest and both Ruff checks, update plan progress, add the
three learning-log bullets, run `git diff --check`, and make a local commit.
Do not invent application tests for documentation changes. UI blocks add dated
screenshots and a screenshot-index row under the existing preservation rule.
Do not silently raise the 2 MiB request or 10,000,000-byte response budgets.
The user approved raising CSS/JS to 90,000 bytes on 2026-11-04, applied in
block 5; review any other budget amendment before implementation.
No push or deployment is implied by a local block's approval.

### Points to settle in block 3

Added 2026-11-04 after a code check of the plan. Block 3 must resolve each
point in its contract before block 4 starts.

**Status:** each point, and the five questions from block 1, has a proposed
answer in [M11_CONTRACT.md](M11_CONTRACT.md#summary-of-decisions).

1. **Closed state without invented times.** `Shift.opened_at` is a required
   string, `calculate_shift` reports a shift without `closed_at` as open, and
   the not-counted check in `integrity_flags` runs only on closed shifts.
   Choose between asking for genuine open and close times and adding an
   explicit closed input to the model. Never fill in a placeholder timestamp.
2. **Explicit rule selection.** `evaluate_rules` with an empty history returns
   no R04 lead, which would read as "ran, no lead". Call the applicable rules
   individually. Block 4 adds a test that R04 and R08 report "not run".
3. **Fictional-data notice on entry.** Manual entry makes real figures easier
   to type than seven prepared CSVs did. Show the fictional-data notice on the
   Close a drawer page itself, not only on Start.
4. **Reuse the walkthrough.** Block 1's worked cases and expected answers
   become block 4's test cases.
5. **One page name.** This plan uses both "Review a drawer" and "Review
   drawers". Choose one for navigation and headings.

## Check coverage for an isolated drawer

Python must supply coverage metadata to the page and closing sheet. Distinguish
**ran, no lead**, **ran, lead found**, and **not run, required data unavailable**.
Passing input validation does not mean the drawer balances or review is complete.

| Check | M11 treatment |
| --- | --- |
| R01 Cash difference | Run when expected and counted cash are known, using the existing example configuration. |
| R02 Single bill | Run when the difference is known. |
| R03 Possible swapped digits | Run when the difference is known; retain the heuristic qualification. |
| R05 Missing sign-off | Run with the supplied fictional verifier/note and existing threshold. A clear result does not authenticate a reviewer or resolve the cash difference. |
| R04 Repeated shortages | Not run: no historical shifts are available in this path. |
| R08 Bank deposit | Not run: one drawer is not a complete day with bank records. Do not imply a matched or missing bank deposit. |
| R09 Missing/inconsistent records | Run only supported checks on supplied facts, such as missing counts/totals and negative expected cash. Check time order only if genuine input times are supplied. Cross-register completeness, overlaps, and duplicate closing records are unavailable without wider records; disclose partial coverage. |

Reject malformed input before calculation. If partial input is supported,
identify which calculations and rules cannot run. Do not convert omissions to
zero, invent timestamps, or create a false all-checks-passed state.

## State and scope boundaries

Keep M11 draft data only in the current page's memory and isolated temporary
server workspaces. Refresh/close loses it; warn clearly and offer the closing
download. Do not put drawer records in browser storage, URLs, analytics,
application logs, a shared server database, or a saved-review queue.
The public service remains fictional-data-only. Two pages do not provide
cross-device handoff or access control. Preserve demo/upload routes and all
existing report and temporary-resource protections.

Defer store settings UI, arbitrary CSV column mapping, direct POS/bank
connections, accounts, cloud storage, multiple closing shifts/register/day,
new currencies, and R06/R07. None is necessary to prove this workflow.

## M12: Later local saved records

This is a future direction, not an approved implementation or a promise that
local storage is automatically safe. After M11, prepare a detailed M12 plan
and obtain approval for its first block. Keep public demo storage unchanged.

Work in this order, with a separate stop and **next** after each block:

1. **Storage/access contract:** choose a local database location, permissions,
   shared-computer assumptions, retention/deletion, supported updates,
   record identifiers, duplicate-close handling, reviewer attribution, and
   backup/restore behavior. Specify the boundary between the local app and
   public demo, and what a page label cannot protect. Approve before coding.
2. **Local web launcher:** a simple local-only command, bound to loopback,
   without debug mode or unintended network exposure. Define the browser
   request protections for local writes. Installation and restart work.
3. **Save and reopen:** transactionally save a complete closing snapshot with
   its settings/version. Reopening preserves amounts; a failed save leaves
   no partial record. Keep existing import/CLI behavior compatible.
4. **History:** list saved closings and open one from the manager page. State
   the supported period, history completeness, and available checks; enable
   history rules only when their actual inputs are available.
5. **Review record:** save a factual note, supplied reviewer ID, review time,
   and reviewed/unreviewed state. Reviewed stays separate from balanced or
   resolved; supplied identities remain unauthenticated in this local model.
6. **Traceable corrections:** preserve original inputs, correction reason,
   new revision, and recalculated results. Link prior review to its revision
   and require review of a changed version. Never silently rewrite history.
7. **Backup:** make a consistent backup with clear location and contents.
   Verify that interrupted backup cannot replace a usable backup with a
   partial file.
8. **Restore:** validate compatibility/integrity before replacing active
   records; preserve the current database until success. Demonstrate recovery
   of cash data, review notes, correction history, and settings from backup.
9. **Recovery and usability verification:** exercise restart, interrupted
   saving, duplicates, read-only/locked storage, and failed restore. Record
   actual outcomes, remaining shared-computer limits, setup instructions,
   fictional task observations, and screenshots. Split this row if necessary.

All development and committed examples remain fictional. Any future proposal
to handle real business data requires a separate scope decision informed by
the actual store, device, access needs, and tested recovery behavior.

## Research and validation status

Official sources rechecked on 2026-11-04:

- [Shopify register sessions](https://help.shopify.com/en/manual/sell-in-person/shopify-pos/cash-register-management/register-sessions-in-shopify-pos):
  describes opening cash, cash movements, closing counts/notes, retained float,
  printable closing details, and later session review. Used as workflow
  background; our exact fields and count-first ordering are design choices.
- [Square drawer reports](https://squareup.com/help/us/en/article/8358-view-cash-drawer-reports):
  describes selecting sessions by date/location and reviewing paid-in/out
  details. Supports a distinct review task, not a claim that DrawerCheck
  integrates with Square or accepts its reports unchanged.

The fictional report in block 1 must explicitly define how its figures map
to DrawerCheck. It is not a vendor-certified export. No participant study,
real store deployment, reduction in losses, or readiness for real cash control
is established by these references or this plan.
