# M10 block 7: hosted verification

Completed on 2026-10-28 after the user requested "do block 7". Local fixes
were committed as `62650f9`; this follow-up verifies that published runtime.
The checkout and origin/main matched `62650f9b08f98fc05d2b6ebcfba38642c3e9b552`
at the start, with a clean tree. This record changes documentation/evidence
only. The agent did not push, deploy, or begin the remaining M9 rules.

## Observed results

| Check | Result |
| --- | --- |
| GitHub CI | [Run 40706484429](https://github.com/GutsJr75/DrawerCheck/actions/runs/40706484429) succeeded for 62650f9. Python 3.12, 3.13, and 3.14 jobs passed, including Ruff, tests, installed command, and optional web/server steps. |
| Published assets | app.css is 23,345 bytes and app.js is 36,642 bytes; both SHA-256 values match the checkout. Public HTML contains the named tape div and no region role on its figure. |
| Render wake-up | Initial browser navigation showed Render's loading page with 503. The loaded app subsequently returned 200; checks below ran against it. This differs from the app's own check-waiting notice. |
| Example | Both engines returned 200, 60 drawers, nine with leads, 16 drawer leads, two whole-day leads, and 18 total flags. |
| Expanded counts | Fixed count chips stay within the page at 320/1,280 px in light/dark in both engines. |
| Drawer region | A named, focusable DIV region contains the figure. Expected, counted, and difference remain $518.75, $498.75, and -$20.00. |
| Focused accessibility | Eight scans per engine: expanded Results and Drawer, both themes and widths. All 16 detect zero WCAG A/AA or best-practice violations and zero page overflow. Incomplete results remain in the raw records; this is not full certification. |
| Fake upload | Seven bundled fictional CSVs show seven Ready and return 200, 60 drawers, and the same complete 18 flags as the example in each engine. |
| Reports | HTML, CSV, and text download in both engines. Saved SHA-256 values match each response. HTML renders its heading, CSV parses as 19 rows including its header, and text opens as UTF-8. Hashes are capture-specific because report timestamps vary. |
| Refresh/resources | Refresh returns to Start with the not-saved notice. Both runs have only drawercheck.onrender.com request hosts, preserved CSP, and no page JavaScript errors. |
| Local checks | 729 tests passed in 14.83 seconds; both Ruff checks and git diff --check passed. No runtime source changed. |

Browsers: Chrome 156.0.8078.73 and WebKit 26.6. Pinned axe-core 4.14.0 runs
only as temporary QA tooling. No application dependency was added.

Asset hashes:

- app.css: `594443575a4747261cb3d5882b2e92cc7d6647d237686adf9253d80b3b5c8639`
- app.js: `dd1d624817ec70c8c48d61cbd66c10812af2af9288650781bc930883def321ca`

This verifies deployed presentation and observed behavior. Render's backend
commit identifier was not independently exposed or read. Hosted CI applies
to runtime 62650f9, not this later documentation-only evidence commit.

## Evidence and remaining checks

[CI run](M10_BLOCK7_HOSTED_CI_RUN.json),
[CI jobs](M10_BLOCK7_HOSTED_CI_JOBS.json),
[asset/markup comparison](M10_BLOCK7_HOSTED_ASSETS.json),
[Chrome](M10_BLOCK7_HOSTED_CHROME.json), and
[WebKit](M10_BLOCK7_HOSTED_WEBKIT.json) contain the raw results.
Twelve screenshots are in the new dated hosted folder and
[timeline](screenshots/README.md); no earlier captures were overwritten.

Implementation, local QA, and hosted follow-up are now recorded. Actual 400%
browser zoom, real screen-reader speech, and first-time-user usability remain
unverified in the [M10 checklist](M10_CHECKLIST.md). The seven known generic
static-audit handler-detection findings remain documented in the local record.
No full accessibility claim is made.

M9 R06 is next, followed by R07, each requiring separate authorization.
Stop for next after the local evidence commit.
