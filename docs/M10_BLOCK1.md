# M10 block 1: shared Tick and tie design

Authorized by the user on 2026-10-26 after the finalized redesign proposal.
Completed locally. Stop for `next` before block 2, Results summary and layout.
No new push, deployment, or hosted CI result is claimed.

## What changed

The existing four views now share the approved ledger-green paper, blue-pen
actions, graphite Notes, Atkinson text/money fonts, larger responsive titles,
spacing roles, rounded controls/sheets, decorative drawer-and-tick logo,
surface header, wrapping footer, and globally styled scrollbars.

One Jinja breadcrumb macro serves Prepare files, Results, Drawer details,
and the missing-drawer state. Ancestors are real hash links; the current view
is plain text with `aria-current="page"`. Decorative slashes are hidden from
assistive technology. Results ancestors reuse the existing back-to-results
role, so the existing filter handler updates them. No routing JavaScript or
financial calculations changed.

The view-specific redesign is still ahead: Results is still the existing flat
list, its main download button remains until block 2, and Drawer details still
uses its original heading and full count sheet until block 4. The sleeping-host
hint remains until the Start block. Review checkboxes and report restyling
remain outside scope.

`DESIGN.md` mirrors the shared CSS tokens, with a new test that detects colour
drift between the guide and both runtime themes. `WEB_PLAN.md` remains the
behavior contract. The small `premium-ui.json` manifest records that existing
ownership for the generic audit; it adds no runtime dependency or framework.

## Font provenance and budgets

The two upright Latin variable WOFF2 assets come from pinned Fontsource
packages 5.3.0. Original copyright notices and OFL text are preserved separately
in `LICENSE-next.txt` and `LICENSE-mono.txt`. Package data now includes both
licences. Next is preloaded; Mono loads with amounts. Both use font-display
swap and retain system fallbacks. No external resource is fetched by the app.

| Asset | Bytes | SHA-256 |
| --- | --- | --- |
| Next Latin variable | 33,996 | `18b2a1a39a2fa298b0ba5390aca68462669826c90925656f1c1f6796e0e1bbaf` |
| Mono Latin variable | 17,752 | `2706b1ee4f452e744ea91f7e4908cbde9c5d35521bf5ffffc71a382a2de89613` |

Total fonts: **51,748 bytes**, below 200,000. Combined CSS and JavaScript:
**54,788 bytes**, below 60,000. Later blocks must stay within that budget.
The response-cap test and core/web parity checks remain in the full suite.

## Verification actually run

| Check | Result |
| --- | --- |
| `.venv/bin/pytest -q`, final run with local-socket permission | PASS: **709 tests in 15.46 seconds**, including resource cleanup, core/web parity, package assets, colour contrast, and the unchanged combined-response-cap regression. |
| `.venv/bin/pytest tests/test_web_page.py -q` | PASS: 18 tests, including the new guide/runtime colour check. |
| `.venv/bin/ruff check .` | PASS. |
| `.venv/bin/ruff format --check .` | PASS: 62 files formatted in the final check. |
| Local Chrome matrix | PASS: all four views at 320 x 900 and 1,280 x 900 CSS pixels, light/dark; one visible view, fonts loaded, no page-wide horizontal overflow, and valid current breadcrumbs. All 16 final matrix screenshots visually inspected. |
| Keyboard and filter restoration | PASS: date selection and Note filter, drawer link, Shift+Tab from the drawer heading to its Results breadcrumb, visible 3 px focus ring, Enter return restoring both filters. |
| Missing-drawer recovery | PASS: breadcrumb and return link keep the Results context. |
| File and request controls | PASS: missing-file summary takes focus, its link focuses the file row; seven fake CSVs selected and uploaded; returned 18 leads. Held local requests exercised both Cancel controls and restored the original buttons. |
| Downloads | PASS: all three download buttons produced files containing R03. The downloaded HTML contains no script. |
| Error and retry | PASS: a simulated local 503 showed an inline error; Try again recovered through the real example API to 18 leads. |
| Refresh recovery | PASS: Start shows the existing results-not-saved explanation after refresh. |
| Reduced motion and forced colors | PASS within scope: colour transitions become 0s; scrollbar colours return to system ownership. |
| Resource inspection | Matrix recorded zero page-error events and no resources outside localhost. This does not claim an error-free console during deliberately aborted requests. |
| Official DESIGN.md lint/diff | Lint: 0 errors, 1 warning because the existing guide uses Markdown tables rather than YAML. Diff: the same warning before/after; it does not parse the table token changes. The project colour-drift test provides that check. |
| Links, punctuation, anti-pattern search, and `git diff --check` | PASS within the changed scope. |

Browser: Playwright CLI **1.64.0-alpha-1790635538000**, driving headless
Google Chrome **156.0.0.0** on macOS against localhost. Machine-readable records:
[view matrix](M10_BLOCK1_BROWSER.json), [interaction checks](M10_BLOCK1_INTERACTIONS.json),
and [generic static audit](M10_BLOCK1_AUDIT.json).

The attempted Space/ArrowDown/Enter sequence did not select a date in this
headless browser. Explicit native selection was verified instead. OS popup
geometry and keyboard selection are not claimed as newly verified here.

## Generic audit disposition

The generic strict audit exits **1**, with **seven** actionless-button findings
and no unresolved ownership findings. It cannot follow this application's
external vanilla-JavaScript event bindings. The same seven button findings
already existed in the M9 baseline; the eighth baseline finding, an undocumented
native select owner, is resolved by the maintained contract and manifest.

All seven flagged controls have existing bindings in `app.js` and were exercised
in the real browser: Try the example, both Cancel buttons, Check my files, and
the three downloads. No inert control was found, and no cosmetic action
attributes were added merely to silence the audit. The raw audit is retained;
this is a reviewed detection limitation, not a claimed strict-audit pass.

## Screenshot timeline and development corrections

The new [screenshot folder](screenshots/2026-10-26-m10-block1/) contains **35**
original viewport PNGs dated in the user's America/Los_Angeles timezone:

- One initial Start capture.
- Sixteen initial view/theme/width captures. Flask had cached an earlier
  breadcrumb template after an edit, so these show the intermediate navigation
  without its final visible slash separators.
- Sixteen final captures with **verified** in their filenames, taken after
  restarting the preview and rerunning the example. Use these for the final
  block result. Earlier captures are retained rather than overwritten.
- Two final 320 px dark captures for the missing-drawer view and wrapping footer.

During development the packaging check caught the renamed licence files missing
from the package-data pattern; that was corrected. Ruff also caught one blank
line in the changed test; it was formatted before the final checks. Neither
issue remains. The preview cache was refreshed before final visual acceptance.

## Limits and next block

This block does not claim a new WebKit pass, 400% zoom pass, 200% text-resizing
pass, real screen-reader session, first-time-visitor usability pass, full
accessibility certification, remote CI pass, or public deployment verification.
Those checks remain in the redesign plan or the existing manual-validation gaps.

The next authorized continuation, after the user says `next`, is **M10 block 2**:
the compact Results summary, accurate Python-owned counts/date labels, quiet
downloads, and responsive side column. R06 and R07 remain unfinished.
