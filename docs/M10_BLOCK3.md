# M10 block 3: grouped Results

Authorized by "go for block 3" on 2026-10-27. Completed locally.
Stop for `next` before block 4, Drawer details. No new push, hosted CI, or
deployment result is claimed.

## Delivered

The example's 18 leads now appear in nine unique drawers and two whole-day
date groups. Unfiltered sections are Needs review (four drawers), Whole-day
leads (two dates), and Check (five drawers). Empty sections are omitted;
a Notes-only upload shows its Note section. Counts come from Python.

Every drawer has a linked register/date title, one visible code to distinguish
same-register/date shifts, Python's exact difference/status, and its leads.
Each lead retains its own level and unchanged message. Drawers appear once,
ordered by highest own level, date, and code. Whole-day leads from any rule
group by date, retain rule codes in native disclosures, and link once to
existing drawers. Bank-only dates get no invented drawers or links.

Filtering happens before grouping. Matching drawers retain their unfiltered
order and highest overall level, so a Note on a Needs review drawer stays
findable. Filtered headings omit counts. Full run, report contents, Back,
breadcrumbs, heading focus, and encoded drawer addresses are preserved.
Unsupported filter keys, including inherited object names such as constructor,
normalize to All rather than displaying undefined wording.

Show, Keep a copy, and What the levels mean remain in the responsive side
column. More detail introduces four closed disclosures with plain previews:
lead totals, day totals, cashier totals, and all drawers. Tables still render
only when opened. No-leads runs hide the queue heading and filters while
keeping the qualified message, downloads, and access to all drawers.

One lead-row renderer serves grouped Results and Drawer details. The latter
keeps all own/day leads and rule codes; its existing page header supplies the
date/drawer context instead of repeating it on each row. This small shared-row
cleanup removes obsolete flat-list navigation branches and helps preserve the
code budget. Drawer title, tape, count sheet, next-drawer navigation, and
zero-row controls remain block 4 work. Core/server calculations and responses
are unchanged. No new dependencies, resource ceilings, or persistence were added.

## Verification actually run

| Check | Observed result |
| --- | --- |
| `.venv/bin/pytest -q`, final run with local-socket permission | PASS: 717 tests in 13.63 seconds, including core/web/report parity, resource cleanup, response caps, contrast, assets, and the new optional-detail preview/unit check. |
| `.venv/bin/pytest -q tests/test_web_page.py` | PASS: 20 tests in 0.54 seconds after the new preview test. |
| `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .` | PASS. |
| `git diff --check` | PASS. |
| Local Chrome matrix | PASS: all four views at 320/1,280 x 900 CSS pixels in light/dark, plus Results at 959/960 px in both themes. No page-wide overflow, page-error events, or outside resource requests. First drawer title and difference fit the 1,280 x 900 target. |
| Grouping and filters | PASS: exact nine-drawer/two-date grouping and all 18 messages; Python amount/status strings preserved; 48 date/level combinations checked for unique grouping, order, overall level, no matches, unchanged Full run, and no filtered section counts. |
| Navigation | PASS: Note on Needs review drawer, all own leads on Drawer details, visible title focus ring, keyboard Enter, browser Back, breadcrumb restoration, invalid filter normalization, missing-drawer recovery, and long encoded drawer addresses. |
| Optional detail | PASS: all three tables start empty, fill with the response's rows when opened, and remain behind native disclosures. Whole-day rule disclosure opens to its code. |
| Synthetic uploads | PASS: clean, only Notes, non-bank whole-day R09, bank-only, zero/absent/open counts, balanced amounts with record leads, and long identifiers with multiple years. The duplicate-closing case retains two unique drawers and visible codes. |
| Downloads and recovery | PASS: all three downloads under an active Note/date filter match the full Python response contents by SHA-256. Both busy/Cancel flows, simulated 503 followed by a real retry, fresh reduced-motion rendering, forced-colors scrollbar fallback, and refresh recovery passed. |
| Generic premium strict audit | Same seven known external-handler detection findings as earlier blocks, exit 1. Each button has its actual handler in app.js and was exercised; this is not a clean static-audit pass. |
| Official DESIGN.md lint | Zero errors and one warning for the existing Markdown-only format. Project tests check exact colour-token agreement and contrast. |

An initial page-budget check failed while the new grouping and old flat-list
code coexisted. The shared renderer and redundant-branch cleanup restored the
unchanged budget; the final suite passes. Browser-harness corrections waited
for native disclosure toggle events and selected a unique first group for
captures. Neither required changing table behavior or weakening assertions.

## Budgets and evidence

| Resource | Measured value | Unchanged ceiling |
| --- | --- | --- |
| CSS plus JavaScript | 59,443 bytes | Under 60,000 bytes |
| Local WOFF2 fonts | 51,748 bytes | Under 200,000 bytes |
| Demo JSON | 159,958 bytes | 10,000,000 bytes |
| Combined allowed workload | 8,620,061 bytes, HTTP 200 | 10,000,000 bytes |
| Combined excessive detail | HTTP 400, bounded 136-byte error | Same cap |

The code budget has **557 bytes of headroom**. Later blocks must simplify or
reuse existing code as needed; do not raise the ceiling without an explicit
scope decision.

Raw records: [browser matrix](M10_BLOCK3_BROWSER.json),
[grouping/filter/navigation checks](M10_BLOCK3_INTERACTIONS.json),
[seven upload cases](M10_BLOCK3_STATES.json),
[downloads and recovery](M10_BLOCK3_RECOVERY.json),
[address cases](M10_BLOCK3_ADDRESSES.json),
[measurements](M10_BLOCK3_METRICS.json), and [static audit](M10_BLOCK3_AUDIT.json).

The [dated screenshot folder](screenshots/2026-10-27-m10-block3/) contains
34 original viewport PNGs: an initial 1,280 x 720 capture, the 20-case matrix,
seven narrow upload states, and six focused captures of grouped leads,
whole-day code access, More detail, a mixed-level Note, and a settled clean
summary. Some early captures include the one-time tick animation; clean-settled
shows its completed state. Earlier folders were not changed. Changed Results,
edge states, disclosures, and representative sibling views were visually
inspected in addition to geometry checks.

Checks used Playwright CLI 1.64.0-alpha and headless Google Chrome 156 against
localhost. This block does not claim a new WebKit, browser-zoom, OS-native popup
keyboard, real screen-reader, or unfamiliar-user usability pass. Those broader
checks remain in the later verification work and the existing manual limits
carry forward. No new hosted CI or deployment result is claimed.
