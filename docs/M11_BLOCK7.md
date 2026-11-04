# M11 block 7: Recount comparison

Authorized on 2026-11-04 by "next" after block 6. Started from `a2f085c` with
a clean working tree. Completed locally. Stop for `next` before block 8.

## Delivered

**Server.** `POST /api/drawer` now accepts a `recount`: the same 12 lines and
rules as the first count. With a recount, the drawer is checked on the
recount (`count_basis: "recount"`) and `initial_count` returns the first
count's lines, line totals, counted cash, difference, and status, labelled
`"first_count, compared with the same expected cash"`. No rules run on the
first count. Recount messages start with "Recount:" so they cannot be
mistaken for the first count's. A recount missing a line is a wrongly shaped
request. The block 4 "not available yet" message is gone.

**Review a drawer.** A "Recount and sign off" section has **Add a recount**,
which opens a blank count sheet. It is never filled from the first count,
because a recount should be an independent count. With a recount checked,
Review shows:

- a **First count and recount** table: counted cash, difference, and status
  for both, all from Python, captioned as coming from this check;
- the count sheet titled **Count sheet: recount**, with the first count's
  lines in a closed "First count lines" disclosure;
- leads and coverage for the recount.

The first count on Close a drawer is never changed by a recount. Editing or
removing the recount marks the shown result stale and asks for Check again,
so the figures on screen always belong to the counts that were checked.
Removing the recount clears its entries. A new check from Close a drawer
clears the recount and the sign-off, as the page says.

## Checks

- **Tests:** 814 passed and 8 opt-in browser tests skipped in the normal run.
  New: the recount balances case B while the first count stays -$20.00 short
  against the same $685.65; recount messages and limits; a partial recount
  is refused; the response carries both counts; the page has 24 blank count
  boxes and a closed recount sheet.
- **Committed browser test** `tests/browser/recount_drawer.cjs`, run by
  `test_a_recount_is_compared_and_never_replaces_the_first_count`: blank
  recount line marked; comparison figures; count sheet title; no leads after
  the recount; first count lines; Close's first count unchanged; stale after
  a recount edit; removing the recount checks the first count again; a new
  Close check clears the recount. All eight opt-in browser tests passed in
  Chrome 156 and WebKit build 2370 (named with
  `DRAWERCHECK_WEBKIT_EXECUTABLE`; an unofficial pairing with Playwright 1.65).
- **Accessibility:** 24 axe-core 4.14.0 scans of the three recount states,
  both engines, light and dark, 320 and 1,280 px: no violations
  ([results](M11_BLOCK7_AXE.json)). Colour contrast was incomplete only in
  the recounted state, which shows the drawer tape, as before.
- **Layout:** no horizontal overflow in any captured state.
- **Budget:** CSS and JavaScript total 78,418 bytes of the 90,000 ceiling.

Not checked: real screen readers, actual browser zoom, a participant, and
the public site.

## Screenshots

[2026-11-04-m11-block7](screenshots/2026-11-04-m11-block7/): the recount
sheet open, a recount line problem, and the recounted result with both
counts compared.
