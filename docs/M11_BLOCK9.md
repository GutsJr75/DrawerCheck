# M11 block 9: End-to-end verification and handoff

Authorized on 2026-11-04 by the user's "you do that, then go for block 9"
after reviewing block 8. Started from `039a135` with a clean working tree.
Completed locally. M11 stops here; M12 is not started.

## Block 8 follow-ups

Two small points from the block 8 review, done first at the user's request:

1. **Plan wording:** M11_PLAN.md read "and the recount, and the closing
   sheet"; the extra "and" is removed.
2. **Readable times on the closing sheet:** opened and closed now read like
   Review, for example "Monday, November 2, 2026, 08:00", instead of
   `2026-11-02T08:00:00`. Python builds them from the date labels it already
   sends. The committed sample was regenerated (only those two lines changed),
   and a new test fails if the sample ever drifts from the generator.

## One fix found by the checks

**The entry count sheet did not fit enlarged text on a narrow screen.** At
200% text in a 320 px window, the Close a drawer count sheet (and the recount
sheet, which shares it) was 478 px wide in a 240 px space. Every count box sat
off to the right, inside an area that scrolled sideways but was not a named
region. The first run of the text and reflow matrix passed, because it only
treated hidden overflow as a problem; reading the screenshot showed the gap.

Fix: the entry sheet is now a size container. When it is narrower than
12.5rem, which grows with the text, each line stacks its label above its box
and the caption becomes a normal block. Normal text keeps the two-column
sheet from block 5 at 320 px. The matrix now also reports any sideways
scrolling area that is not a named region, and stacking is checked directly.
The pre-fix capture is kept in the screenshot folder, labelled "unstacked".

## Checks

| Check | Result |
| --- | --- |
| Python and web tests | 824 passed, 12 opt-in browser tests skipped; with browser tests enabled, 836 passed |
| Ruff | Both checks pass |
| Committed browser tests, Chrome 156 and WebKit build 2370 | All 12 cases pass: uploads, Close messages, Review and sign-off, recount, closing sheet, and the new end-to-end test. WebKit is named with `DRAWERCHECK_WEBKIT_EXECUTABLE`, an unofficial pairing with Playwright 1.65 |
| End-to-end (new `tests/browser/drawer_end_to_end.cjs`) | Keyboard: Space picks a choice, Enter submits from a field, summary links followed with Enter (Option+Tab in WebKit, as in Safari). Refresh clears the result and every entry. Cancel on Close and on Review keeps entries or the sign-off and ignores the late reply. A network failure and a server error each offer Try again without losing entries. IDs that look like markup stay text on Review and in the closing sheet. Add a drop stops at 20 |
| Text size and reflow | 96 checks: six states (Close empty and with problems, Review result and recounted, both closing sheets), both engines, both themes, at normal text 320 px, 200% root text at 1,280 x 900, 320 x 200 reflow, and 200% text at 320 px. No page overflow, no clipped content, no unnamed sideways scrolling ([results](M11_BLOCK9_REFLOW.json)) |
| Accessibility | 128 axe-core 4.14.0 scans of every M11 page state and both closing sheets, both engines, both themes, 320 and 1,280 px: no violations. Colour contrast was incomplete only where the drawer tape shows, as in M10 ([results](M11_BLOCK9_AXE.json)) |
| Limits and safe rendering | Server limits (32 KiB body, amounts, quantities, 20 drops, 256 characters, JSON shape) are covered by the block 4 tests, which pass. Escaping is covered by Python tests for the sheet and the new browser test for Review |
| Existing full-run report | Byte-identical to `babde22` for the same demo data and timestamp (checked during the block 8 review) |
| Budget | CSS and JavaScript total 79,117 of 90,000 bytes |

## Performance

Measured with the block 5 script and conditions (Chrome 156 headless through
Playwright 1.65, Apple M1 8 GB, macOS 27.2, loopback without throttling, a
fresh browser context per run, the server already running and warmed).

The first comparison against the block 5 baseline looked much slower
([file](M11_BLOCK9_PERF.json)), in milliseconds:

| Timing | Block 5 baseline | Block 9 first run | Change |
| --- | ---: | ---: | ---: |
| Start to DOMContentLoaded | 30.8 | 49.5 | +60.7% |
| Start to load event | 61.4 | 105.1 | +71.2% |
| Try the example to Results visible | 92.2 | 133.5 | +44.8% |
| Drawer link to Drawer details visible | 13.3 | 10.9 | -18.0% |

That crossed the 20% trigger, so the block 5 baseline code (`b474088`) and
the current code were measured side by side in eight alternating rounds
([repeats](M11_BLOCK9_PERF_REPEATS.json)). The machine was busier than in
block 5 (load average about 6 from other desktop apps), and the unchanged
baseline code slowed by the same amount. Pooled medians of 40 runs each:

| Timing | Baseline code | Current code | Change |
| --- | ---: | ---: | ---: |
| Start to DOMContentLoaded | 40.8 | 39.4 | -3.4% |
| Start to load event | 79.3 | 81.0 | +2.1% |
| Try the example to Results visible | 129.8 | 133.8 | +3.1% |
| Drawer link to Drawer details visible | 11.3 | 11.3 | 0% |

Conclusion: no slowdown attributable to M11 in these local runs. The first
numbers are kept because they show why a single comparison across different
days can mislead.

## Not verified

- **Participant testing:** nobody unfamiliar with the project has tried the
  walkthrough or the pages. Nobody was contacted. This is the most important
  open check.
- **Real screen reader:** no VoiceOver or other screen reader was used.
  Accessibility-tree and axe checks do not prove what is spoken.
- **Actual browser zoom at 400%:** not done; root text at 200% and narrow
  reflow are related but different checks.
- **Hosted CI and the public site:** the user pushed M11 up to `56a99b8`
  (blocks 1 to 5 and the block 5 repair); blocks 6 to 9 are local. No CI run
  or live check has been observed for any M11 commit, so none is claimed.
- **WebKit pairing:** WebKit build 2370 with Playwright 1.65 is unofficial.
  Installing the matching build (`npx playwright install webkit`) would make
  the default WebKit launch work.

## Screenshots

[2026-11-04-m11-block9](screenshots/2026-11-04-m11-block9/): closing sheets
with readable times (light and dark at 1,280 px, light at 320 px, missing
report), the count sheet at 200% text in a 320 px window before and after
stacking, the recount sheet stacked, Review at 200% text at 1,280 px, and
Review recounted in a 320 x 200 window in dark mode.
