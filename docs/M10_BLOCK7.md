# M10 block 7: final local verification

Hosted follow-up, 2026-10-28: CI and public checks now pass for `62650f9`,
including both fixes. See [hosted evidence](M10_BLOCK7_HOSTED.md). The local
delivery record below preserves its earlier pending-publication status.

Authorized by "Go for it" on 2026-10-28 after the block 6 summary named final
verification. Started from `17875c1` with a clean working tree. Local checks
and documentation are complete. Publication and hosted verification of the
two fixes below remain pending, along with the explicit manual gaps in the
[M10 checklist](M10_CHECKLIST.md). No push or deployment was performed.

## Two defects found and fixed

The drawer tape put role=region on a figure, which fails axe's allowed-role
rule. A named, keyboard-focusable div now owns scrolling and contains the
original semantic figure/caption. A page-contract assertion guards that
wrapper. Both engines can focus it and scroll a large fake tape by keyboard.

Chrome widened the 320 px page to 332 px when full-run lead counts were
expanded. Adjacent nowrap inline spans had no reliable break opportunity.
Making each severity chip an inline block keeps each label/count together
and lets chips wrap between one another. Data tables still scroll within
their named regions. No JavaScript, arithmetic, rule, or report change.

Initial scans retain 56 allowed-role violations and Chrome's narrow overflow.
The final matrix repeats the same 27 states with neither defect detected.

## Final local evidence

| Check | Observed result |
| --- | --- |
| Regression suite | 729 passed in 15.01 seconds after both fixes. Page suite: 23 passed. Both Ruff checks and git diff --check pass. |
| Accessibility | 216 final axe-core 4.14.0 scans: 27 states in Chrome 156.0.8078.48 and WebKit 26.6, light/dark, 320/1,280 px. Zero detected WCAG 2.0/2.1/2.2 A/AA or best-practice violations. Color-contrast incomplete results are retained; token contrast tests supplement them, not full certification. |
| State coverage | Start, missing/ready/problem/failed/waiting files, Start waiting/timeout, Results plain/Note/no-match/open detail, drawer plain/expanded zeros, missing drawer, clean/only-Notes/bank-only/balanced-problem/long runs, all-zero/absent-count/missing-POS/open drawers, and unsaved refresh. |
| Geometry | No final scan has page overflow. Both engines also pass Results at 959/960 px and long identifiers/multi-year labels. |
| Text and reflow | Four views in both themes and both engines: 200% root text at 1,280 x 900 and separately 320 x 200 reflow. No page overflow or detected clipping. These are 32 resize/reflow checks, not an actual 400% browser-zoom pass. |
| Keyboard/live feedback | Enter opens the example and focuses Results; live region says Results are ready. Native radio arrows, disclosure Space, count toggle Space, summary focus/error-link Enter, and named table/tape scrolling work. WebKit moved horizontally on a second Right arrow and by a page with Option+Right; the first recorded arrow alone left scrollLeft at zero. |
| Drawer navigation | All 60 exact demo outcomes/count rows/input ticks and full/Note-filtered Next order checked in both engines. No wrapping at the final drawer; Back preserves filters. |
| Media preferences | Reduced-motion shows static ticks and removes transitions. Forced-colour emulation is active in both engines and uses system scrollbar colours. |
| Parity | Pre-M10 snapshot fc4f3ce versus the current working tree: all 60 complete shift records agree after excluding new limit_text; all 18 global flag records agree; all three report objects agree for the captured comparison. Generated report timestamps naturally differ across later runs, so hashes are capture-specific. |
| Units and counts | 60 drawers, nine with leads, four highest-level Needs review, 16 drawer leads and two whole-day leads on two dates, 51 without own leads. All amounts remain Python-owned. |
| Budgets | CSS/JS 59,987 bytes with 13 bytes remaining below 60,000; fonts 51,748 below 200,000. Demo JSON 161,185 bytes. Combined capped workload 8,701,107 bytes; excessive aggregate details return 400 with a 136-byte bounded error. No cap increase. |
| Security/resources | Local pages request only localhost in the scanned runs. Existing CSP, safe DOM insertion, isolation/cleanup, CSV protection, and response-cap regression tests pass. Expected mocked 400/503 console errors are recorded. WebKit retains its known native-select inline-style CSP warning; protections were not weakened. |
| Static tooling | Generic strict audit still reports seven external-handler detection findings, exit 1. Actual controls have browser evidence; no dummy attributes added. Official DESIGN.md lint has zero errors and one existing Markdown-only warning. |

Raw files: [summary](M10_BLOCK7_SUMMARY.json),
[parity](M10_BLOCK7_PARITY.json), [budgets](M10_BLOCK7_METRICS.json),
[Chrome drawer checks](M10_BLOCK7_CHROME_DRAWERS.json),
[WebKit drawer checks](M10_BLOCK7_WEBKIT_DRAWERS.json),
[Chrome text/keys](M10_BLOCK7_CHROME_RESIZE_KEYS.json),
[WebKit text/keys](M10_BLOCK7_WEBKIT_RESIZE_KEYS.json),
[WebKit native table scrolling](M10_BLOCK7_WEBKIT_SCROLL.json),
[Chrome fixes/media](M10_BLOCK7_CHROME_FOCUSED.json),
[WebKit fixes/media](M10_BLOCK7_WEBKIT_FOCUSED.json), and
[static audit](M10_BLOCK7_AUDIT.json). The eight M10_BLOCK7_AXE files hold final
scans; eight INITIAL_AXE files preserve the findings before repair.

## Hosted evidence, separate from local fixes

Observed [GitHub Actions run 40664015982](https://github.com/GutsJr75/DrawerCheck/actions/runs/40664015982)
for `17875c1`: Python 3.12, 3.13, and 3.14 jobs passed, including Ruff and
optional web/server steps. The connected run-list wrapper filters to PR runs,
so the push run was retrieved through GitHub's public API; its job details
came from the connected GitHub tool. See [run](M10_BLOCK7_CI_RUN.json) and
[jobs](M10_BLOCK7_CI_JOBS.json). This does not test unpublished block 7 fixes.

The already published site's CSS/JS hashes exactly match block 6. Its real
example and seven bundled fake CSV upload returned 200, 60 drawers, and 18
identical flag records. The worked drawer shows -$20.00; all three report
downloads match their response hashes. HTML opened in Chrome; CSV parsed
as 19 rows including its header; text opened as UTF-8. Refresh recovered to
Start. See [live smoke checks](M10_BLOCK7_LIVE.json). Asset matching is not
a separate observation of Render's backend commit identifier.

Block 7 changes the tape wrapper and stylesheet locally. After the user
publishes this commit, inspect its own CI, compare deployed assets, and repeat
the public smoke checks. No hosted success is claimed for these local fixes.

## Manual gaps and capture history

Actual browser zoom remains unverified: native computer-use app calls timed
out twice with timeoutReached (-10005). Earlier M8 automation used a 320 x 200
viewport plus device scale factor 4, which emulates reflow rather than actual
browser zoom. M8_CHECKLIST.md and WEB_PLAN.md now carry that correction.
No real screen-reader speech or new-participant usability check was performed.

All 136 dated screenshots remain in the new block folder. Use fixed for the
final accessibility repair matrix and focused count/tape shots; verified text200
and reflow320x200 show their separate layout checks. Live-before-fixes captures
show the published block 6 runtime, not an unpublished deployment. Initial
verified captures and initial resize images are retained rather than replaced.

Harness corrections are explicit: the original no-match date also had a
single-bill Note, so the final fixture chooses a date without Notes from the
payload. Drawer assertions wait for the requested route to render. Keyboard
checks start from a closed disclosure and reset a filter through a visible
path. The exported brand is uppercased by CSS, so report opening checks its
actual heading. These changes fix test assumptions, not product behavior.

Pinned axe-core was downloaded only into temporary QA tooling and its SHA-512
verified. No Node runtime dependency or outside asset request was added to
the project. Review checkboxes, report restyling, R06, and R07 remain outside
this block. Stop for next before any further milestone work.
