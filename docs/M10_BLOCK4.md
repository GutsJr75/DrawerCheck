# M10 block 4: Drawer details

Authorized on 2026-10-27 after the user reported pushing block 3 commit
`b777b7a`. The local branch and origin/main tracking reference matched that
commit at the start. No new hosted CI or deployment result was inspected.
Completed locally. Stop for `next` before block 5, Start.

## Delivered

Drawer details now uses a human register/date title, including weekday and
year, for the page and browser tab. Unique drawer code, cashier ID, and times
remain underneath, with full date labels for overnight shifts. A single
surface strip shows Expected cash, Counted cash, and Difference using Python's
exact strings. Written status and highest own-lead level remain independent:
a balanced amount can still have a record problem requiring review.

The tape and count sheet remain side by side when they fit and stack on
phones. Six known tape inputs can carry the shared green tick. The visible
legend says this means availability for the calculation, and that an aggregate
zero for safe drops does not prove a source row exists. Unknown inputs and
calculated outputs receive no tick. The SVGs are decorative and static.

Supplied zero-quantity rows fold only when another supplied quantity is
positive. A native Show/Hide button exposes aria-expanded and controls those
same rows by ID. Each drawer resets to its initial collapsed state. All-zero
sheets retain every supplied row and the real $0.00 total, without a toggle.
Absent sheets remain unknown, and missing denominations are never invented.
Large outcome strings wrap; named, keyboard-accessible tape/count regions
scroll internally when needed, preserving page reflow at 320 px.

What to look at shows all own leads, messages, levels, rule codes, and limits
when applicable. Whole-day leads remain separate. The two existing explanations
sit under More about this drawer with previews. Next drawer with leads uses
the unique drawer order from the active Results filters, never wraps, and hides
for an outsider or the final drawer. Back to results stays available and keeps
filters. All-drawers/day-link entries get Next only if they belong to that list.

## Python data and unchanged calculations

`shifts[].flags[]` and `shifts[].daily_flags[]` gain `limit_text`. R01, R04, and
R05 use the saved flag evidence. R08 uses its matching-window evidence and,
for mismatches, the report's saved review policy. Heuristics, record problems,
and unexpected deposits get no invented limit. Global flag objects, original
messages/evidence, core calculations, and all three reports are unchanged.

Nine parameterized cases check the policy wording, including a deliberately
different configuration to prove saved R01/R04/R05 evidence is respected.
The UI renders this Python wording directly. It performs no money or review
threshold calculations. Native count-row disclosure only checks supplied
quantities; no count totals are recalculated in JavaScript.

The fixed CSS/JS budget is preserved by reusing existing primitives and trimming
duplicate source comments already covered by DESIGN.md. Source remains readable.
No new framework, dependencies, persistence, review checkboxes, or resource caps
were added. Start and Prepare files remain their later blocks.

## Verification actually run

| Check | Observed result |
| --- | --- |
| `.venv/bin/pytest -q`, final run with local-socket permission | PASS: 727 tests in 13.81 seconds, including core/web/report parity, saved limits, count line totals, cleanup, contrast, packaging, and the unchanged combined-response-cap regression. |
| `.venv/bin/pytest -q tests/test_web.py tests/test_web_page.py` | PASS: 130 tests in 7.22 seconds after adding policy-limit and control/availability semantics coverage. |
| Both Ruff checks and `git diff --check` | PASS. |
| Chrome four-view matrix | PASS: all views at 320/1,280 x 900 in both themes, plus Results at 959/960 px. No page-wide overflow, page-error events, or outside resources; fonts loaded. |
| Every example drawer | PASS: all 60 human titles, browser titles, outcome strings, supplied row quantities/line totals, folding conditions, own messages, and input-tick availability agree with Python. |
| Next and return navigation | PASS: all nine review drawers, four Note-filtered drawers, a one-drawer date/Note filter, final no-wrap state, outsider/member entries from All drawers, a day-link outsider, full own/day context, keyboard Next, focus ring, breadcrumb return, and browser Back. |
| Zero-row button | PASS: keyboard Space expands/collapses the same controlled rows and updates aria-expanded. Source row counts and exact line totals are preserved. |
| Synthetic uploads | PASS: mixed zero/positive, all-zero, no-zero, absent count, missing POS, open drawer, and very large amounts. Overnight times preserve their calendar dates. Large tape content scrolls internally while the page stays within 320 px. |
| Long identities and multiple years | PASS: encoded drawer addresses, wrapping human titles/metadata, Next from 2026 to 2027, and no final wrap. |
| Reports and refresh | PASS: all three downloaded files under an active filter match the full Python report contents by SHA-256. Refresh returns to Start with the unsaved-results explanation. Forced-colors scrollbar fallback passed. |
| Generic premium strict audit | Same seven external-handler detection findings as earlier blocks, exit 1. These are not a clean static-audit pass. Existing handlers remain and block 3's full button checks are retained; example, upload, and report downloads were exercised again here. The new count toggle passed its browser checks. |
| Official DESIGN.md lint | Zero errors and one existing warning for Markdown-only format. Project tests check exact colour-token agreement and actual contrast pairs. |

An initial targeted test expected only the four Results previews; Drawer details
adds two more, and the test now covers all six. The policy and runtime checks
passed. One early focused tape capture landed at the top of the page. The
settled `tape-checked` capture verifies the intended target, allowing one pixel
for fractional scroll positioning; earlier images are retained.

## Budgets and raw evidence

| Resource | Measured value | Unchanged ceiling |
| --- | --- | --- |
| CSS plus JavaScript | 59,615 bytes | Under 60,000 bytes |
| Local WOFF2 fonts | 51,748 bytes | Under 200,000 bytes |
| Demo JSON with drawer limit labels | 161,185 bytes | 10,000,000 bytes |
| Combined allowed workload | 8,701,107 bytes, HTTP 200 | 10,000,000 bytes |
| Combined excessive detail | HTTP 400, bounded 136-byte error | Same response cap |

Only **385 bytes of code headroom** remain. Later blocks must continue to reuse
or simplify existing code rather than silently increasing the ceiling.

Raw records: [matrix](M10_BLOCK4_BROWSER.json),
[all-drawer and navigation checks](M10_BLOCK4_INTERACTIONS.json),
[seven synthetic cases](M10_BLOCK4_STATES.json),
[entry paths, keyboard, reports, and long titles](M10_BLOCK4_EXTRA.json),
[settled close-ups](M10_BLOCK4_CAPTURE_CHECKS.json),
[measurements](M10_BLOCK4_METRICS.json), and [static audit](M10_BLOCK4_AUDIT.json).

The [new dated folder](screenshots/2026-10-27-m10-block4/) contains 35 original
viewport PNGs: one initial 1,280 x 720 capture, seven input/count states, the
20-case matrix, five focused captures, and two settled tape/all-zero close-ups.
Use `tape-checked` for the focused tape view. Earlier folders were not changed.
Drawer layouts, input legends, count rows, unknown/large values, rule limits,
Next controls, and representative sibling views were visually inspected.

Verification used Playwright CLI 1.64.0-alpha with headless Google Chrome 156
against localhost. This block does not claim a new WebKit, browser-zoom,
OS-popup keyboard, real screen-reader, or unfamiliar-user usability pass.
The existing manual validation limits and broader final verification work
remain open. No new hosted CI or deployment result is claimed.
