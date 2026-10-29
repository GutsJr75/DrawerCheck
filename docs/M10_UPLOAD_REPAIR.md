# M10 upload-state repair, 2026-10-29

The user authorized a contained repair after the whole-M10 review found one
upload-state bug. Changing a file during a check could mark the corrected
file Problem using an error from the previous selection. A late successful
response could also show results from the old files. The native chooser path
predates M10; M10's drop area calls the same shared handler.

## Change

The shared addFiles handler now calls the existing stopWaiting helper before
accepting a recognized file during an upload request. That helper aborts the
browser wait and makes late answers harmless. The replacement remains Ready;
the visitor can explicitly check again. Unknown filenames do not interrupt
the pending request. Reuse the existing Stopped waiting announcement without
moving focus away from the chooser; explicit Cancel still restores button
focus. No new copy, styles, money calculations, request caps,
server endpoints, or application dependencies were added.

The CSS/JS budget remains below 60,000 bytes: 59,983 bytes after removing two
redundant comments to accommodate the guard and cue. Fonts remain 51,748
bytes. The core and saved reports are unchanged.

## Regression checks

[test_web_browser.py](../tests/test_web_browser.py) starts a local Flask test
server on an available port and closes it after each browser run.
[upload_replacement.cjs](../tests/browser/upload_replacement.cjs) drives the
real page using Playwright. Test-only gates hold responses after the actual
validator has completed. They are registered only on the test's app instance.

Each engine covers six cases:

- Choose a replacement while an old validation error is held.
- Choose a replacement while an old success is held.
- Drop a replacement during each of those two cases.
- Choose or drop an unknown filename while a check is pending; it must finish.

The replacement cases deliberately keep fetch receiving after abort. They
start a new valid check before releasing the old response, then verify the
current run, lead count, and drawer difference stay correct. They also check
that Ready, Cancel, slow waiting, and error visibility reset as intended.
They verify the existing stopped announcement and retained chooser focus.
The ignored-file cases also rerun and explicitly Cancel to verify that the
original Cancel action still restores focus to Check my files.
These test browser behavior rather than searching source text for the guard.

The two engine tests failed on the unfixed source because Check my files
remained busy after replacement. With the repair they pass. The test harness
was also corrected to distinguish the held response from the newer response;
matching only the API address could confuse the two.

## Run the optional browser checks

The ordinary Python installation does not need Node.js or browser tools.
Without DRAWERCHECK_PLAYWRIGHT_MODULE the two browser tests are explicitly
skipped, including in the existing CI configuration. To run them, install
Playwright as separate local QA tooling, with Google Chrome and the WebKit
engine available. Set the variable to that Playwright package's absolute path:

```sh
DRAWERCHECK_PLAYWRIGHT_MODULE=/absolute/path/to/node_modules/playwright \
  .venv/bin/pytest -q -s tests/test_web_browser.py
```

The installed Playwright package can provision WebKit with its own CLI:

```sh
node /absolute/path/to/node_modules/playwright/cli.js install webkit
```

This repair reused the already installed QA tools. No package was installed
and no Node package or browser became an application dependency. The test
always starts its own localhost app and uses generated fictional CSVs.

For dated captures, set DRAWERCHECK_SCREENSHOT_DIR to a new folder under
docs/screenshots. Filenames inherit that folder's dated label. Existing PNGs
are rejected rather than overwritten. Normal regression runs take no pictures.

## Evidence and limits

The dated [screenshot folder](screenshots/2026-10-29-m10-upload-repair/) contains
Prepare immediately after replacement, before a new check: both engines,
both selection paths, 320 px light and 1,280 px dark. The screenshot timeline
records the capture tool. No earlier screenshot folder was changed.

The final full opt-in suite passes 731 tests in 24.60 seconds, including the
stopped-announcement, retained-focus, and explicit Cancel checks. Both Ruff
checks, both JavaScript syntax checks, and git diff --check pass.
The ordinary browser-test invocation
without QA tools explicitly skips its two engine tests. Final test results
are recorded in the learning log. The generic static UI
audit retains its seven known external-handler detection findings; it is not
a clean static-audit pass. The scoped browser checks exercise the real actions.
Actual 400% browser zoom, screen-reader speech, and first-time-user testing
remain unverified. No new full accessibility scan is claimed.

This repair is local only. No push, deployment, or new hosted CI result is
claimed. R06 remains next, followed separately by R07; stop for next.
