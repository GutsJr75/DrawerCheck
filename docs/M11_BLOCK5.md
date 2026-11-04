# M11 block 5: Close a drawer

Authorized on 2026-11-04 by "go for block 5". Started from `b474088` with a
clean working tree. Completed locally. Stop for `next` before block 6.

## Delivered

**Close a drawer** (`#/close`) lets a visitor enter one fictional drawer
without preparing seven CSVs. It follows the [contract](M11_CONTRACT.md):

1. **Copy the shift slip:** business date, register, cashier ID, starting
   cash, and the opening and closing times, with "Times not available".
2. **Count the cash:** a narrow paper count sheet with one blank box per bill
   or coin. Blank is never sent as 0. No running total is shown; Python works
   out every total after the check.
3. **Copy the register report:** "Yes" or "Not available", then four figures,
   labelled "Cash sales, before refunds" and "Paid out, not safe drops".
4. **Copy the safe drop log:** three separate choices: list the drops, "No
   safe drops this shift", and "Drop log not available". Drops can be added
   (up to 20) and removed; labels renumber.
5. **Check the drawer:** sends the entries as JSON to `POST /api/drawer`.

The fictional-data notice sits on the page itself. Neither radio group starts
chosen. Unchosen groups are caught before sending; every other check is the
server's. Each problem appears in a focused summary whose links move focus to
the field, and beside the field with `aria-invalid` and `aria-describedby`.
Count-line errors take a full-width row so they stay readable at 320 px.
Unavailable times give one message, attached to "Times not available".

On success the page moves to a minimal **Review a drawer** (`#/review`):
the drawer's identity, expected, counted, and difference from Python, the
status, and its leads, using the shared lead rows. "Change the entries" goes
back with every entry kept. Any edit discards the old result, and a reply
that arrives after an edit is ignored, as in the upload repair. Without a
result, Review says there is nothing to review and links to Close a drawer.

Both pages are reachable only by address. They are not linked from Start yet,
because Review does not show check coverage until block 6, and an isolated
drawer must not be shown without saying which checks did not run.

## Budget and performance

The user's 90,000-byte budget is now in DESIGN.md and the test, which also
counts files in any subfolder. CSS and JavaScript total **71,125 bytes**.

Measured before any asset change, then after, with
[measure.mjs conditions](M11_BLOCK5_BASELINE.json) recorded in each file:
Google Chrome 156.0.8078.80 headless through Playwright 1.65, Apple M1 with
8 GB, macOS 27.2, local loopback without throttling, a fresh browser context
per run (empty cache), the local development server already running and
warmed by one example run. Medians of five runs, in milliseconds:

| Timing | Before | After | Change |
| --- | ---: | ---: | ---: |
| Start to DOMContentLoaded | 30.8 | 37.8 | +22.7% |
| Start to load event | 61.4 | 69.5 | +13.2% |
| Try the example click to Results heading visible | 92.2 | 98.7 | +7.0% |
| Drawer link click to Drawer details heading visible | 13.3 | 11.2 | -15.8% |

DOMContentLoaded crossed the 20% investigation trigger, so both versions were
measured again in three alternating rounds
([repeats](M11_BLOCK5_REPEATS.json)). DOMContentLoaded medians were 39.7,
30.4, and 36.7 ms before and 32.2, 30.7, and 30.2 ms after; the other
timings overlapped the same way. The spread between runs is larger than the
difference between versions, so this is not treated as a regression.
Files: [baseline](M11_BLOCK5_BASELINE.json), [after](M11_BLOCK5_AFTER.json).

## Checks

- **Tests:** 810 passed, 2 optional browser tests skipped. New page test:
  every `data-field` matches a server field name, ids are unique, no radio
  starts chosen, and count boxes start blank.
- **Browser flow, Chrome 156 and WebKit (build 2370):** a Playwright script
  outside the repository walked both engines through: no expected cash on
  Close; unchosen groups caught with summary focus and links; a blank count
  line and a one-decimal amount rejected by the server with marked fields;
  fixing only those two and checking reached Review with $685.65, $665.65,
  -$20.00, Short, Needs review, and three leads; going back kept every entry;
  an edit discarded the result; unavailable times and drop log gave their
  cannot-check messages, times once; Review without a result showed its empty
  state; no horizontal overflow at 320 or 1,280 px; no script errors.
- **Accessibility:** 40 axe-core 4.14.0 scans (five states, both engines,
  light and dark, 320 and 1,280 px), WCAG 2.0 to 2.2 A/AA plus best
  practice: no violations and no incomplete results
  ([results](M11_BLOCK5_AXE.json)). The package matched npm's published
  SHA-512 and stayed in temporary tooling. This is not certification.
- **Existing upload regression test:** passes in Chrome. Its WebKit case
  could not launch: the installed Playwright 1.65 expects WebKit build 2386,
  and only build 2370 is on this machine. No browser was downloaded.
- **WebKit console note:** with this Playwright and WebKit pairing, every page
  load logs "Refused to apply a stylesheet because its hash...". The same
  message appears on the previous commit's Start page, and the site has no
  inline styles, so it is not caused by this block.

Not checked: real screen readers, actual browser zoom, and a participant.

## Screenshots

[2026-11-04-m11-block5](screenshots/2026-11-04-m11-block5/): Close a drawer
empty and with problems, Review with a result (Chrome, light and dark, 320 and
1,280 px), and Review empty.
