# M10 block 5: Start

Authorized by "Start block 5" on 2026-10-27 and completed locally on
2026-10-28. The starting commit was `5d2d87f`, with a clean working tree.
Stop for `next` before block 6, Prepare files.

## Delivered

Start keeps its shared large title and example tape. A shorter lead explains
the comparison, followed immediately by Try the example and Upload demo CSVs.
The fictional month description follows those actions. The shared tape shows
six static input-availability ticks with a visible qualification that they do
not mean the drawer balances. Expected cash, counted cash, and difference
remain unticked; all real example figures and the definitions are retained.

A native ordered list explains Count, Compare, Review beneath the title/tape
group. It uses three columns when they fit and stacks on phones. Existing
typography, colours, topic/group spacing, buttons, and disclosures are reused.
The always-visible sleeping-server explanation is removed. The five-second
request message, 90-second browser timeout, Cancel, retry, and refresh recovery
remain owned by the unchanged JavaScript handler. README still explains the
host's first-visit delay.

The implementation changes the template and adds 255 bytes of CSS, with
page-contract test updates.
There are no JavaScript, server, arithmetic, rule, report, or resource-cap
changes. The nested process section is distinguished from app views in the
page-shell test, and drawer tick assertions are scoped to the drawer tape.

## Local verification

| Check | Observed result |
| --- | --- |
| Full Python suite | 728 passed in 13.54 seconds, including the existing response-cap and local Gunicorn socket tests. |
| Targeted page suite | 22 passed after the final test-selector cleanup. |
| Ruff and whitespace | Both Ruff checks and `git diff --check` passed. |
| Chrome matrix | 20 view/theme/width cases: four views at 320/1,280 px in light/dark plus Results at 959/960 px. No page overflow, page errors, or external resource requests; fonts loaded. |
| Changed Start layout | Both entry actions fit within the first 900 px at 320/1,280 px in both themes; each is at least 44 px high. Native step order and static input-only ticks checked. |
| Example and keyboard | Skip link first, main focus, example next, visible 3 px focus ring, Enter to real Results, and Results heading focus. Real response has 60 drawers and 18 leads. Tape definitions open and close. |
| Waiting and recovery | Actual five-second notice; duplicate Enter sends one request; Cancel restores action/focus and ignores a late success; 503 and network errors; actual retry button succeeds. Leaving pending Start for upload ignores the old response and focuses Prepare. |
| Timeout | Production DOM settings are 5,000/90,000 ms. A browser-only 100 ms timeout fixture exercises the existing timeout message and retry; this is not a measured 90-second wait. |
| Upload and refresh | Seven real bundled fake CSVs, upload Cancel, successful upload with 60 drawers/18 leads, and six drawer input ticks. Refresh from Results and Drawer returns to Start with the not-saved notice. |
| Media preferences | Static ticks have no animation. Forced-colour scrollbar fallback and reduced-motion preference checked. |
| Code/font budget | CSS/JS totals 59,870 bytes, under the unchanged 60,000-byte cap with 130 bytes remaining. Fonts total 51,748 bytes, under 200,000. |
| Generic strict audit | Same seven external-handler detection findings as earlier blocks, exit 1. This is not a clean audit pass; the existing controls have browser evidence, and no dummy attributes were added. |
| Official DESIGN.md lint | Zero errors and one existing warning for Markdown-only format. Project tests still verify colour-token agreement and contrast pairs. |

Raw results: [matrix](M10_BLOCK5_BROWSER.json),
[18 interaction cases](M10_BLOCK5_INTERACTIONS.json),
[ten final captures and metrics](M10_BLOCK5_FINAL_CAPTURES.json), and
[static audit](M10_BLOCK5_AUDIT.json).

## Screenshot history and limits

The 38 October 27 screenshots are retained in their original folder. Some
captured colours partway through an existing 150 ms theme transition. The
October 28 folder adds ten final captures after a 200 ms settling wait,
including four complete Start pages and focused process/waiting/retry states.
Use those settled images for final Start appearance. No earlier image is
overwritten, renamed, or deleted.

The first interaction harness used an incorrect expected timeout phrase and
stopped after the app correctly showed its existing message. Correcting that
expectation passed all 18 cases; the earlier captures remain. Initial page
tests also needed their view/tape scope updated, and Ruff formatting was fixed
before the final checks. These were verification adjustments, not app failures.

No new hosted CI, deployment, WebKit, zoom/text-resize, native popup keyboard,
screen-reader, or unfamiliar-user pass is claimed. The seven generic audit
findings and broader M10 block 7 verification remain open. Review checkboxes,
report restyling, Prepare redesign, and the remaining M9 rules are not included.
