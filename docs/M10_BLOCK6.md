# M10 block 6: Prepare files

Authorized on 2026-10-28 by "Go for it" after the block 5 summary named
Prepare files as next. Started from `0779a1f` with a clean working tree.
Completed locally. Stop for `next` before block 7.

## Delivered

Prepare files now has two native numbered steps: Add the seven files, then
Check the files. The normal Choose files input sits inside a dashed drop
area. Selection and drops share addFiles, which keeps file objects by their
required names and replaces a same-named file. It never reads CSV contents
or submits a check automatically.

One compact ruled sheet shows each filename, written state, Ready size/tick,
purpose, and Example download. Each download's accessible name includes its
filename. Ready means added; a sentence beside checking explicitly separates
this from checking contents. Problem rows retain the complete server error
and lose the tick. Under Check my files, the live progress sentence lists
missing filenames or asks for correction when a chosen file has a Problem.
The button refers to that progress text with aria-describedby.

Prepare reuses Results' grid, now named work-layout/work-main. At 960 px the
short help note and two native disclosures sit beside the steps; below that
they follow both steps in reading order. File sizes can wrap under Ready on
phones, keeping every filename on one line in the checked widths. Long
filenames and errors wrap inside the page. Multiline error links align with
their first-line bullet. Existing chooser, row, button, and summary focus
behavior remains in place.

The implementation keeps the existing chosen-file map, request handler,
server importer, money calculations, rules, reports, and all resource limits.
Two new progress strings live in errors.py and reach the template through
CLIENT_MESSAGES. No result-response fields change. To retain the strict
60 KB code budget, remove unused legacy link/narrow-view styles and redundant
high-level comments already explained in WEB_PLAN.md; retain and clarify
comments explaining browser/focus behavior.

## Local verification

| Check | Observed result |
| --- | --- |
| Python | Final full suite: 729 passed, including existing caps, cleanup, packaging, and local server socket coverage. The page suite passes 23 tests. |
| Ruff and whitespace | Both Ruff checks and `git diff --check` passed. |
| Shared layout | 20 cases cover all four views at 320/1,280 px in light/dark and Results at 959/960 px. No page overflow, page errors, or external resources; fonts loaded. |
| Prepare layout | Eight empty cases at 320/959/960/1,280 px in both themes verify step order, help placement, dashed border, seven named links, and initial hidden ticks. Eight final Ready cases keep every filename on one actual text line and show seven ticks without page overflow. |
| File paths | Partial drag/drop and native-input selection merge into the same map. Wrong-case names produce rename guidance; unknown names remain literal text, including a markup-like filename. Same-name correction restores Ready. Empty selection preserves chosen files, and the input clears for repeated selection. |
| Keyboard chooser | Separately focused the native input, measured its label's 3 px ring, pressed Space to open the chooser, and used CLI upload to select two bundled fake files. The page reported two Ready and the five missing filenames. This is not OS-dialog visual/usability testing. |
| Missing files | Empty Check sends no request, lists seven missing files, focuses the summary, and links to the correct row with a 3 px ring. Partial selection lists only missing names below the check button. |
| Real file problems | A malformed shifts.csv header returns 400 with source line 1, marks that row Problem, removes its tick, reports six Ready, and focuses the summary. Its link focuses the offending row. Replacing that file clears the problem. |
| Long errors | A 300-character unknown filename wraps. Separate real 400 responses cover a 400-character field exceeding the 256-character limit and a 240-character invalid money value reaching the money parser. Long summary/row errors stay inside 320 px and keep error-link focus. Correcting shifts.csv succeeds. |
| Size limit | A batch containing a 2,097,153-byte file fails the existing combined precheck without a request; the summary link focuses the native input. The 2 MiB cap is unchanged. |
| Waiting/retry | Real five-second slow notice, duplicate Enter sends one request, Cancel restores focus/action and chosen files, 503 shows inline retry rather than a file error, and the actual retry button succeeds. |
| Real upload | Bundled seven-file fake upload and corrected error upload each return 60 drawers and 18 leads. Results heading receives focus; returning to Prepare keeps chosen files. Refresh clears the browser's file map. |
| Example downloads | All seven named links produce the expected filenames. Saved download SHA-256 values match the corresponding generated fake CSV content. |
| Media/help | Both optional disclosures work; static ticks have no animation; reduced-motion removes button transitions and forced colours use the system scrollbar. |
| Budgets | CSS/JS totals 59,975 bytes, below 60,000 with 25 bytes remaining. Fonts remain 51,748 bytes, below 200,000. The response caps and financial calculations are unchanged. |
| Static audit | Same seven external-handler detection findings as prior blocks, exit 1. These are not a clean static-audit pass; existing actions have real browser evidence and no dummy attributes were added. |
| Official DESIGN.md lint | Zero errors and one existing Markdown-only warning. Project tests verify exact colour-token agreement and contrast pairs. |

Raw evidence: [shared matrix](M10_BLOCK6_BROWSER.json),
[empty layout](M10_BLOCK6_LAYOUT.json),
[20 file/recovery interactions](M10_BLOCK6_INTERACTIONS.json),
[native keyboard chooser](M10_BLOCK6_NATIVE.json),
[field-limit edges](M10_BLOCK6_EDGE.json),
[money-parser edges](M10_BLOCK6_EDGE_MONEY.json),
[final Ready layout](M10_BLOCK6_READY.json), and
[static audit](M10_BLOCK6_AUDIT.json).

## Capture history and limits

All 67 captures are retained in the dated October 28 folder. Use ready-final for
the final Ready layout and long-error-money-240 for the final wrapping/error
states. Empty-complete and the checked shared-view matrix show the remaining
views. Initial captures remain for the timeline.

The first matrix helper needed its generic main selector scoped to Results
after that layout became shared. A scripted chooser batch was interrupted by
the CLI's modal handling, so native keyboard activation was checked separately
with press/upload, and the rest of the batch uses native input selection.
A long-error check initially saw the old stylesheet through same-document
navigation; a real reload verified the updated styles. The final filename
check measures text rectangles rather than the stretched grid-cell height.
These harness adjustments and initial captures are retained without being
presented as clean first attempts.

No new hosted CI, deployment, WebKit, browser zoom/text-resize, screen-reader,
OS-dialog usability, or unfamiliar-user pass is claimed. These checks do not
constitute full accessibility certification. Cross-view verification and its
hosted follow-up remain block 7. Review checkboxes, report restyling, and the
remaining M9 rules are not included.
