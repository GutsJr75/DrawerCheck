# Public frontend plan

## Where things stand

- **M7, web request handling: done.** Authorized by the user on 2026-10-23 and
  verified locally and on GitHub. [Run 39932017056](https://github.com/GutsJr75/DrawerCheck/actions/runs/39932017056)
  passed for the final M7 commit `2bdbb7a` on Python 3.12, 3.13, and 3.14,
  including the web tests.
- **M8, screens and public demo: not started.** It waits for the user's next
  instruction.
- **Quick map of this document:** the user decision and audience come first,
  then the screens and wording, the architecture, hosting, milestones, the
  definition of done, and finally the [M7 request contract](#m7-request-contract-and-handoff)
  that M8 builds on.

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

This design decision originally recorded future M7/M8 behaviour without authorizing
implementation. M7 was subsequently authorized and completed. Detailed visual
choices and browser checks remain M8 work. See [DESIGN.md](../DESIGN.md).

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
- Workload limits: a 2 MiB total upload-request limit, at most 5 registers,
  100 people, 1,000 shifts, 2,000 bank deposits, and 2,000 safe drops per run.
  POS/count rows are capped at their natural maxima of 1,000 and 12,000.
  Each field has a 256-character limit. Count CSV records and check field lengths
  before opening a database, excluding headers and blank lines. Limit expanded
  shift-code references to 1,000 and the complete response to 10,000,000 bytes.
  These are project
  choices, not industry standards. Confirm that
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

## M7 request contract and handoff

Install with `pip install -e ".[dev,web]"`. The core-only installation remains
`pip install -e .`. The web extra adds Flask to handle requests and Gunicorn to
serve the application on Unix hosts; Gunicorn is excluded on native Windows.
The application factory is `drawercheck.web:create_app()`. No browser page is
implemented at this milestone.

| Request | Input | Successful response |
| --- | --- | --- |
| `POST /api/demo` | Empty body, no URL options | The fixed 30-day example's full results. |
| `POST /api/check` | Multipart upload with seven repeated `files` fields | The uploaded records' full results. |

Filenames must exactly match the seven names in the CSV contract. No archive,
folder path, extra field, policy override, or database path is accepted. MIME
labels are not treated as proof of CSV validity; the shared importer validates
the actual bytes, including UTF-8/BOM, headers, rows, and references.

Both routes use the core's built-in example policies, independent of local
`config.toml`. The 2 MiB limit includes the complete multipart request. Valid
requests exactly at the limit pass; larger ones return 413. Multipart parsing
also has an eight-part limit and 128 KiB non-file-field limit. The per-file
record limits are 5 for `registers.csv`, 100 for `cashiers.csv`, 1,000 for
`shifts.csv`, 2,000 for `bank_deposits.csv`, and 2,000 for `safe_drops.csv`.
The remaining files also have early caps: 1,000 for `pos_totals.csv` and 12,000
for `cash_counts.csv`, following one POS row and twelve allowed denominations
per shift. This gives all seven files a row cap before database work.
Values in data records may have up to 256 characters, including whitespace.
Exceeding a record or field limit returns 400 while the
shared CSV reader prepares the input, before SQLite is opened or any rows are
inserted. Headers and blank lines do not count; quoted multiline values remain
one record. These limits apply only to web runs; CLI imports remain uncapped.
The fixed example uses 2 registers, 5 people, and 60 shifts, comfortably within
the limits.

Roster caps also bound the register-by-date missing-record leads. Long text and
overlaps need separate bounds: web reconciliation allows at most 1,000 total
references to other shift codes across overlap and multiple-closing details.
Multiple-closing references are counted before the lists are created; overlap
references are counted as pairs are found and stop before crossing the limit.
Excess returns 400 before rule evaluation and saving results. This is a workload
limit, not a change to the reconciliation rules. Core callers can omit the limit.

The entire serialized response, including all result fields, JSON escaping,
three embedded reports, and the trailing newline, has a 10 MB budget
(10,000,000 bytes). JSON is encoded incrementally into a bounded response buffer.
Results that exceed the budget return a short 400 error; no flags or reports
are silently truncated. Error responses have the same final size check. Cleanup
and no-store/nosniff headers apply to these rejections as well. Report strings
and records still use working memory, so this response limit is not a claim
that the process uses only 10 MB of RAM.

The combined stress fixture fills all seven record caps, spreads 1,000 shifts
over 1,000 dates, and verifies that the full successful response is under 10 MB.
Separate cases cover long HTML-escaped identifiers and excessive same-day or
cross-date overlaps. These must be rejected safely rather than relying on one
fixture as proof that every accepted input will have a small output.

JSON includes `notice`, `from_date`, `to_date`, `generated_at`, `days`, `cashiers`,
`flags`, `shifts`, and `reports`. Money fields use names ending in `_amount`
and are formatted in Python, including nested flag evidence. Count entries have
a formatted `denomination` and integer `quantity`. Missing cash remains `unknown`;
a bank-only date says `Not calculated (no shifts)`. No browser money calculations
are needed. Each shift includes its input records, expected/count/difference,
saved shift leads, daily leads, policy thresholds, and shared deposit explanation.

Each `reports` entry (`text`, `html`, `csv`) includes its `filename`, `media_type`,
and complete `content`. M8 can turn these buffered strings into local downloads;
it must not request an already deleted server workspace. The HTML content is the
existing escaped offline report, and CSV uses the shared cell protection.
JSON strings are data: M8 must render uploaded names, notes, identifiers, and
errors through text nodes or normal template escaping, never `innerHTML`.

Each run owns a fresh temporary directory. All database connections are closed,
the directory is removed before the response returns, and upload streams close
even after a failed multipart parse. There is no server run cache, session cookie,
shared database, or stored download. Responses use `Cache-Control: no-store`.
Invalid input returns JSON `error.message` with status 400; CSV errors additionally
include `file_name`, physical `line_number`, and `column`. Server failures return
a generic message with status 503 and do not log submitted records or paths.
HTTP routing/parser failures also return JSON, without debug pages.

The interface should display `error.message`. Header errors identify
`the first row (column names)`; whole-record and encoding errors do not invent
a field name. An unclosed quoted value gets that specific explanation, while
other quoting/format problems and overlong values get different instructions.
The structured `column` metadata retains the importer's internal location tags
for code that needs them; those tags are not part of the displayed message.

The M7 repair also adds non-unique indexes covering each deposit/drop duplicate
lookup's full record key. Existing databases acquire them on the next import or
`init-db`; records and duplicate-rejection behaviour are preserved. Reconciliation,
daily summaries, report loading, and web shift details group review leads once
instead of repeatedly scanning every lead for each date or shift.

Local verification and exact commands are recorded in the learning log. CI now
tests the core before installing optional web packages, then runs the web tests
on Python 3.12/3.13/3.14. The hosted [run 39932017056](https://github.com/GutsJr75/DrawerCheck/actions/runs/39932017056)
passed both stages on all three versions for the final M7 commit `2bdbb7a`.
M8 still needs the actual interface, browser and usability checks, and observed
public deployment.

## Dependency references rechecked on 2026-10-23

- [Flask releases](https://flask.palletsprojects.com/en/stable/changes/) and
  [Flask on PyPI](https://pypi.org/project/Flask/): Flask 3.1.3 and Python support.
- [Gunicorn on PyPI](https://pypi.org/project/gunicorn/): Gunicorn 26.2.0 and Unix support.
- [Flask resource limits](https://flask.palletsprojects.com/en/stable/web-security/):
  total request size, multipart part count, and non-file-field limits.
- [Flask uploads](https://flask.palletsprojects.com/en/stable/patterns/fileuploads/):
  fixed filename handling and request-size rejection.

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
