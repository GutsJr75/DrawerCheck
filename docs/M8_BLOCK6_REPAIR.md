# M8 block 6 repair, 2026-10-24

The user authorized all three suggestions from the block 6 review. They are
implemented and verified locally on 2026-10-24. No push or Render deployment was
performed during that repair session. The public deployment was subsequently
confirmed as described below; block 7 was authorized on 2026-10-26.

## Server processing limit

The revised `render.yaml` starts two explicit sync workers, with one thread
each and a 30-second timeout:

```sh
gunicorn --bind 0.0.0.0:$PORT --workers 2 --worker-class sync --threads 1 --timeout 30 "drawercheck.web:create_app()"
```

Each worker serves one request at a time. Gunicorn can stop a stalled worker
and start its replacement while the other worker serves another visitor.
This trades four active request threads for two independently replaceable
workers. The Python reconciliation code and per-request workspace design stay
unchanged. [Gunicorn's timeout documentation](https://gunicorn.org/reference/settings/#timeout)
explains why the former threaded setup did not limit individual requests.

The timeout is a worker watchdog with scheduling tolerance, not an exact
30-second deadline measured from the visitor's click. Host wake-up and queue
time are separate. An aborted request may return Gunicorn's generic HTTP 500;
the page already handles non-JSON failures with its unavailable message and
Try again action. The browser's Cancel button stops waiting, while the worker
watchdog bounds processing independently.

The new `tests/test_web_server.py` starts a real Gunicorn server using the
Blueprint's command and a local Unix socket, without accessing the network.
Only the timeout is shortened to two seconds. A temporary test wrapper delays
demo generation for eight seconds inside its real temporary workspace.

- Before the repair, the test failed: the threaded worker kept processing.
- After the repair, a second visitor completed the normal 60-drawer demo while
  the first was stalled; the stalled request ended with HTTP 500, never reached
  its completion marker, and its workspace was removed.
- A later request still returned 60 drawers and 16 leads. The test checks the
  worker timeout log and leaves no temporary server running.
- The optional-web GitHub Actions step now includes this test. Hosted results
  for this repair have not been observed.

Cleanup is verified for this interruptible Python stall. A process crash or
forced kill cannot guarantee that Python cleanup code runs.

## Memory and concurrent-work check

Two concurrent uploads used the existing combined-workload fixture, each with
1,000 drawers, 2,000 daily summaries, and all three report formats. Each request
contained 569,801 bytes including multipart framing. Both returned HTTP 200:
one took 2.36 seconds and the other 2.30 seconds on this Mac.

Sampling only the Gunicorn master and its two workers showed a peak sum of
152.6 MiB RSS. Summed RSS can count shared pages more than once, and sampling
can miss short peaks. This is local macOS evidence, not a Render measurement
or a guarantee that every permitted input fits a particular memory limit.

## Wording and browser checks

- Start now says **Upload demo CSVs**.
- The download area says: **Results disappear when you refresh or close this
  page. Download a report to keep a copy.**
- Native Google Chrome successfully ran the local example and displayed the
  new reminder. Tab reached the renamed link, Enter opened Prepare files, and
  submitting without files still focused the seven-item error summary.
- The two changes were inspected at 1,222 px and at a 320 px responsive
  viewport, in dark mode. The new label fits and the reminder wraps. Four
  inspected screenshots are in the [new timeline folder](screenshots/2026-10-24-m8-block6-repair/).
  Browser chrome and DevTools were cropped out; the 320 px images show scrolled
  positions so the changed controls and wording are visible.
- No fresh full accessibility, light-theme, or cross-browser audit is claimed.
  The existing contrast tests passed; no colours or styles changed.

## Verification

| Command or check | Result |
| --- | --- |
| `.venv/bin/pytest -q tests/test_web_server.py` before the fix | FAIL with the old threaded command, as expected |
| `.venv/bin/pytest -q tests/test_web_server.py tests/test_web_page.py` after the fix | PASS: 18 tests |
| `.venv/bin/pytest -q` | PASS: 686 tests in 22.19 seconds |
| `.venv/bin/ruff check .` | PASS |
| `.venv/bin/ruff format --check .` | PASS |
| `git diff --check` | PASS |
| Local Gunicorn with the revised deployment options | PASS: two sync workers started; browser demo and two concurrent combined workloads succeeded |
| Frontend skill's strict static audit | Exit 2, with the same eight findings present before the repair; see the explanation below |

The generic static audit cannot follow this app's external JavaScript event
listeners and incorrectly calls seven working buttons actionless. Its button
rule accepts inline `onclick` attributes, which conflict with this project's
CSP. Existing `app.js` listeners remain the canonical owners; no inline
handlers were added. Its eighth finding requires tool-specific manifest data
for the native select. The existing native choice is now explicit in
`DESIGN.md`, but no extra manifest was introduced for these wording changes.
The [raw audit output](M8_BLOCK6_REPAIR_AUDIT.json) is retained; a strict audit
pass is not claimed.

Chrome's extension-enabled profile also showed an Issues entry about CSP
blocking `eval`, without a source location. Its console listed zero messages.
The unchanged app script contains no `eval`, `new Function`, or string-based
timers, and the tested flows worked. The issue was not attributed to a specific
extension or silently dismissed as resolved. No CSP setting was weakened.

## Applying the repair to the public demo

After pushing this commit, sync the Blueprint if the service is Blueprint
managed. If the service was created manually, set its Start Command to the
exact command above and deploy the repaired commit. Merely changing
`render.yaml` in Git does not establish that a manually configured service uses
the new command.

Then inspect the deployment logs for sync workers, verify both new messages,
run the public example and a fake-data upload, and check report downloads.
Observe the new GitHub Actions result before claiming hosted verification.
Do not send deliberately stalled test requests to the public site.

## Public deployment confirmation, 2026-10-26

The user supplied Render dashboard screenshots in the conversation showing:

- Deployment source commit `332f01b`.
- `Using worker: sync` at 03:17:27 PDT on 2026-10-24.
- Two `Booting worker with pid` entries, for processes 59 and 60, at the same
  startup time and on the same instance (`kqsbl`).
- Successful `GET /` health-check responses and successful static asset
  requests in the runtime log view.

These screenshots were reviewed on 2026-10-26; the startup event they show is
dated 2026-10-24. They confirm the deployed commit, worker type, and two workers.
They do not directly establish the effective timeout value or test a timeout
on Render. The command and local regression supply that separate evidence.
The dashboard images remain conversation attachments, not repository image
files. No new app screenshot was captured for this documentation block.

The user reported that the remaining step-by-step checks were complete and
working, covering CI, configuration/deployment, the example, synthetic upload,
report downloads, refresh recovery, and the local timeout test. This is
user-reported evidence, not a fresh agent browser run or transcript of those
commands. No deliberate stall was sent to the public service by this agent.

GitHub Actions was independently inspected through the connected GitHub API on
2026-10-26: [run 40085196045](https://github.com/GutsJr75/DrawerCheck/actions/runs/40085196045)
for `332f01b39d2b822c2171fd5e3d48ed0b78503409` completed successfully on
2026-10-24. Python 3.12, 3.13, and 3.14 all passed lint, formatting, core tests,
installed CLI help, and optional web requests (including the new server test).
This closes the repair's deployment follow-up with the evidence distinctions
above. The [M8 checklist](M8_CHECKLIST.md) retains remaining manual checks.
