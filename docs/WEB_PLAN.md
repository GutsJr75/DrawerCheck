# Public frontend plan

## Where things stand

- **M10 block 1 (authorized 2026-10-26):** the shared "Tick and tie" palette,
  local Atkinson fonts, responsive type/spacing, decorative drawer logo,
  header, footer, and breadcrumbs replace the corresponding M8 shell styles.
  Results grouping and the later view changes remain separate blocks. The
  current visual rules are in [DESIGN.md](../DESIGN.md); the delivery scope is
  in [REDESIGN_PLAN.md](REDESIGN_PLAN.md).
- **M10 block 2 complete locally (authorized 2026-10-26):** Results now uses
  a Full run summary, secondary downloads, and a responsive side column.
  Python supplies separate drawer/day counts and weekday date labels,
  including overnight clock dates. That block kept the list flat.
  See [block 2 evidence](M10_BLOCK2.md). Stop for `next` before grouping.
- **M10 block 3 complete locally (authorized 2026-10-27):** matching leads
  group by unique drawer and whole-day date. Unfiltered sections use server
  counts; filtered sections retain full-run drawer order and overall levels
  without counts. More detail contains closed disclosures with previews.
  See [block 3 evidence](M10_BLOCK3.md). Stop for `next` before Drawer details.
- **M10 block 4 complete locally (authorized 2026-10-27):** Drawer details
  has a human title, exact outcome strip, supplied-zero row toggle, qualified
  input ticks, applicable rule limits, and filter-aware Next navigation.
  See [block 4 evidence](M10_BLOCK4.md).
- **M10 block 5 complete locally (authorized 2026-10-27, completed 2026-10-28):**
  Start has a shorter lead, actions before the example description, qualified
  input ticks, and the numbered Count, Compare, Review sequence. Remove the
  always-on hosting hint and preserve the existing request/recovery behavior.
  See [block 5 evidence](M10_BLOCK5.md).
- **M10 block 6 complete locally (authorized 2026-10-28):** Prepare files
  now uses two steps, a dashed drop area with its native chooser, compact
  Ready/Problem rows, named missing-file guidance, and responsive side help.
  Both input paths share the existing chosen-file map and validation flow.
  See [block 6 evidence](M10_BLOCK6.md). Stop for `next` before block 7.
- **M7, web request handling: done.** Authorized by the user on 2026-10-23 and
  verified locally and on GitHub. [Run 39932017056](https://github.com/GutsJr75/DrawerCheck/actions/runs/39932017056)
  passed for the final M7 commit `2bdbb7a` on Python 3.12, 3.13, and 3.14,
  including the web tests.
- **M8, screens and public demo: all seven delivery blocks complete.** Includes
  the live public deployment at
  [drawercheck.onrender.com](https://drawercheck.onrender.com) verified on
  2026-10-24 and the documentation wrap-up authorized on 2026-10-26. The
  [M8 checklist](M8_CHECKLIST.md) records verification gaps: a real screen-reader
  check remains open, and the user deferred a friend usability check.
- **Design rules for M8: ready.** [DESIGN.md](../DESIGN.md) says how the site
  should look (WCAG 2.2 AA, colours, fonts, and signature elements). This file
  says how it should behave, including navigation, uploads, and loading.
- **Block 6 repair:** locally verified on 2026-10-24. On 2026-10-26, reviewed
  user-provided Render screenshots confirming repair commit `332f01b` and two
  sync workers; the user reported the other checks passing. Independently
  observed successful hosted CI run 40085196045. See
  [repair evidence](M8_BLOCK6_REPAIR.md).

| M8 block | What gets built | Status |
| --- | --- | --- |
| 1 | Summary, count line totals, and labels in the JSON; page layout, colour tokens, IBM Plex fonts, demo notice, footer, and security headers | Done |
| 2 | Start and Prepare files: "Try the example", the example tape, and the file checklist with its error summary | Done |
| 3 | Results and Drawer details: the plain-facts summary, review list, drawer tape, and count sheet | Done |
| 4 | Navigation and states: addresses, filters, downloads, loading, Cancel, and the slow-start message | Done |
| 5 | Checks: WCAG 2.2 AA, 320 px and 400% zoom, keyboard, dark mode, and screenshots | Done |
| 6 | Hosting: Render setup and a check of the live public site (`https://drawercheck.onrender.com`) | Done |
| 7 | Wrap-up: README screenshots and interview notes | Done, with remaining manual checks recorded |

- **Quick map of this document:** the user decision and audience come first,
  then the screens and wording, the architecture, hosting, milestones, the
  definition of done, and finally the [M7 request contract](#m7-request-contract-and-handoff)
  that M8 builds on.

## User decision

M9 block 1 adds the R03 swapped-digit heuristic after M8 delivery, now verified
locally, on GitHub (run 40426134663), and on the public site on 2026-10-26.
Current source demo results contain 18 leads rather than the historical M8
16; the additional two are notes only. The old screenshots and verification
counts below remain historical evidence. R03 has no new screen or JavaScript
calculation; it reuses server labels and existing lead rendering. See
[M9 block 1](M9_BLOCK1.md#public-verification-follow-up-2026-10-26) for current
checks and deployment evidence.

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
| R02_SINGLE_DENOMINATION | Possible single bill |
| R04_REPEAT_SHORT | Repeated shortages |
| R05_MISSING_VERIFIER_OR_NOTE | Missing sign-off |
| R08_DEPOSIT | Bank deposit to check |
| R09_DATA_INTEGRITY | Missing or inconsistent records |
| info / warn / review | Note / Check / Needs review |
| balanced / over / short | Balanced (within $1.00) / Over / Short |
| incomplete / open | Missing records / Still open |
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
implementation. M7 was subsequently authorized and completed. The visual system,
WCAG 2.2 AA target, and signature elements were added to [DESIGN.md](../DESIGN.md)
on 2026-10-23. The behaviour rules below were added at the same time. Browser
checks remain M8 work.

### Navigation, addresses, and the Back button

M10 block 1 adds a shared breadcrumb macro to Prepare files, Results, Drawer
details, and the missing-drawer view. Start is the root and needs no breadcrumb.
The current view is plain text, not a link. Parent links use the same hash
addresses below; every Results ancestor uses the existing `back-to-results`
role, so filtering updates its address alongside the existing return actions.
The short current label on Drawer details stays "Drawer details" until its
human-readable heading arrives in block 4. Page titles and view-heading focus
still use the existing shared route handler. No new routing or stored state.

### Canonical UI Map

This document is the maintained behavior contract; DESIGN.md owns visual rules.
The optional `premium-ui.json` audit manifest points here rather than creating
a second UX contract. Existing native popup geometry is an intentional choice.

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
| --- | --- | --- | --- | --- |
| Select/Listbox | Native select and radio buttons in index.html, populated by app.js | This document's navigation and filter rules | Browser/OS-owned popup, CSS-styled trigger | Keyboard, opened popup, filter restoration in the local browser |
| Date | Python labels.dates in web.py, shared formatDate lookup in app.js | M10 data contract below; server-owned English calendar labels | Read-only labels, no date picker; includes overnight clock dates | API date coverage and visible date options |
| Form | Existing chosen-file map, shared addFiles handler, importer validation, and error summary | Upload and request contracts below | Seven fake CSVs; native chooser and drop area; both use addFiles | Web/page tests; chooser/drop/replacement, file errors, limits, and focus in the browser |
| Scrollbar | Global app.css standards rules and WebKit fallback | DESIGN.md runtime mapping | Document scrolling; optional tables own horizontal overflow | Narrow views and computed styles, system fallback in forced colors |

There is no table selection, account CRUD, or toast system. Existing polite
live announcements and inline errors remain owned by app.js and the template.
The operation and recovery rules below remain authoritative.

Each view has its own address after `#`, so the browser's Back and Forward
buttons, refresh, and copied links behave the way people expect:

| Address | View |
| --- | --- |
| `#/` | Start |
| `#/prepare` | Prepare files |
| `#/results?date=2026-09-03&show=review` | Results, with optional date and severity filters (`show` is `all`, `review`, `check`, or `note`) |
| `#/drawer/2026-09-03-R1` | Drawer details for one shift (the shift code is URL-encoded) |

- Moving to another view adds a history entry. Changing a filter replaces the
  current entry, so Back does not step through every filter click.
- After each view change, update the page title (for example
  "Drawer 2026-09-03-R1 | DrawerCheck") and move keyboard focus to the view's
  main heading.
- Results live only in the open page. If someone refreshes, or opens a results
  or drawer address with no results loaded, show Start with: "Results are not
  saved. Run the example again or upload your files."
- An address for a shift that is not in the current results shows "This drawer
  is not in the current results" with a link back to Results.
- Do not block leaving the page with a browser warning. The demo notice already
  says results disappear when the page closes.

Built in M8 block 4 (2026-10-23):

- Every view link is a real `#/` link, so it can be opened, copied, or read by
  a screen reader as a link. "Back to results" keeps the current filters.
- Filters are a date list (only dates that have leads) and a level choice.
  They apply as soon as they change and replace the address. An unknown date
  or level in an address falls back to all leads. Because the browser does not
  count leads, the line under the filters describes them in words ("Showing
  leads marked Needs review on September 16, 2026") rather than as a number.
- An empty, unknown, or non-view hash: no hash shows Start, `#/unknown` becomes
  `#/`, and other hashes such as `#main` leave the current view alone.
- Leaving a view while a check is waiting stops waiting, like Cancel.
- Server and connection failures on Prepare files now show beside the button
  with "Try again", instead of in the error summary, whose title is about the
  files.
- The "Skip to main content" link uses `#main`. The block 4 router must treat
  only addresses starting with `#/` as views and leave other hashes alone, so
  the skip link keeps working.

### Uploading files

- Use a normal labelled file input that accepts several `.csv` files at once.
  Dragging files onto the list is optional extra help, never the only way.
- Show a checklist of the seven required filenames. Each row shows Waiting,
  Ready (with file size), or Problem (with the message). Choosing a file again
  replaces the one with the same name.
- Before sending, the browser checks only the filenames, the number of files,
  and the total size. It never reads or judges the file contents; the server
  does that.
- When the server reports a problem, show an error summary at the top of the
  view titled "There is a problem with your files", move focus to it, and link
  each message to the matching checklist row. Use the `file_name` returned with
  CSV errors to find that row.
- Beside the chooser, say plainly: "Use example data only. Files are checked
  and then deleted; nothing is saved."

Built in M8 block 2 (2026-10-23):

- Each checklist row has a "Download example" link to `GET /examples/<file>`,
  which runs the same demo generator as "Try the example" in a temporary
  folder and returns that one CSV. Only the seven names are accepted.
- A file whose name differs only in capital letters gets a rename hint; any
  other name is reported as not one of the seven. Neither is added.
- The browser's own messages live in `errors.py` with the server's, and reach
  the page through the template, so the script contains no message wording.
- A file the server reports a problem with stays chosen but is not counted as
  ready, so "6 of 7 files ready" agrees with the rows.
- Buttons switch views directly for now, and a busy button changes its text and
  ignores further presses. Block 4 replaces both with addresses, Cancel, the
  slow-start message, and the 90-second limit. Results show one sentence until
  block 3 builds the real view.
- Drag and drop is not built; the plan treats it as optional.

Built in M8 block 3 (2026-10-23):

- Results shows the plain-facts line from `summary`, the leads by level, and
  every lead with its level, plain title, Python's message, and the date,
  drawer or "Whole day", and rule code as secondary detail. "Needs review"
  comes first, then date and drawer. The day and cashier tables sit in closed
  sections and fill only when opened, so a large upload shows quickly.
- Drawer details shows the tape, the count sheet, this drawer's leads, the
  day's leads, how the limits work, and how the drawer adds to the bank
  deposit. Every amount is Python's string; unknown amounts say why.
- Both tapes come from one list of lines in `web.py` (`TAPE_LINES`), so the
  Start example and Drawer details share labels, signs, and definitions.
- Only drawers with their own leads could be opened from Results in block 3.
  Block 4 added `#/drawer/<code>` addresses, drawer links on whole-day leads,
  and the All drawers section, so every drawer is reachable.
- Results renders every lead at once. A very large upload (thousands of
  leads) may be slow to draw; block 4's filters are the first remedy.

Block 3 repair after review (2026-10-23):

- The bank-deposit sentence now names the actual reason a drawer's share is
  unknown, checked in order: the drawer is still open; it has no count; or it
  was counted but its day is incomplete. A day is incomplete when any drawer is
  open or has missing records, a register closed twice or is missing, or a
  register appears more than once (`expected_deposit` in `reconcile.py`).
  Python's calculation is unchanged.
- The tape's status line may wrap, so a "Balanced (within $1.00)" drawer with a
  label fits 320 px. Tape labels and error-summary links are at least 24 px
  tall, and error links have 8 px between them.
- Block 4 adds links to every drawer: whole-day leads link to that date's
  drawers, labelled as drawers on that date because an unexpected bank entry
  is filed under its own date and may be unrelated to them, and a closed
  "All drawers" section lists every drawer. Bank-only dates have no drawer
  links.

### Loading and slow starts

There are two different waits, and only the second one is ours to design:

1. **Opening the site while the server sleeps.** Render's free service sleeps
   after 15 minutes without traffic. On the next visit, Render shows its own
   loading page in the browser while the server wakes, which
   [Render's documentation](https://render.com/docs/free) says takes about one
   minute. Our page has not loaded yet, so none of our messages can appear.
   README explains this first-visit delay. M10 block 5 removes the always-on
   Start explanation, as approved in REDESIGN_PLAN.md; the request notice
   below still appears when a check is slow.
2. **Waiting for a check after our page has loaded.** The server may still be
   slow if it fell asleep while the page stayed open. Our page handles this:

- After a button is pressed, disable it and change its text to say what is
  happening ("Checking the example..." or "Checking your files..."). Announce
  the same text to screen readers.
- After 5 seconds with no response, add: "The demo server may be waking up.
  This usually takes about a minute." Do not promise a maximum time.
- Offer a "Cancel" button while waiting. Cancel stops the browser waiting
  (using an `AbortController`), returns the view to its previous state, and
  ignores any response that arrives afterwards. It does not stop the server:
  the check may still finish in Python, which is harmless because each run is
  bounded and its temporary files are deleted. Do not word Cancel as if it
  stops processing.
- After 90 seconds with no response, stop waiting in the same way and show a
  short error with "Try again".
- No percentage bars, shimmering placeholders, or spinners without words.

Built in M8 block 4: both timings come from `web.py` (`SLOW_NOTICE_MS` and
`GIVE_UP_MS`) through the page, so the docs, page, and tests agree. Cancel, the
time limit, and leaving the view end the wait at once, even if the network has
not let go yet; a late answer is ignored rather than shown.

### M10 block 2 Results contract (2026-10-26)

This supersedes the historical M8 plain-facts layout described above.

- Show one server-labelled date range, then the "Full run" slip: affected
  drawers out of checked drawers, drawer leads, whole-day leads and dates,
  and drawers with no own leads. No no-leads count implies an exact match.
- A decorative green tick reinforces the visible no-leads wording only when
  at least one drawer qualifies. It draws once per new run, never on return
  from Drawer details. Reduced motion shows a still tick. Zero drawers gets
  "No drawers in this run." and no tick.
- At 960 px and above, filters, three secondary downloads, and level
  definitions sit beside the review list. Below that width they stack:
  filters, review list, downloads, definitions, then optional detail.
  DOM/keyboard order is summary, filters, review, downloads, optional detail.
  Keep one set of controls and preserve heading focus and native input behavior.
- Full-run counts and report contents stay unchanged when filtering.
  The live status names active filters in words. Detailed lead/severity
  totals are in a closed disclosure after the review area.
- The current list still renders all individual leads with the existing
  metadata and rule codes. Grouping and the full More detail layout await block 3.
- Python adds `drawers_with_leads`, `drawers_without_leads`, disjoint
  `drawers_by_highest_severity`, `drawer_leads_total`, `whole_day_leads_total`,
  and `whole_day_lead_days` to `summary`. Preserve existing fields and meanings.
  The demo gives 9, 51, {review: 4, warn: 5, info: 0}, 16, 2, and 2.
- Whole-day means `shift_id is None`, for any rule. `deposit_lead_days`
  remains R08-only. Highest-level drawer counts use only each drawer's own leads.
- `labels.dates` maps ISO dates to English weekday/month/day/year text.
  Include range endpoints, every day/shift/flag date, bank-only dates, and
  opening/closing clock dates for shifts crossing midnight. Browser rendering
  uses this lookup without date arithmetic or the visitor's timezone.
- Reports, core calculations, response/upload limits, and transient retention
  remain unchanged. Regression tests cover count invariants and date coverage.

### M10 block 3 grouping contract (2026-10-27)

This replaces the flat-list portion of the block 2 contract above.

- Unfiltered section order is Needs review, Whole-day leads, Check, then Note,
  omitting empty sections. Each unique drawer appears once under its highest
  own lead level, ordered by date/code within that level. Whole-day leads from
  any rule group by date and sort by date.
- Drawer titles link to existing encoded drawer addresses and show register
  and server-labelled date. One visible code distinguishes same-register,
  same-date shifts. Render Python's exact difference and status, including
  unknown values, open/missing records, and balanced amounts with record leads.
- Keep every lead's original title/message/level. Drawer rule codes stay on
  Drawer details. Whole-day rule codes remain available in native disclosures;
  date groups link once to existing drawers, with no bank-only drawer links.
- Filter leads first, then group matches. Preserve the unfiltered drawer order
  and highest overall level in filtered groups. Use Matching drawers followed
  by matching Whole-day leads, without section counts. Full-run summary and
  downloaded reports stay unchanged. Status text describes filters in words.
- Preserve history replacement for filter changes, Back, breadcrumbs, heading
  focus, invalid-address normalization, and refresh recovery. Accept only own
  supported level keys, so values such as constructor normalize to All.
- Drawer details shows all own/day leads when reached from a filtered group.
  A shared lead-row renderer keeps titles, messages, labels, and rule access
  consistent; date/drawer context is supplied once by the existing page header.
- No-leads runs hide the queue heading and filters, retaining the qualified
  message, all-drawers disclosure, and report downloads. No matches retains
  filter selections and offers Show all leads. Notes-only and day-only runs work.
- More detail contains closed lead counts, day totals, cashier totals, and all
  drawers, each with a visible preview. The three tables still render lazily.
- Next-drawer navigation, a new Drawer title/outcome strip, and zero-count-row
  controls remain block 4 work, not part of this authorization.

### M10 block 4 Drawer details contract (2026-10-27)

This supersedes the earlier Drawer details layout; all prior request, filter,
report, and core-calculation contracts still apply.

- Human page/browser titles use register and the complete server-labelled date.
  Metadata retains unique drawer code, cashier ID, and times, including dates
  across midnight. Long identifiers wrap rather than clipping.
- Expected, Counted, and Difference are Python's exact strings. Difference
  status and highest own-lead level remain separate concepts. Do not infer
  record-problem severity from a small or balanced difference.
- Tick only known tape inputs. Explain that a tick means an available value,
  and an aggregate zero for safe drops does not prove a source row exists.
  Outputs and unknown inputs get no tick. Marks are decorative and static.
- Fold supplied zero rows only when another supplied row is positive. The
  native button controls their existing IDs, updates aria-expanded and its
  Show/Hide wording, and resets on each drawer. All-zero counts show all
  supplied rows and $0.00; missing counts remain unknown. Never invent rows.
- Tape/count regions have names and keyboard access for internal horizontal
  scrolling when large values need it. Outcome figures wrap within the page.
- What to look at shows full own leads, rule codes, and applicable limit_text.
  Whole-day leads and the two existing explanatory disclosures remain available.
- Python enriches only shifts[].flags[] and shifts[].daily_flags[] with
  limit_text. R01, R04, and R05 wording comes from saved flag evidence; R08
  matching-window wording uses its evidence, and mismatch review wording uses
  the report's saved configuration. Heuristics, record problems, and unexpected
  deposits get no invented limit. Global flags and report contents are unchanged.
- Keep the unique filtered drawer order from Results. Next follows that order
  without wrapping; it hides at the end and for drawers outside the list.
  All-drawers/day-link entries get Next only if they belong to the active list.
  Back links restore the active filters. Drawer details always shows full leads.
- Review checkboxes remain deferred.

### M10 Start sequence (block 5, completed 2026-10-28)

- Keep the existing title, shorter comparison lead, primary Try the example,
  and secondary Upload demo CSVs. Put the made-up month description after
  the actions. Both actions stay visible in the first 900 px at 320/1,280 px.
- The shared real example tape shows six static availability ticks, with a
  visible qualification that they do not mean the drawer balances. Calculated
  outputs remain unticked and the existing definitions stay available.
- Add an ordered Count, Compare, Review explanation below the title/tape group.
  It explains the human count, the Python comparison, and human review without
  adding an interactive task list or saved progress.
- Remove only the always-visible hosting hint. Preserve the shared request
  handler, five-second slow notice, 90-second browser timeout, duplicate guard,
  Cancel, error retry, route focus, stale-response protection, and refresh
  recovery. The upload view and server/core calculations are unchanged.
- Local evidence: [block 5](M10_BLOCK5.md). These checks do not replace the
  final cross-browser, screen-reader, zoom, or unfamiliar-user checks.

### M10 Prepare files contract (block 6, 2026-10-28)

- The two-step ordered list contains Add the seven files and Check the files.
  The native chooser and dashed drop area call the same addFiles handler;
  drops add/replace file objects without reading contents or auto-submitting.
  Non-file drags do not advertise file acceptance.
- Keep Waiting, Ready with size/tick, and Problem with the full server message.
  Ready means added; checking still happens through the existing request.
  Server-rejected files remain chosen but lose Ready and their tick. Replacing
  one clears its problem and restores Ready. Empty input selection keeps the
  chosen map; clearing the native input permits selecting an edited file again.
- Below Check my files, the live progress sentence gives the ready count and
  names still missing. With seven chosen but a Problem row, it instead asks
  for correction. Check my files refers to this sentence with aria-describedby.
  New progress wording comes from errors.py via CLIENT_MESSAGES.
- Each compact row keeps its purpose and an Example download with a filename
  in its accessible name. Optional help is a side column at 960 px and follows
  both steps below that width. Preserve both existing native disclosures.
- Keep validation limits, focused error summary and its row/input links,
  same-name replacement, slow waiting, duplicate guard, Cancel, and retry.
  Long names and full errors wrap; multiline error links align with the first
  bullet line. Native input, row, and button focus remain visible.
- Prepare and Results reuse one work-layout/work-main CSS owner. No rule,
  financial calculation, report, request cap, or result-response change.
  Evidence and verification limits: [block 6](M10_BLOCK6.md).

### Data the screens need from Python

The browser only displays values; it never calculates money or counts leads.
M8 must add these to the M7 JSON, computed in Python with integer cents:

- `line_total_amount` for each count row (denomination x quantity), for the
  count sheet. Add only this one field per count row.
- A `summary` block for the Results line: drawers checked, drawers with at least
  one "Needs review" lead, leads by severity, and days with bank-deposit leads.
  For the demo this gives 60 drawers, 4 needing review, and 16 leads in total.
- One `labels` lookup per response that maps each rule code, severity, and
  shift status to its public words from the wording table above. Define it once
  in Python so every screen uses the same words. Send it once rather than
  repeating the words on every flag; the browser looks each label up by its
  code, which is not a calculation. Keep the rule code as secondary detail.

Add tests that compare these new fields with the CLI results for the demo.

Built in M8 block 1 (2026-10-23), in `web.py`:

| Field | Shape | Demo value |
| --- | --- | --- |
| `shifts[].shift.counts[].line_total_amount` | Formatted money, from integer cents | `$400.00` for four $100 bills on `2026-09-03-R1` |
| `summary.drawers_checked` | Number of shifts in the results | 60 |
| `summary.drawers_needing_review` | Shifts with at least one `review` lead of their own | 4 |
| `summary.leads_total` and `summary.leads_by_severity` | All leads, then `info`, `warn`, and `review` counts | 16; 2, 7, and 7 |
| `summary.deposit_lead_days` | Distinct dates with an `R08_DEPOSIT` lead | 2 |
| `labels.rules`, `labels.severities`, `labels.statuses` | Code-to-words maps from the wording table | `Balanced (within $1.00)` uses the run's tolerance |

Tests check each field against the CLI's saved results, check that the line
totals add up to the counted cash for every demo shift, and check that every
rule code in `rules.py` and every severity and status has public words.

**These additions must not undo the M7 workload fixes.** The existing test
`test_combined_caps_keep_the_full_response_within_budget` fills every web limit
at once and must still succeed under the 10 MB response budget. Measured on
2026-10-23 before M8, that response was 8.2 MB (8,196,971 bytes, with 12,000
count rows and 6,019 flags), leaving about 1.8 MB. Estimates: line totals add
roughly 360 KB; repeating labels on every flag would add roughly 400 KB more,
which the single lookup avoids. Keep that test unchanged as the guard, record
the new measured size in the learning log, and do not raise the budget to make
room. Measured after block 1: 8,539,525 bytes (342,554 more), about 1.46 MB
under the unchanged budget.

### Security headers for the public site

Serve every page with a Content-Security-Policy that allows only the site
itself: `default-src 'self'; script-src 'self'; style-src 'self';
font-src 'self'; img-src 'self' data: blob:; connect-src 'self';
object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'`.
Keep `X-Content-Type-Options: nosniff` and `Cache-Control: no-store`, and add
`Referrer-Policy: no-referrer`. No inline scripts or styles are needed. Block 1
sends all four headers on every response: the page, its static files, and the
API. Tests compare the policy with the exact text above. Keep a
tight Gunicorn worker timeout, such as 30 seconds: a full-size check takes about
a second, and the browser's 90-second wait covers the host waking up, not
processing. Confirm the final values against the host's documentation during
deployment.

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

### Built in M8 block 6 (2026-10-24)

Rechecked [Render's Flask guide](https://render.com/docs/deploy-flask),
[Free tier limits](https://render.com/docs/free),
[Python version rules](https://render.com/docs/python-version), and
[Blueprint YAML reference](https://render.com/docs/blueprint-spec) on
2026-10-24:

- Render's `free` compute plan provides 0.1 CPU, 512 MB RAM, and 750 free
  instance hours per month. It spins down after 15 minutes without inbound
  traffic and takes about one minute to wake (showing Render's own loading
  page on the first visit), and its local filesystem is wiped on every spin-down
  or deploy.
- `render.yaml` defines one stateless web service (`name: drawercheck`,
  `runtime: python`, `plan: free`, `healthCheckPath: /`, and
  `PYTHON_VERSION: 3.13.5`) with no persistent disk or external database.
- Build command: `pip install ".[web]"` (installs Flask and Gunicorn without
  `pytest` or `ruff`).
- Start command:
  `gunicorn --bind 0.0.0.0:$PORT --workers 2 --worker-class sync --threads 1 --timeout 30 "drawercheck.web:create_app()"`.
  Updated during the block 6 repair: two sync workers handle two visitors at
  once, and Gunicorn can stop and replace a stalled worker after roughly
  30 seconds. The old threaded setting checked worker liveness and did not
  limit each check. This is a processing watchdog, not an exact deadline from
  when a visitor clicks: time spent waking the host or queued is separate.
  Local concurrent workload and memory evidence is in
  [the repair notes](M8_BLOCK6_REPAIR.md); Render memory was not measured.
- `test_render_blueprint_matches_stateless_gunicorn_contract` in
  `tests/test_web_page.py` checks `render.yaml` and runs `gunicorn --check-config`
  with those exact flags.
- `tests/test_web_server.py` also runs a real server over a local Unix socket,
  with a shorter timeout, and checks cancellation of stalled work, another
  visitor's success, cleanup, and recovery. The test does not use the network.
- The revised command and wording passed local checks. Repair deployment
  follow-up was confirmed on 2026-10-26 through user-provided Render logs and
  reported live checks; [the repair notes](M8_BLOCK6_REPAIR.md#public-deployment-confirmation-2026-10-26)
  distinguish this evidence from direct agent observation. The detailed
  live-site checks below describe the original deployment before the repair.
- Verified on the live public URL
  [https://drawercheck.onrender.com](https://drawercheck.onrender.com) on
  2026-10-24 after [GitHub Actions run 40075833849](https://github.com/GutsJr75/DrawerCheck/actions/runs/40075833849)
  passed on Python 3.12, 3.13, and 3.14:
  - `GET /` returned 200 with the exact planned `Content-Security-Policy`,
    `Referrer-Policy: no-referrer`, `X-Content-Type-Options: nosniff`, and
    `Cache-Control: no-store`.
  - `POST /api/demo` and `POST /api/check` (with all seven synthetic CSVs)
    returned identical results (60 drawers, 4 needing review, 16 leads, 2
    deposit-lead days) and reports matching the local CLI.
  - All seven `GET /examples/<file>` downloads matched `data/demo/*.csv`
    byte-for-byte.
  - In a fresh browser session, `Try the example`, the 7-file upload on Prepare
    files, downloading `drawercheck.html`, `drawercheck.csv`, and
    `drawercheck.txt`, opening `2026-09-03-R1`, and opening a drawer address in
    a fresh tab (`"Results are not saved"`) all worked with zero console errors
    and zero requests to other domains. Live screenshots are in
    `docs/screenshots/2026-10-24-m8-block6/`.

## Milestones and files

Each work block targets 30 to 60 minutes. Split a growing block; do not remove
required correctness or data-isolation checks to meet the earlier time estimate.

| Milestone | Work blocks | Main files |
| --- | --- | --- |
| M7: Web request handling | Optional package setup and application entry point; upload/demo pipeline with temporary cleanup; errors, limits, isolation, and parity tests. | `src/drawercheck/web.py`, `errors.py`, `pyproject.toml`, `tests/test_web.py`, CI updates |
| M8: Screens and delivery | Python additions for the screens (summary, count line totals, public labels) and the base layout with tokens and fonts; Start and upload screens; Results and Drawer details; filtering, downloads, navigation, and user states; accessibility and browser verification; hosting configuration and public smoke check; README/screenshots and interview update. | `src/drawercheck/web.py`, `src/drawercheck/templates/`, `src/drawercheck/static/` (including fonts and their license), package-data setup, `render.yaml`, `README.md`, `docs/INTERVIEW_NOTES.md` |

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
- Check WCAG 2.2 AA on every view in light and dark mode: an automated
  accessibility scan with no violations, plus a manual pass covering the
  keyboard, focus visibility, a 320-pixel-wide screen, text resized to 200%,
  browser zoom at 400% in a 1,280-pixel-wide desktop window (equivalent to a
  320 CSS-pixel viewport), reduced motion, and screen-reader announcements for
  loading, results, and errors. Report which tools were actually used.
- Check Cancel during a deliberately slowed check: the view returns to its
  previous state, and a response arriving afterwards is ignored.

Checked in M8 block 5 (2026-10-23) and rerun in the block 5 repair
(2026-10-24). Tools actually used: Playwright 1.64 (the copy the Playwright
plugin installed) driving Google Chrome 156 and Playwright's WebKit 26.6 build,
and axe-core 4.14.0 (checksum verified) for the automated scan. No real screen
reader was run. On 2026-10-26 the user confirmed no unfamiliar participant has
tried the site and deferred a possible friend usability check until later.
Neither manual check is claimed as passed; [the M8 checklist](M8_CHECKLIST.md)
records how to finish them.

Every check confirms the expected view and address before it scans, measures,
or takes a screenshot. Moves inside the app change the address's `#` part in
the page, because WebKit reloads the page when asked to open the address it is
already on, which clears the results.

| Check | Result |
| --- | --- |
| axe-core, WCAG 2.0 to 2.2 A and AA rules | 0 violations in 136 scans: 17 views and states (Start, waiting, time-out, not saved; Prepare files empty, missing files, a file problem, a connection failure; Results plain, filtered, no matches, all sections open; four drawers and the missing-drawer view) in both themes, at 1,280 and 320 px, in Chrome and WebKit. axe's best-practice rules also report 0. |
| Keyboard, in Chrome (Tab) and WebKit (Option+Tab, Safari's default for links and buttons) | Every Tab stop shows the 3 px ring. The example run, filters (arrow keys on the levels, typing on the date list), drawer links, line meanings (Enter and Space), Back to results, a report download, the error summary links, and Cancel all work without a mouse. |
| Reflow and zoom | No view scrolls sideways at 320 px; 400% zoom in a 1,280 x 800 window (320 x 200 CSS px) stays 320 px wide on every view in both engines. Block 5 had measured Start in place of three WebKit views; the repair confirmed each view first. |
| Text at 200% | With the root text doubled at 1,280 px, no view widens or clips text. |
| Reduced motion | The 150 ms colour transitions drop to 0 seconds. |
| Announcements and tree | The live region says "Results are ready.", the busy text, the slow-start sentence, and "Stopped waiting."; errors use alert regions and the summary takes focus. The accessibility tree names every region, heading, table, control, and link. |
| Requests | Every request in every run went to the local site; no other website was contacted. |

Fixed during block 5: Drawer details tape row headers were named only "Plus",
"Minus", or "Equals" because each label sat inside its definition toggle; they
now carry the whole line ("Minus Cash refunds"). The date list was 25 px tall in
WebKit, which ignores sizing on native drop-downs; it now has its own arrow and
is 44 px everywhere. Drawer details widened to 1,469 px with 200% text; its two
columns now appear only when both fit. The demo notice moved inside the header
landmark, a favicon removed a 404 on every visit, and `.playwright-mcp/` is now
ignored by Git.

Known and accepted: WebKit logs one "Refused to apply a stylesheet" message for
the date list's built-in styling under the strict style policy; the list works
and looks right, and loosening the policy to silence it is not worth it.
Pressing the down arrow on a closed date list opens the menu on macOS rather
than changing the date. Text at 200% on a 320 px screen (beyond WCAG's
separate 200% text and 320 px tests) still widens Drawer details to 509 px.

Open from the block 5 repair: each Drawer details tape row header is named,
for example, "Minus Cash refunds" and also contains the hidden word "Minus".
Check with VoiceOver whether it is spoken twice before changing it, because
removing the hidden word could drop the operator in screen readers that read a
cell's contents rather than its name.
- Check the Back and Forward buttons, refresh, and a copied drawer address,
  including the "Results are not saved" message. Check that the browser makes
  no requests to other websites and that the performance budget in DESIGN.md
  is met.
- Compare each view with DESIGN.md: tokens, fonts, the drawer tape, the count
  sheet, the plain-facts summary, and the "What to avoid" list. Record
  screenshots of each view on desktop and phone widths, committed as a dated
  timeline folder under [docs/screenshots/](screenshots/README.md) following
  the screenshot rule in AGENTS.md.
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
| `GET /examples/<file>` | One of the seven CSV names (added in M8 block 2) | That file from the built-in example, as a download. |

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
`flags`, `shifts`, and `reports`. M8 block 1 added `labels` and `summary`, plus
`line_total_amount` on each count row. Money fields use names ending in `_amount`
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
At the M7 handoff, the interface, browser/usability checks, and observed public
deployment were still M8 work. The delivery status and remaining manual checks
are now recorded at the top of this document and in the [M8 checklist](M8_CHECKLIST.md).

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
