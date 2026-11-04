# M11 block 8: Offline closing sheet

Authorized on 2026-11-04 by "Go for block 8". Started from `babde22` with a
clean working tree. Completed locally. Stop for `next` before block 9.
Nothing was pushed or deployed.

## Delivered

Review has a secondary **Download closing sheet (.html)** action below check
coverage. `POST /api/drawer` embeds the complete file in `closing_summary`
with its filename and media type. The browser reuses the existing download
helper; it does no cash arithmetic. Editing any entry hides the result and
download until a fresh check succeeds. Earlier files remain snapshots of
their own check, with a reminder to download again after changes.

The sheet includes:

- Shift identity, real supplied times, starting cash, report figures, and
  individual safe drops with their total.
- Expected cash, counted cash, difference, status, and the written formula.
  A recount keeps both count sheets and a comparison against the same
  expected cash. Leads and coverage belong to the selected count.
- Review leads with their limits; checks that ran, checks that did not run,
  and the records check's checked/unavailable details.
- Supplied verifier ID and note, explicitly unverified, plus the example
  settings and UTC generation time. Reviewed and balanced remain separate.
- A fictional-data banner, offline/Print instructions, and the boundary
  between a downloaded snapshot and saved history.

`reports/closing_sheet.py` renders the same formatted Python values as
Review. It does not rerun calculations or rules. The existing HTML report's
inline CSS and escaped semantic-table helper are shared, with extra print
styles confined to the closing sheet. Every dynamic HTML value is escaped.
The file contains no script, external resource, form, or network dependency.
No CSV export, dependency, persistence, or resource limit changed.

The committed [sample closing sheet](../examples/sample_closing_sheet.html)
shows case B: first count $665.65 and -$20.00, recount $685.65 and $0.00,
both compared with $685.65 expected cash. Its fictional note describes the
additional $20 bill. Opening the HTML file locally gives the intended view;
GitHub displays its source.

## Verification

- **Full suite with browser checks enabled:** 833 passed. Both Ruff checks,
  JavaScript syntax checks, local Markdown links/anchors, and
  `git diff --check` passed.
- **New Python coverage:** balanced, short, and missing-report cases;
  zero recount versus unknown difference; both count sheets; supplied
  reviewer details; malicious-looking IDs, bags, and multiline notes;
  offline markup, timestamp, print styles, and independent snapshots.
- **Browser coverage:** all ten committed browser cases passed in Chrome
  156 and WebKit build 2370. The new closing-sheet case enters case B,
  downloads before/after sign-off and recount, checks stale-result hiding,
  opens the actual saved `.html` offline, verifies print styles and zero
  external requests, then downloads a missing-report result. WebKit 2370
  was explicitly selected with `DRAWERCHECK_WEBKIT_EXECUTABLE`, an
  unofficial pairing with Playwright 1.65. No browser was installed.
- **One intermediate repeat:** 832 passed and the existing Chrome review
  test failed while launching Chrome, before application assertions. The
  final repeat ran without other browser work and passed all 833 tests.
- **Existing reports:** report tests passed. A one-off comparison using the
  same generated demo data and timestamp found the full-run HTML identical
  byte for byte to `babde22` after exposing its shared CSS/table helpers.
- **Accessibility:** 24 offline-sheet scans and 16 app download/stale scans
  across both engines, both themes, 320 and 1,280 px found no violations.
  Offline sheets had no incomplete results. The eight app result scans
  retained the existing drawer-tape colour-contrast incomplete result; stale
  scans had none. [Raw results](M11_BLOCK8_AXE.json), axe-core 4.14.0.
- **Static UI audit:** [seven baseline findings](M11_BLOCK8_AUDIT.json)
  remain for old controls wired in external JavaScript. No new finding was
  added. This is not a clean static-audit pass; browser checks verify the
  actual download and existing flows.
- **Layout and print:** offline sheets fit 320 and 1,280 px without document
  overflow in both engines/themes. Chrome's A4 PDF was rendered with native
  PDFKit and inspected page by page. An initial five-page print split the
  count table and check descriptions; compact print spacing and break rules
  keep them together in the final four-page sample. No clipping or missing
  count lines was seen. This verifies PDF output, not a physical printer or
  the native Print dialog.
- **Asset budget:** every static CSS/JS file totals 78,617 of 90,000 bytes.
  No budget increase. The block 5 performance comparison waits for block 9.

Not checked here: a real screen reader, actual browser zoom, an unfamiliar
participant, hosted CI, or the public site. Local passes do not establish
those results. Block 9 is still required.

## Screenshot timeline

[2026-11-04-m11-block8](screenshots/2026-11-04-m11-block8/) contains 22
captures: nine app/offline-screen views and thirteen print-page images.
Chrome screen captures show the download action, stale result, short and
missing-report sheets, and a recount sheet in both themes and widths.

Print captures retain the initial five pages and the first four-page print
revision. Use **sheet-print-sample-page1** through **page4** for the final
committed sample with its corrected recount note. The `714` print filename
width is logical rendering width; PDFKit's 2x PNG backing is about 1,430 px.
Older captures were not overwritten, renamed, or removed.
