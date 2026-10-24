# Screenshots

Screenshots of the website, kept as a timeline so progress is easy to see.
Every image shows fictional demo data only.

## How they are organised

- Each work block gets its own folder, named
  `<YYYY-MM-DD>-<milestone>-<block>`, using the date the screenshots were taken.
- Each file starts with the same date and label, then the view, the state if
  any, the theme, and the window width in pixels:
  `2026-10-23-m8-block2-prepare-missing-light-320.png`.
- Earlier folders are never changed or deleted. A later block that needs new
  pictures of an old view gets them in its own new folder.

## Timeline

| Folder | Taken | What it shows | How |
| --- | --- | --- | --- |
| [2026-10-23-m8-block1](2026-10-23-m8-block1/) | 2026-10-23 | The page layout: demo notice, heading, and footer, before any views existed | Headless Firefox 158 screenshots of the local app |
| [2026-10-23-m8-block2](2026-10-23-m8-block2/) | 2026-10-23 | Start with the example tape and its help, and Prepare files when empty, with missing files, and with a server error on one file | Headless Firefox 158 driven through WebDriver BiDi, light and dark |
| [2026-10-23-m8-block3](2026-10-23-m8-block3/) | 2026-10-23 | Results with the plain-facts line, leads, and the day and cashier tables; Drawer details for `2026-09-03-R1` with a definition open; the uncounted drawer `2026-09-25-R1`; and a drawer with a whole-day deposit lead from an upload missing September 3's deposit | Headless Firefox 158 driven through WebDriver BiDi, light and dark |
| [2026-10-23-m8-block3-repair](2026-10-23-m8-block3-repair/) | 2026-10-23 | After the block 3 review repair: the balanced drawer with a "Needs review" label now fitting 320 px, a counted drawer on an incomplete day with the corrected deposit sentence, and the error summary with spaced 24 px links | Headless Firefox 158 driven through WebDriver BiDi with real mouse and keyboard input, light and dark |
| [2026-10-23-m8-block4](2026-10-23-m8-block4/) | 2026-10-23 | Results filtered by date and level with drawer links on a whole-day lead (1,280 and 320 px), the All drawers table, a drawer opened from a day link, the missing-drawer view, Start after a refresh ("Results are not saved"), and Start while waiting and after the time limit | Headless Firefox 158 driven through WebDriver BiDi with real mouse input and deliberately slowed responses; light, with dark for three views |
| [2026-10-23-m8-block5](2026-10-23-m8-block5/) | 2026-10-23 | The final views for the accessibility check: Start, Prepare files with a file problem, Results, and Drawer details at 1,280 and 320 px in light and dark (Chrome); the same four views at 390 px in WebKit, Safari's engine; Results and Drawer details at 400% zoom; and Results and Drawer details with text at 200%. Correction: the WebKit Results and Drawer details files at 390 px both show Start by mistake; the block 5 repair folder has the real views | Playwright 1.64 driving Google Chrome 156 and WebKit 26.6 |
| [2026-10-24-m8-block5-repair](2026-10-24-m8-block5-repair/) | 2026-10-24 | Corrected WebKit pictures: Results and Drawer details for `2026-09-03-R1` at 390 px, and the same two views at 400% zoom | Playwright 1.64 driving WebKit 26.6; each picture taken only after the script confirmed the expected view and address |
