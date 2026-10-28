# Visual redesign plan: "Tick and tie"

**Status: M10 blocks 1/2 completed locally on 2026-10-26; blocks 3/4
completed locally on 2026-10-27; blocks 5/6 and block 7 local verification
completed on 2026-10-28. Final hosted verification of block 7 fixes and
manual checks remain open.**
[Block 1 evidence](M10_BLOCK1.md) covers the shared design,
[block 2 evidence](M10_BLOCK2.md) the Results summary/layout,
[block 3 evidence](M10_BLOCK3.md) grouping and filters, and
[block 4 evidence](M10_BLOCK4.md) Drawer details and navigation, and
[block 5 evidence](M10_BLOCK5.md) Start and its recovery flows, and
[block 6 evidence](M10_BLOCK6.md) Prepare files and upload guidance.
[Block 7 evidence](M10_BLOCK7.md) and the [current checklist](M10_CHECKLIST.md)
separate local passes, observed block 6 hosted results, and remaining checks.

The sequence is M10, then M9 R06 and R07. [DESIGN.md](../DESIGN.md) and
[WEB_PLAN.md](WEB_PLAN.md) describe the current app, including the new shell;
this document specifies the later redesign work. Each future block needs its
own continuation and updates the relevant current-contract sections.

The private [concept canvas](https://claude.ai/artifact/4HZ3thdSfEQS3trS32zqBv#page-dcb81aee8d83)
provides the visual starting point. The [archived review](screenshots/2026-10-26-redesign-concept-review/README.md)
covers all four desktop light-theme views. Dark mode, mobile layouts, and
prototype interactions were not verified. The canvas has not been updated to
match this revised plan; the written decisions below take priority where they
differ. Its figures come from the fictional built-in demo, not real records.

## 1. What is wrong today

The user's feedback: pages feel crammed, sections are not separated, and the
look is not distinctive. The initial proposal identified the issues below;
the current templates and lead renderer confirm the repeated rows, code-heavy
titles, and download placement. The archived screenshots above show the
proposed replacement, not new captures of the running app.

| Cause | Where it shows |
| --- | --- |
| **One distance for everything.** Gaps between unrelated sections (summary, downloads, filters, list) are 16 to 24 px, about the same as gaps inside a group. The eye cannot tell where one topic ends. | Results, Prepare files |
| **Flat hierarchy.** Section headings are 20 px against 16 px body, and every block has the same weight. Nothing says "start here". | All views |
| **Repetition instead of grouping.** Results shows 18 leads in one list: 16 belong to nine drawers and two belong to whole days. Multiple leads repeat the same drawer details. | Results |
| **Wrong item leads.** Downloads sit above the review list and use the main button style, so the page's first action is "download", not "review". | Results |
| **Too many small grey lines.** Most rows have a 14 px muted line, and hints stack two or three deep. Small grey text reads as noise. | Results, Prepare files, Start |
| **Codes in human places.** The drawer page title is `Drawer 2026-09-03-R1`, and rule codes appear on every Results row. | Results, Drawer details |
| **Weak page frame.** The page background and panels are almost the same colour, and the header is a plain word on a line. | All views |
| **Note looks like a link.** The Note label uses the accent teal, so a hint looks as important as an action. | Results, Drawer details |
| **Always-visible hosting detail.** Start shows the sleeping-server explanation before anyone encounters a delay. Keep the existing waiting message and README explanation instead. | Start |
| **Generic look.** IBM Plex plus marine teal on blue-grey reads like many developer tools. The torn tape edge is the only element with character. | All views |

## 2. What "comfortable" means here

The audience knows neither code nor cash drawers (see WEB_PLAN.md). Comfort for
them comes from five things, each of which the redesign targets directly:

1. **Calm rhythm.** Space does the grouping. Three spacing roles, so a visitor
   can feel where one topic ends. Based on the Gestalt law of proximity, which
   NN/g notes can outweigh colour or shape as a grouping cue.
2. **Easy reading.** A typeface designed for low-vision readers, 17 px body,
   lines under 70 characters, and no stacks of small grey text.
3. **Colour with a job.** Blue means "you can act". Red and amber pencil mean
   "look here". Green accompanies a written availability or no-leads status,
   never an unsupported claim that records were verified.
4. **A clear overview.** The summary says where to look and how many drawers
   have no leads. No leads is not proof of an exact match or complete records.
5. **Details on demand.** Essentials first, explanations one click away and
   never more than one level deep (progressive disclosure).

## 3. The theme: Tick and tie

"Tick and tie" borrows the visual language of checking figures against records.
It gives the site an identity drawn from its subject. DrawerCheck applies
limited example rules to supplied data; it does not verify the underlying
business records. The tick meanings below preserve that distinction.

### Colour

Pale ledger paper, a blue pen for actions, red and amber pencil for review
levels, and green for labelled status cues. The listed pairs were independently
recalculated on 2026-10-26 and meet the relevant AA contrast thresholds: 4.5:1
for ordinary text and 3:1 for control boundaries. This verifies those pairs,
not full WCAG 2.2 AA conformance. Actual backgrounds, hover, focus, errors,
and disabled states still need implementation checks.

| Token | Role | Light | Dark | Contrast on surface (light / dark) |
| --- | --- | --- | --- | --- |
| `page` | Ledger paper background | `#E8EEE5` | `#121A16` | |
| `surface` | Sheets, inputs | `#FBFCF8` | `#1A2520` | |
| `text` | Pine ink | `#1C2A23` | `#E5EDE6` | 14.5 / 13.2 |
| `muted` | Supporting text | `#4E6157` | `#A8B9AE` | 6.4 / 7.7 |
| `line` | Dividers only | `#C8D6C6` | `#33443B` | decorative |
| `control` | Control borders, dashed tape rules | `#6E8476` | `#7F978A` | 3.9 / 5.0 |
| `accent` | Blue pen: buttons, links, focus | `#2747A6` | `#A3B6FF` | 8.0 / 8.0 |
| `on-accent` | Text on the main button | `#FFFFFF` | `#121A16` | 8.3 / 9.0 |
| `review` / bg | Red pencil: Needs review, "Short" amounts | `#A3302A` / `#F8E6E2` | `#FF9E92` / `#3D2522` | 5.8 / 7.1 on bg |
| `check` / bg | Amber pencil: Check | `#7A5200` / `#F6EAD0` | `#F0C26A` / `#3A3020` | 5.8 / 7.8 on bg |
| `note` / bg | Graphite: Note | `#3D4E46` / `#E3EAE3` | `#C6D2CA` / `#27332D` | 7.2 / 8.4 on bg |
| `ready` / bg | Tick green: labelled availability or no leads | `#2C6A44` / `#E0EFE3` | `#93D3A6` / `#1F3A2A` | 5.4 / 7.1 on bg |

Dark mode is "after closing": a deep pine desk, not near-black.

The proposed change from teal to blue-pen and pencil colours is an aesthetic
choice that supports the ledger theme, not a claim that teal is less usable.

### Type

- **Atkinson Hyperlegible Next** for all text, and **Atkinson Hyperlegible
  Mono** for money only. The [Braille Institute](https://www.brailleinstitute.org/freefont/)
  describes their distinctive letterforms. The Google Fonts sources include
  SIL Open Font License 1.1
  files for [Next](https://github.com/google/fonts/blob/main/ofl/atkinsonhyperlegiblenext/OFL.txt)
  and [Mono](https://github.com/google/fonts/blob/main/ofl/atkinsonhyperlegiblemono/OFL.txt),
  checked on 2026-10-26. Keep the matching copyright notices and licences with
  the shipped fonts; record the exact asset source and version in block 1.
- Why: they were designed so that easily confused characters (0 and O, 1 and l,
  5 and S) look different. For a money tool aimed at beginners, that is the
  comfort argument and the accessibility argument at once.
- Self-hosted Latin subsets, as today. No font request to another site; the
  canvas's external preview fonts are not a production exception. Use
  `font-display: swap` and the existing system-font fallbacks.
- Scale: 52 (Start title), 40, 30, 26, 19, 17 body, 15 small. Weights 400, 600,
  700. Line height 1.55 body, 1.1 to 1.25 headings. Nothing under 15 px except
  the 14 px status labels. On phones, reduce the Start title to about 34 px and
  other page titles to about 30 px; retain body size and readable wrapping.

### Space and shape

- **Three spacing roles.** 8 to 12 px inside one item, 16 to 24 px between
  items in a group, and 32 to 64 px between topics. Use the smaller topic gaps
  on phones and above the Results list. These are roles, not three rigid pixel
  values. Keep headings closer to the content they introduce.
- **One sheet per section.** Each section is one surface panel with thin rules
  between rows, never a grid of separate cards.
- Corners: 4 px labels, 8 px controls, 12 px sheets. No shadows or gradients.
- Content up to 1,200 px. Results and Prepare files use a main column with a
  side column that stacks below 960 px.
- Keep the Results header and summary compact. At a 1,280 x 900 CSS-pixel
  viewport and normal zoom, the first review drawer's title and outcome should
  be visible without scrolling. Do not shrink body text or hide information to
  meet this target; at zoomed and narrow widths, readable reflow takes priority.

### Signature elements

Spend the boldness in one place:

- **The tick.** One consistent mark with an explicit meaning in each context:
  a file is selected and passes the existing browser prechecks; a known tape
  input is available for the calculation; or a drawer has no leads from these
  checks. A Ready file has not yet passed the server's full validation. The
  logo mark is decorative. No tick means "audited", "resolved", or an exact
  match, and no tick marks a person.
- **The drawer tape** stays, with its torn edge. Ticks may accompany known
  inputs with the legend "Ticked values are available for this calculation."
  An aggregate zero for safe drops is not proof that a source row exists.
  Unknown inputs and calculated outputs receive no tick. Decorative marks are
  hidden from screen readers; meaningful ones have the same accessible wording
  as their visible explanation, without repeating every label twice.
- **One motion.** On Results, the summary's ticks draw in once (about 600 ms).
  `prefers-reduced-motion` shows them still. No other animation.

## 4. View by view

### Start

- Larger title and lead, the two actions, then one line about the example.
- The tape stays beside the title, now with ticks, and is the page's picture.
- New "How a check works" section with three numbered steps (count, compare,
  review). Numbering is honest here because it is a real sequence.
- Remove the always-on sleeping-server hint. The existing 5-second waiting
  message already covers a slow check.

### Prepare files

- Two numbered steps: "Add the seven files", then "Check the files".
- A dashed drop area with the normal **Choose files** button inside it.
- The checklist becomes compact rows: status, filename, size, one-line purpose,
  and an "Example" link. Ready rows carry the tick.
- Under the button, say which files are still needed by name.
- Help moves to a side column: a short "Not sure what goes in a file?" note and
  the two existing disclosures.
- Preserve replacement of same-named files, row-specific problems, the focused
  error summary and its links, retry, waiting, and Cancel. Below 960 px, show
  file selection and checking before optional help. Every Example link must
  identify its filename to assistive technology.

### Results (largest change)

The figures below are expectations for the current built-in example. Render
the response values and appropriate singular/plural wording for every run.

- Use the title "Results" and one server-labelled date range. Do not hard-code
  September or assume uploads cover one month or year.
- **Summary slip, labelled "Full run":** "9 of 60 drawers have leads to
  check." A supporting line says "16 drawer leads; 2 whole-day leads on
  2 dates." The highest-level drawer counts belong in the section headings,
  not repeated as another summary row.
- Show "51 drawers with no leads" with "No leads found by these checks."
  Remove the concept's "Nothing to look at for these". A small difference
  within tolerance may have no lead; no green claim of an exact match.
- **Group leads by drawer.** One entry per drawer: a human title such as
  "Register R2, Tuesday, September 8, 2026", the difference with its word on the
  right, and its leads underneath. 18 rows become 9 drawers and 2 days.
- **Unfiltered sections:** Needs review (4 drawers), Whole-day leads (2 dates),
  Check (5 drawers), then Note when needed. Omit empty sections. Drawers appear
  once, in their highest own lead level. Within a level, sort by date then
  unique shift code; preserve severity order within each drawer's leads.
  Whole-day leads group by date and include any rule, not just bank deposits.
- **Side column:** "Show" filters, "Keep a copy" downloads with the
  results-disappear warning, and "What the levels mean". All three downloads
  use secondary styles, never a solid main button. Drawer titles are clearly
  labelled links with visible focus. Filters precede the list in both reading
  and keyboard order; downloads follow it. On phones use summary, filters,
  list, downloads, then optional detail. Desktop columns must preserve that
  same meaningful order without duplicated controls or positive `tabindex`.
- Rule codes leave Results rows and appear on Drawer details. Whole-day leads
  keep theirs in a disclosure, so codes stay available as WEB_PLAN.md requires.
- Tables move to a "More detail" section with one-line previews. Put detailed
  lead counts in a disclosure here: "18 leads total: 7 Needs review, 7 Check,
  4 Note." Keep these counts separate from drawer totals and out of the main
  summary so its new layout does not recreate the crowded concept.

#### Filters and next-drawer navigation

- Filter individual leads by date and level first, then group the matching
  leads by unique shift code or whole-day date. Selecting Note must find a
  note on a drawer that also has a Needs review lead.
- While a filter is active, use one grouped drawer list followed by matching
  whole-day groups. Retain the unfiltered drawer order and show each drawer's
  highest overall level alongside its matching leads. Omit section counts
  and describe the filters in words; do not calculate displayed counts in JS.
- The summary remains labelled "Full run" and never implies filtered totals.
  Drawer details always shows all of that drawer's leads and its daily leads,
  even when opened from a filtered list. Back to results restores the filters.
- "Next drawer with leads" follows the unique drawers in the filtered list,
  with no wrap-around. On the last drawer, show "Back to results". A drawer
  opened from All drawers or a whole-day link gets Next only if it belongs to
  that list. Dates without any drawers have no drawer links.
- Keep the existing hash addresses, history replacement on filter changes,
  view-heading focus, refresh recovery, and invalid-address fallback.

### Drawer details

- Title in words: "Register R1, Thursday, September 3, 2026". Include the year
  for uploaded ranges that cross years; use this same complete format
  consistently. The unique shift code, cashier ID, and times sit underneath
  and wrap when needed. A register/date alone is not a unique shift identifier.
- **Outcome strip:** Expected cash, Counted cash, Difference with its word and
  level, as three large figures.
- Tape and count sheet side by side, stacked on phones. Hide supplied rows
  whose quantity is zero behind "Show bills and coins with none counted";
  the button has `aria-expanded` and controls those rows in the same table.
  Omit the button when there are no such rows. If every supplied quantity is
  zero, show all rows and the real $0.00 count. An absent count remains unknown;
  never invent zero rows for denominations missing from the source.
- "What to look at": each lead with its level, message, the limit that applied,
  and the rule code.
- "More about this drawer": the two existing explanations, each with a one-line
  preview.
- A "Next drawer with leads" link at the bottom, so review flows without
  returning to Results each time.
- Keep whole-day leads and deposit explanations visible or available as today.
  Only show a rule-specific limit when that rule has one. Do not infer a
  missing-record lead's severity from the displayed cash difference.
- Do not add the concept's "Looked at" checkboxes in this scope.

### Every view

- Header on the surface colour with the logo mark. Breadcrumbs replace the
  lone "Back to" links.
- The demo notice strip stays at the top of every view, unchanged in wording.
- A shorter one-row footer.
- Footer, header, breadcrumbs, and identifiers may wrap on narrow screens.
  Preserve the skip link, semantic headings, explicit labels, written statuses,
  focus visibility, live announcements, and the existing security headers.
  Keep the footer's learning-project boundary, file-deletion explanation, and
  source/report links.

### Required states beyond the built-in example

| State | Required behavior |
| --- | --- |
| No leads | Say "No leads found by these checks"; retain the full-run summary, all-drawers access, and downloads. No review queue or green verification claim. |
| No filter matches | Explain that no leads match, offer Show all leads, retain selected filters and the full-run summary. |
| Only Notes | Show the Note section and allow opening each affected drawer. |
| Whole-day leads only, including bank-only dates | Keep them visible even with no drawer leads. With zero drawers, say "No drawers in this run" instead of "0 of 0". |
| Missing POS, absent count, or open shift | Preserve unknown amounts, the reason, and applicable leads; do not show a completion tick. |
| Balanced amount with a record problem | Keep the exact difference, tolerance wording, and Needs review label together. |
| Multiple shifts per register/date, long IDs, or multi-year dates | Group by unique shift code; show enough identifying context and wrap without clipping. |
| Slow, cancelled, failed, or refreshed check | Preserve current waiting, retry, Cancel, late-response protection, and unsaved-results recovery. |

## 5. Changes needed outside CSS

All money, displayed summary counts, public labels, and date wording stay in
Python. The browser groups, orders, filters, and renders existing values. No
framework, new reconciliation rule, database schema change, or saved review
state is needed.

Add the following full-run fields to the existing `summary` without changing
the meaning of its current fields. "Drawer lead" means a flag with a shift
identity; "whole-day lead" means one without. A drawer's highest level comes
only from its own flags, not the day's flags.
Use `shift_id is None` to identify whole-day flags in Python; the current web
response gives those flags an empty `shift_code`, not a null code.

| Proposed field | Meaning | Current demo |
| --- | --- | --- |
| `drawers_with_leads` | Unique shifts with any own lead | 9 |
| `drawers_without_leads` | Shifts with no own leads | 51 |
| `drawers_by_highest_severity` | Disjoint drawer counts for `review`, `warn`, `info` | 4, 5, 0 |
| `drawer_leads_total` | Leads attached to shifts | 16 |
| `whole_day_leads_total` | Leads without a shift identity, any rule | 2 |
| `whole_day_lead_days` | Distinct dates with those whole-day leads | 2 |

Assert in Python tests that the first two counts sum to `drawers_checked`, the
highest-level counts sum to `drawers_with_leads`, and the two lead totals sum
to `leads_total`. Existing `drawers_needing_review` must equal the highest
review drawer count. Existing `deposit_lead_days` continues to count R08 only.

| Change | Owner | Why |
| --- | --- | --- |
| Add the summary fields above | `web.py`, `tests/test_web.py` | Distinguish leads, drawers, and dates without browser arithmetic. |
| Add shared `labels.dates`, keyed by ISO date, with weekday, month, day, and year | `web.py` | Cover range endpoints and every shift, day, and flag date, including bank-only dates. Do not derive weekdays from browser time zones. |
| Group leads by shift and order shifts by highest level | `app.js` | Presentation only, built with DOM methods. No `innerHTML`, which a test forbids. |
| Next drawer with leads | `app.js` | Uses the order already on the page. |
| Replace fonts and retain the matching licences | `static/fonts/` | Must stay under the 200 KB font budget; measure in block 1 before completing the font switch. |
| Rewrite tokens and the contrast test pairs | `app.css`, `tests/test_web_page.py` | The test recalculates every pair from the stylesheet. |
| Update visual and interaction rules as each block ships | `DESIGN.md`, `docs/WEB_PLAN.md` | Keep current behavior distinct from this proposal and historical M8 evidence. |

Unchanged: rule/severity/status labels, neutral flag language, `#/` addresses,
upload and processing limits, temporary workspaces, the 60 KB combined CSS/JS
budget before compression, no third-party requests, and the WCAG 2.2 AA target.
Preserve the 10,000,000-byte response cap and
`test_combined_caps_keep_the_full_response_within_budget`; measure the new
response size rather than increasing the cap. Keep DOM text insertion safe.
The downloadable reports retain their existing calculations, contents, and
styles. New summaries must agree with the core and reports.

## 6. Delivery as M10, one block at a time

These are seven planned work areas, with Results and Drawer details before
Start-page polish. Target 30 to 60 minutes per block, not a guaranteed total.
Split an area into smaller recorded blocks if needed; never drop checks to
fit the estimate. Each authorized block ends with tests, both Ruff checks,
`git diff --check`, a plan update, three learning-log bullets, and a commit,
then stops for `next`. Any visible change gets screenshots in a new dated
folder and a timeline entry. Never modify earlier screenshot folders.

| Block | What gets built | Done when |
| --- | --- | --- |
| 1 | Tokens, fonts, responsive type and spacing, shared header, notice, footer, logo, breadcrumbs. Update the affected DESIGN.md sections. | Actual contrast pairs and font/code budgets pass; all four current views still work at 320 and 1,280 px in both themes. |
| 2 | Results summary, quiet downloads, responsive side column, Python summary/date additions. | Count invariants and date coverage pass; combined response-cap test passes; keyboard and mobile order agree; the summary uses accurate units. |
| 3 | Results grouping, severity sections, filters, More detail, and required empty states. | Mixed-level Note filtering, day-only leads, no matches, stable unique grouping, Back, and address cases pass; first drawer visible at the desktop target. |
| 4 | Drawer details: human title, outcome strip, zero-row toggle, tape ticks with explicit meaning, full drawer/day leads, next-drawer navigation. | Unknown and all-zero counts stay distinct; exact tape values remain unchanged; next-drawer sequence respects filters and ends without wrapping. |
| 5 | Start: title, tape, How a check works, remove the always-on sleeping-server hint. | Example and upload entry points, waiting, Cancel, retry, and refresh recovery still work; first actions stay clear at 320 and 1,280 px. |
| 6 | Prepare files: steps, drop area, compact checklist, side help. | Error summary still takes focus and links to rows. |
| 7 | Cross-view verification, README/screenshots and interview notes, then observed CI and deployment checks after publication. Split local checks and hosted follow-up if needed. | Run the acceptance checklist below; report local, hosted, and unverified checks separately. No deployment claim from a local pass. |

### Acceptance checklist

- Check changed views in light and dark at 320 and 1,280 px during their own
  blocks, not only at the end. Final review also covers an intermediate width
  near the side-column breakpoint and long identifiers.
- Verify 400% browser zoom in a 1,280-pixel window separately from 200% text
  resizing; no lost controls or page-wide horizontal scroll. Table scrolling
  stays inside labelled regions.
- Run keyboard-only navigation, focus/reading order, error-link focus,
  announcements, reduced motion, targets, and contrast checks in Chrome and
  WebKit. Preserve working links and native form controls.
- Exercise every state in the table above, including a Note attached to a
  Needs review drawer, no filters matching, all-zero counts, an absent count,
  and a whole-day date with no drawers. Use fake fixtures only.
- Compare original and redesigned demo outcomes: 60 drawers, nine with leads,
  16 drawer leads plus two whole-day leads; all amounts and all 18 flag tuples
  unchanged while R06/R07 remain unimplemented. Verify report downloads too.
- Measure fonts, CSS/JS, and the full capped response. Observe that production
  pages make no third-party requests and preserve security/cleanup behavior.
- After the user publishes, inspect the actual CI result and deployed revision,
  run the example and a seven-file fake upload, and open all report formats.
  Record any automatic deployment separately from an agent deployment action.
- A real screen-reader session and a first-time visitor usability check remain
  open from M8. Carry them forward honestly if unavailable; screenshots and
  automated checks are not substitutes or full accessibility certification.

## 7. Authorization and deferred work

The proposed package is the ledger palette, Atkinson fonts, grouped review
flow, corrected wording, and the seven work areas above. Default scope excludes
"Looked at" checkboxes and restyling the downloadable HTML report. Both can be
requested later and are not prerequisites for this redesign.

The user approved **M10 block 1 under this plan, before the remaining M9
rules**, on 2026-10-26, then explicitly authorized **block 2** with "go for
block 2", then authorized **blocks 3, 4, and 5** separately on 2026-10-27.
Block 6 was separately authorized on 2026-10-28 with "Go for it".
Block 7 local checks were separately authorized and completed on 2026-10-28.
All views and local checks are delivered. Two QA fixes await publication and
final hosted verification; real browser zoom, a screen reader, and usability
testing remain unverified. Approval does not authorize
running all seven areas unattended. Once M10 is delivered, return to M9 R06,
then R07, with their existing per-block review stops. New rules may change
group membership, severity, and counts; the frontend must remain generic
rather than relying on today's demo distribution.

## Sources

- [NN/g: Proximity principle in visual design](https://www.nngroup.com/articles/gestalt-proximity/)
- [NN/g: Progressive disclosure](https://www.nngroup.com/videos/progressive-disclosure/)
- [GOV.UK Design System: Task list](https://design-system.service.gov.uk/components/task-list) and its [2023 research update](https://designnotes.blog.gov.uk/2023/12/15/working-as-a-community-to-iterate-the-task-list-pattern/): whole rows clickable, sentence-case status labels.
- [Atkinson Hyperlegible Next](https://fontsource.org/fonts/atkinson-hyperlegible-next/about) and [Mono](https://fontsource.org/fonts/atkinson-hyperlegible-mono/about): OFL 1.1.
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
