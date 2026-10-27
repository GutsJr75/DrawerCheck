# M10 block 2: Results summary and layout

Authorized by the user's "go for block 2" on 2026-10-26. Completed locally.
Stop for `next` before block 3, Results grouping. No new push, hosted CI, or
deployment result is claimed.

## Delivered

Results now opens with one date range and a torn-edge slip labelled "Full run":
9 of 60 drawers have leads to check, 16 drawer leads, two whole-day leads on
two dates, and 51 drawers with no own leads. The qualification "No leads found
by these checks" stays visible. A green tick reinforces that wording, never
an exact match or a completed human review. It draws once per run over 600 ms,
stays still with reduced motion, and hides when no drawers qualify.

At 960 px and above, the review list occupies the main column. Filters,
secondary download buttons, and level definitions sit in a 19rem side column.
Below that width, filters precede the review list and downloads follow it.
There is one set of controls. DOM and keyboard order agree, without positive
tabindex. The download reminder remains. Detailed lead/severity totals move
to a closed disclosure below the review area.

Python adds separate affected/unaffected drawer counts, disjoint highest-level
drawer counts, drawer/whole-day lead totals, and whole-day date counts.
Whole-day uses `shift_id is None` for any rule; deposit-lead days remain R08-only.
The tests check the count identities and preserve existing summary meanings.
`labels.dates` supplies English weekday/month/day/year labels for range
endpoints, every shift/day/flag date, bank-only dates, and opening/closing clock
dates. Including clock dates preserves the existing overnight-shift display.
The browser only looks up these labels and renders supplied counts.

The lead list is still flat. Grouping, severity section headings, and the full
More detail treatment await block 3. Drawer details, Start, and Prepare files
retain their current structures. Financial calculations, flag contents, report
contents, resource caps, and temporary-workspace behavior are unchanged.
Review checkboxes and report restyling remain deferred.

## Verification actually run

| Check | Observed result |
| --- | --- |
| `.venv/bin/pytest -q`, final run with local-socket permission | PASS: 716 tests in 15.71 seconds, including core/web/report parity, cleanup, count invariants, date coverage, contrast, assets, and the unchanged combined-cap regression. |
| `.venv/bin/pytest -q tests/test_web.py tests/test_web_page.py` | PASS: 119 tests in 6.58 seconds before the final decorative tick addition; the final full suite includes it. |
| `.venv/bin/ruff check .` | PASS. |
| `.venv/bin/ruff format --check .` | PASS: 63 files already formatted in the final check. |
| `git diff --check` | PASS. |
| Chrome final matrix | PASS: all four views at 320/1,280 x 900 in both themes, plus Results at 959/960 x 900 in both themes. No page-wide overflow, page-error events, or external resources; fonts loaded. First review title starts at y=793 px in the 1,280 x 900 desktop target. |
| Keyboard and filters | PASS: Tab from Results heading reaches date, level radios, then review links; ArrowRight applies a level. Downloads follow review links in Tab order. A Note on a Needs review drawer remains findable; breadcrumb Shift+Tab/Enter restores filters with a 3 px ring. Summary remains Full run. No-match recovery works. |
| Reports | PASS: all three downloaded files match the Python response contents by SHA-256, while filters are reset independently of the reports. |
| States | PASS: real seven-file fake uploads for clean records and a bank-only run; no-leads visibility, no invented drawer links, singular whole-day wording, busy/Cancel, simulated 503 followed by real retry, and refresh recovery. |
| Tick and motion | PASS: initial 600 ms animation, no replay on drawer return, visible still tick under reduced motion, no tick when zero drawers qualify. Forced-colors scrollbar fallback also passed. |
| Generic premium strict audit | Retains the same seven external-handler detection findings as block 1, not a clean pass. All seven buttons have handlers in app.js. Example, Cancel, upload, and all downloads were exercised. No dummy attributes were added to silence the scanner. |
| Official DESIGN.md lint | Zero errors, one warning because the guide uses Markdown rather than YAML. Exact token agreement and contrast are checked by the project tests. |

The browser report comparison initially tried a dynamic Node import unsupported
by the CLI's code sandbox. It was corrected to hash expected contents in the
browser and compare the saved files in Python; all three comparisons passed.
This was a verification-script correction, not an application failure.

## Measured budgets

| Resource | Observed value | Unchanged ceiling |
| --- | --- | --- |
| CSS plus JavaScript, uncompressed | 56,141 bytes | Under 60,000 bytes |
| Local WOFF2 fonts | 51,748 bytes | Under 200,000 bytes |
| Built-in demo JSON | 159,958 bytes | 10,000,000 bytes |
| Combined allowed workload, 1,000 drawers and 2,000 dates | 8,620,061 bytes, HTTP 200 | 10,000,000 bytes |
| Combined workload with overlong aggregate detail | HTTP 400, bounded 136-byte error | Same response cap; not increased |

Raw evidence: [initial matrix](M10_BLOCK2_BROWSER.json),
[final matrix](M10_BLOCK2_BROWSER_FINAL.json),
[capture recheck](M10_BLOCK2_CAPTURE_RECHECK.json),
[interactions and report hashes](M10_BLOCK2_INTERACTIONS.json),
[edge states](M10_BLOCK2_STATES.json), [tick checks](M10_BLOCK2_MOTION.json),
[measurements](M10_BLOCK2_METRICS.json), and [static audit](M10_BLOCK2_AUDIT.json).

## Screenshot timeline and limits

The [new dated folder](screenshots/2026-10-26-m10-block2/) contains 34 original
viewport PNGs. It retains the first 1,280 x 720 capture, the 20-case matrix
before the decorative tick, two scrolled narrow control/download views, clean
and bank-only states, and eight final Results captures with the shipped tick, plus a settled
959 px light recapture.
Use Results filenames containing `final` for the final summary appearance;
for the 959 px light view, use `final-checked`. The earlier final PNG showed
repeated header pixels near its bottom. A fresh settled capture and DOM check
confirmed one header and the expected Review leads heading at y=825 px, with
no overflow. The artifact did not reproduce; its original PNG is retained.
Earlier folders were not changed. Changed Results layouts, breakpoint pairs,
narrow controls/downloads, empty states, and representative sibling views were
visually inspected as well as checked for geometry.

This block used Playwright CLI 1.64.0-alpha with headless Google Chrome 156
against localhost. It does not claim a new WebKit, browser-zoom, OS-native popup
keyboard, real screen-reader, or unfamiliar-user usability pass. Those broader
checks remain for the later verification block, with the existing manual
validation limits carried forward. No new hosted CI or deployment is claimed.
