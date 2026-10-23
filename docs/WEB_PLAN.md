# Public frontend plan

Status: Scope approved on 2026-10-22; implementation is scheduled for M7/M8.
M0 through M6 are complete, including hosted CI verification. M7 is the next
milestone and awaits a separate user instruction.

## User decision

The user requested both a polished recruiter demo and an interactive frontend,
even if that expands the project. They explicitly chose a public app where
visitors can upload CSVs and run checks.

This amendment permits the web interface, hosting, and optional web dependencies
previously excluded by the original brief. All money, database, demo-data,
neutral-wording, and report-safety requirements still apply. The original brief
is retained unchanged; read it together with the current plan.

## Audience and design direction (approved 2026-10-22)

Assume visitors may know neither coding nor cash-drawer reconciliation. Explain
the task through ordinary words and concrete examples. The public site is a
personal learning demo using fictional records, not a tool for real cash control.

Build a minimal, professional interface: neutral backgrounds, one main accent,
readable text, consistent spacing, familiar controls, and one primary action per
view. Use cards, icons, and colour only when they help someone understand or act.
Keep the example-data notice, errors, and missing-record warnings visible.
Minimalism must not hide essential information or remove accessible labels.

### Focused views and optional explanations

These are task-focused views, not separate required setup steps or a commitment
to four server routes. Keep navigation simple and preserve the temporary-run
behaviour described below.

| View | Main purpose | Information shown when needed |
| --- | --- | --- |
| Start | Explain the purpose briefly; make `Try the example` the main action and uploading the secondary action. | A short explanation of what the example contains. No files, coding, or compulsory tutorial required. |
| Prepare files | Help uploaders choose the seven synthetic CSV files and see which are present or missing. | Downloadable examples/templates, preparation guidance, file limits, and specific corrections. Skip this view for the built-in example. |
| Results | Show a short summary, review items, date/severity filters, and report downloads. | Brief definitions beside unfamiliar terms; open a record to investigate it. |
| Drawer details | Explain one shift's expected cash, counted cash, difference, and review leads. | An expandable calculation and suggested checks in plain sentences. Provide a clear return to results with filters retained while the run remains open. |

Show essentials first and let visitors open details where they are relevant.
Place help beside its subject rather than collecting all instructions on the
first screen. Expandable help must work by keyboard and touch, not hover alone.
Use a normal `Choose files` button even if drag and drop is offered. Allow users
to replace a wrong file before submitting. Explain loading, empty, no-matching-
results, error, and success states with a clear next action. Do not invent
percentage progress when it cannot be measured.

### Plain language without changing meaning

Keep the same action and concept labels across views. Explain necessary cash
terms briefly; do not require visitors to understand rule codes or commands.

| Internal term or format | Suggested public wording |
| --- | --- |
| Reconcile | Check drawers |
| Variance | Cash difference |
| R01_VARIANCE | Cash difference to check |
| R09_DATA_INTEGRITY | Missing or inconsistent records |
| info / warn / review | Note / Check / Needs review |
| Exact net | Total over/short |
| HTML / CSV / text download | Web page (.html) / Spreadsheet (.csv) / Text (.txt) |

These labels describe review leads, not findings about a person or deadlines.
Keep rule codes available as secondary details. Distinguish issue counts from
affected-shift counts, and missing amounts from zero. Each issue should say
what happened, what is unknown, and what the visitor can check next.

During M7, add plain web error messages in `errors.py` that name the actual file,
source line, and field where available, explain the problem, and suggest a fix.
Preserve identifiers and physical CSV line numbers accurately; a cashier ID is
not a cashier name, and multiline records make guessed spreadsheet row numbers
unreliable. The website runs the pipeline itself, so do not ask visitors to run
CLI commands. Keep the existing validation and shared calculations unchanged.

This decision records future M7/M8 behaviour only. It does not implement screens,
change the M4 report, or authorize M5. Detailed visual choices and browser checks
remain part of the later frontend work. See [DESIGN.md](../DESIGN.md).

## Experience to build

1. Open the public URL and see what DrawerCheck does, with a visible demo-data
   notice and a button to run the supplied example without preparing files.
2. Alternatively, choose the seven synthetic CSV files. Show the required names
   and a way to download example inputs. Accept CSVs, not uploaded archives.
3. Run reconciliation and see a clear progress state or a specific input error.
4. See daily totals, balanced/over/short and incomplete counts, flags by severity,
   and the cashier over/short summary. Support date and severity filtering.
5. Inspect a shift's calculation and review leads, using the same explanation
   data as the CLI. Distinguish unknown values from counted zero cash.
6. Download the text, standalone HTML, and protected CSV reports. Start a new run
   when desired. Explain that refreshing/closing the page does not preserve a run.

Use responsive HTML and CSS, visible text labels, labelled inputs, keyboard
navigation, and clear empty/loading/error/success states. The initial public app
has no login, saved history, record editing, custom policy editor, integrations,
or production-business workflow. Allow synthetic demo inputs only; validation
cannot prove that arbitrary uploaded names or figures are fictional.

## Architecture and initial choices

- Keep the command-line core and its standard-library-only runtime. Install the
  web dependencies separately using an optional extra, added during M7.
- Use Flask, which connects browser requests to Python functions. Use Gunicorn,
  which runs the Flask app on the Linux host. Verify supported dependency
  versions during M7; no dependencies change during this scope update.
- Use HTML, CSS, and minimal bundled JavaScript for the browser interface. Keep
  financial calculations, rule thresholds, and money formatting in Python.
  Send formatted money strings to the browser so JavaScript cannot round cents.
- Import, reconcile, explain, and generate reports by calling shared functions.
  Do not execute shell commands with uploaded values or maintain a second rules
  engine for the frontend. M2 onward functions must accept explicit paths and
  return data/errors rather than printing their own CLI messages.
- Give every run a fresh temporary directory and SQLite database. Use the seven
  fixed expected filenames within that directory, never client-supplied paths.
  Preserve the raw upload bytes for the importer's hash and CSV handling.
- Close database connections and delete temporary files after preparing the
  response, including after an error. Keep no shared visitor results database.
  The response must include the information needed to display results and
  download reports while the page is open, so downloads need no saved workspace.
- Initial design limits: a 2 MiB total upload-request limit and at most 1,000
  shifts per run. These are project choices, not industry standards. Confirm that
  the default demo fits and test rejection at the boundaries during M7.
- Keep all errors in `errors.py`. Escape dynamic HTML, protect CSV exports,
  reject unexpected file inputs, and do not log uploaded CSV contents. Debug
  mode and tracebacks must be disabled on the public deployment.
- The downloadable HTML report remains one offline file with inline CSS and no
  JavaScript. The interactive app's JavaScript and styles are bundled locally,
  without external scripts, fonts, trackers, or POS/bank API calls.

## Hosting direction

Render's free Python web service is the initial candidate, following its Flask
and Gunicorn deployment guide. Recheck limits and costs during M8 before choosing
the actual service configuration. Creating an account or connecting the repository
may require the user's interaction at that stage.

The current Render documentation describes sleeping after idle time, a delayed
first response, and loss of uploaded files/local databases on restart. Temporary
per-request workspaces avoid relying on persistent disk, but README must explain
the first-load delay and demo availability limits. Do not promise uninterrupted
availability or call the app suitable for real cash control.

GitHub Pages can show a static report but cannot run the Python reconciliation
service. A Pages-only deployment would not satisfy the interactive-public-app
request.

## Milestones and files

Each work block targets 30 to 60 minutes. Split a growing block; do not remove
required correctness or data-isolation checks to meet the earlier time estimate.

| Milestone | Work blocks | Main files |
| --- | --- | --- |
| M7: Web request handling | Optional package setup and application entry point; upload/demo pipeline with temporary cleanup; errors, limits, isolation, and parity tests. | `src/drawercheck/web.py`, `errors.py`, `pyproject.toml`, `tests/test_web.py`, CI updates |
| M8: Screens and delivery | Upload/demo screen; summary and shift details; filtering/downloads and user states; browser verification; hosting configuration and public smoke check; README/screenshots and interview update. | `src/drawercheck/templates/`, `src/drawercheck/static/`, package-data setup, `render.yaml`, `README.md`, `docs/INTERVIEW_NOTES.md` |

M2 through M6 still complete the core first. Stop after each authorized milestone
for review. Optional rules R03, R06, and R07 move to M9 and remain opt-in.

## Verification and expanded definition of done

- The same inputs and config produce the same calculations, flags, explanations,
  and report content through the CLI and web. Test the actual shared functions.
- Use Flask's in-process test client for web tests; no automated test depends on
  an external host. Test bad uploads, duplicate/missing files, size and shift
  limits, escaped values, protected CSVs, and readable errors without tracebacks.
- Test two independent runs and failure cleanup. Neither run may read or alter
  the other run or the developer's local database.
- Verify the actual browser flow on desktop and a narrow screen: built-in demo,
  uploads, errors, results, filtering, shift explanation, downloads, and starting
  again. Check keyboard operation and the downloadable report's offline behavior.
- Check that the focused views keep essential warnings visible and optional
  explanations available by keyboard and touch. Confirm that labels and counts
  match the underlying results, with no command-line instructions in web errors.
- Arrange a usability check with a person unfamiliar with the project: can they
  run the example, find and explain an item needing review, and download a report
  without coaching? Record observed difficulties and repairs; if no participant
  is available, record the missing check rather than claiming it passed.
- Keep the core install working without web dependencies. Run pytest and both
  Ruff checks; add web coverage to CI and report only observed CI results.
- Verify a real public URL from a fresh browser session before marking M8 done.
  Check a synthetic upload, the demo button, report downloads, restart behavior,
  and cold-start messaging. Deployment success must come from actual checks.
- Update README with the public demo link, real screenshots, core/web setup,
  temporary-data behavior, hosting limitations, and a plain explanation of each
  library. Update career material only after the claimed features exist.

## Primary references reviewed on 2026-10-22

- [Flask uploads](https://flask.palletsprojects.com/en/stable/patterns/fileuploads/):
  file handling, untrusted filenames, and request-size limits.
- [Flask testing](https://flask.palletsprojects.com/en/stable/testing/): testing
  requests without a live server.
- [Flask deployment](https://flask.palletsprojects.com/en/stable/deploying/): use
  a production server for a public app, with debug mode disabled.
- [Gunicorn](https://flask.palletsprojects.com/en/stable/deploying/gunicorn/):
  the proposed Linux hosting process; it is not a native Windows server.
- [Render Flask guide](https://render.com/docs/deploy-flask): example deployment
  with Python and Gunicorn.
- [Render free services](https://render.com/docs/free): current idle, storage,
  usage, and availability limitations; recheck before deployment.
- [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages):
  static hosting scope.
