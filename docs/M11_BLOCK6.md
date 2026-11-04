# M11 block 6: Review a drawer

Authorized on 2026-11-04 by "next" after the block 5 repair. Started from
`56a99b8` with a clean working tree. Completed locally. Stop for `next`
before block 7.

## Delivered

**Review a drawer** (`#/review`) now shows the whole check for one entered
drawer, all from Python's reply:

- The drawer's register, date, cashier ID, and opening and closing times.
- Expected, counted, and difference, with the status and highest level.
- **How expected cash is worked out:** the shared drawer tape. Ticks mark
  known inputs only; with no register report, those lines read "unknown" and
  a note explains why.
- **Count sheet:** every line with Python's line total, and counted cash.
- **What to look at:** the drawer's leads, using the shared lead rows.
- **Which checks ran:** each rule with "Ran, no lead", "Ran, lead found", or
  "Not run" and its reason. The records check lists what it checked and what
  it could not check. A sentence explains that one drawer cannot show
  patterns over time or a whole day's bank deposit.
- **Sign off:** "Verifier ID (not checked)" and a note, with the limit taken
  from the settings and a plain statement that the ID is typed text, not a
  login or signature. **Check again** sends the same entries with the
  sign-off. A valid verifier and note clear the sign-off lead; the cash
  difference does not change.

Editing the sign-off hides the old result and asks for Check again, and a
reply that arrives after the edit is ignored. "Change the entries" returns to
Close a drawer with every entry kept. A new check from Close a drawer clears
the sign-off, because a sign-off applies to the figures it was given with.
Sign-off problems appear in a summary on Review, tied to their fields.
Nothing claims to save the review.

**Start** now links to Close a drawer, since Review discloses which checks
ran. Drawer details and Review share one tape-filling function, so both
show Python's amounts the same way.

## Checks

- **Tests:** 811 passed and 6 opt-in browser tests skipped in the normal run.
  New page test: the sign-off wording, the settings-based limit, the
  no-saving sentence, and the coverage labels.
- **Committed browser test** `tests/browser/review_drawer.cjs`, run by
  `test_review_a_drawer_signs_off_and_ignores_late_replies`: tape and count
  lines, leads, every coverage state, a stale result after a sign-off edit,
  R05 cleared by Check again with the difference unchanged, a delayed reply
  ignored after an edit (Playwright holds the response until the edit),
  an invalid verifier ID marked on Review, entries kept on going back, the
  sign-off cleared by a new check, and the missing-report case. All six
  opt-in browser tests passed in Chrome 156 and WebKit build 2370, named with
  `DRAWERCHECK_WEBKIT_EXECUTABLE` (an unofficial pairing with Playwright 1.65).
- **Accessibility:** 48 axe-core 4.14.0 scans (Start and five Review states,
  both engines, light and dark, 320 and 1,280 px): no violations
  ([results](M11_BLOCK6_AXE.json)). Colour contrast was marked incomplete in
  the 32 scans that show the drawer tape, as in M10; the token contrast
  tests cover those colours. This is not certification.
- **Layout:** no horizontal overflow at 320 or 1,280 px in any captured
  state. Screenshots caught two issues, fixed before commit: the note field
  spanned the full page width (now 40rem at most), and "Quantity" broke
  mid-word at 320 px because of a wrapping rule on the view (now off for the
  tape and count sheet, which scroll instead).
- **Budget:** CSS and JavaScript total 76,446 bytes of the 90,000 ceiling.

Not checked: real screen readers, actual browser zoom, a participant, and
the public site.

## Screenshots

[2026-11-04-m11-block6](screenshots/2026-11-04-m11-block6/): Start with the
new link; Review with case B's result, after an edited sign-off, after a
valid sign-off, with an invalid verifier ID, and without a register report.
