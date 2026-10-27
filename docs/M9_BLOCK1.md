# M9 block 1: possible swapped digits

Authorized and verified locally on 2026-10-26. Hosted CI and public HTTP checks
were subsequently observed the same day; see the follow-up below. M9 is split into three blocks:
R03, R06, and R07. This block completes R03 only. Stop for review before R06.

## Behavior and scope

R03_TRANSPOSITION_HINT adds an info-level lead when the magnitude of a known
cash difference is a whole-dollar amount of at least $9 and divisible by 9.
Both overages and shortages qualify. The public label is **Possible swapped
digits**; the message is **Could be two digits swapped when typing a total.
Hint only.**

This is a heuristic, a rough clue only. For example, typing $52 instead of $25
creates a $27 difference, but many unrelated differences are also divisible
by nine. R03 does not establish that a typo happened or identify original
digits. It does not change the cash calculations, existing leads, or severity.
It does not guess when cash is unknown, a shift is open, the difference is
fractional dollars, or its magnitude is below $9.

Implementation reuses the pure Python rule registry, saved evidence, shared
report data, web label lookup, and existing browser lead rendering. No new
browser arithmetic, control, stylesheet, dependency, or CSV schema was added.
The saved policy version is now 5. Earlier saved results prompt reconciliation
again; reconciling a subset under the new policy clears incompatible results
from other dates rather than mixing rule sets. A full rerun is recommended
for an existing command-line database after upgrading.

## Demo and reports

The deterministic demo CSVs are unchanged. Their existing $45 shortage on
September 8 and $9 shortage on September 18 now each get one R03 note. The
default total is 18 leads: 4 info, 7 warn, and 7 review. It still checks 60
drawers, 4 drawers need review, and 2 dates have bank-deposit leads. The
original 16 leads and all cash/deposit amounts remain unchanged.

The requested +$27 over example is covered in the focused rule tests rather
than injected into the public CSVs. The committed offline sample was regenerated
through the real importer, reconciliation, and HTML renderer with 18 leads.
The exact golden table, CLI, web summary, exports, and server-recovery test
expectations were updated together.

## Verification

| Check | Result |
| --- | --- |
| `.venv/bin/pytest -q` with local Unix-socket permission | PASS: 708 tests in 13.59 seconds, including the unchanged response-cap regression and real server recovery test. |
| `.venv/bin/ruff check .` | PASS. |
| `.venv/bin/ruff format --check .` | PASS. |
| R03 boundaries | Both signs; $9 minimum; +$27 example; cents, below-boundary, and nonmultiples rejected; unknown/open data suppressed; large integer amounts checked without rounding. |
| Stored results and reports | R03 evidence survives saving/explanation, text/HTML/CSV exports, filtered reconciliation, and repeated runs. Old policy snapshots are rejected and incompatible dates cleared on rerun. |
| Default demo, JSON, labels, and offline sample | Exact 18-lead set matches the documented table and every export; public label coverage and CLI/web parity pass. |
| Real browser | Native Google Chrome against localhost: built-in example, 18-lead summary, Note filter, both new hints, drawer details, Back retaining the Note filter, and Tab/Enter opening the R03 drawer link worked. Console showed zero messages when inspected. |
| Narrow viewport | At 320 CSS px, the drawer's new label, message, and rule code wrap inside the existing lead panel; inspected and captured in dark mode. |
| Screenshot timeline | Three new inspected images in `screenshots/2026-10-26-m9-block1/`, dated 2026-10-26. Browser chrome and DevTools cropped with sips from 2x captures. |
| Generic strict frontend audit | Exit 2, with the same eight findings as the baseline before this block; raw result in `M9_BLOCK1_AUDIT.json`. No strict audit pass is claimed. |
| Document links, punctuation, and `git diff --check` | PASS. |

During development, one new migration test initially used the wrong exception
and database column name; those test mistakes were corrected to the existing
contract. The first full run then found two deposit tests still expecting the
old demo count. Their assertion now checks that the one-cent deposit change
adds exactly one lead. After sample regeneration and those corrections, the
final full suite passed. No new application failure remains from these runs.

The generic auditor cannot follow this project's external JavaScript event
listeners, so seven functioning buttons are reported as actionless. Its eighth
finding requires machine-readable native-select ownership; the ownership is
already documented in DESIGN.md, and the date control is unchanged. The raw
findings match the pre-change baseline exactly. No inline handlers, weaker CSP,
or unrelated control rewrite was introduced to silence the tool.

## Limits and next block

At the end of the implementation session, M9 had not been pushed or deployed
by the agent, and only local results were claimed. The subsequent hosted and
public checks below replace that pending status. The agent made no Render
setting change or deployment during either verification session.

No new full accessibility, cross-browser, light-theme, zoom, capacity, or Render
memory audit was run. Earlier M8 evidence remains historical. A real screen
reader and the user-deferred friend usability check remain open.

Next, after **next**, implement R06 (high cash sales with no recorded safe
drop) using the existing example threshold. R07 needs its historical median
details settled before its later block. No R06 or R07 rule is registered here.

## Public verification follow-up, 2026-10-26

The user subsequently pushed and deployed M9 block 1. Independently inspected
GitHub Actions [run 40426134663](https://github.com/GutsJr75/DrawerCheck/actions/runs/40426134663)
for `c5af7a4ad4818a7d136b4e36159c2d8459c7eb66`: completed successfully.
Python 3.12, 3.13, and 3.14 all passed lint, formatting, core tests, installed
CLI help, and optional web/server tests. The run began at 00:23:56 UTC on
2026-10-27, which is 17:23:56 PDT on 2026-10-26. This run verifies the
implementation commit, not this later documentation update.

The following live checks were run on 2026-10-26 against
`https://drawercheck.onrender.com`, using Python's standard-library HTTPS
client and only the repository's fictional demo files:

| Request or check | Observed result |
| --- | --- |
| `GET /` | HTTP 200; exact expected Content-Security-Policy, Cache-Control, Referrer-Policy, and X-Content-Type-Options values; current upload label and refresh reminder present. |
| `POST /api/demo` | HTTP 200; 60 drawers, 4 needing review, 18 leads, 2 bank-deposit lead days; severities 4 info, 7 warn, and 7 review. |
| R03 labels and flags | Public label "Possible swapped digits"; exactly two info hints for 2026-09-08-R2 and 2026-09-18-R1; both messages say "Hint only." |
| Seven `GET /examples/<file>` downloads | HTTP 200; every file matched its `data/demo` repository bytes. |
| `POST /api/check` with all seven demo CSVs | HTTP 200; all response fields other than generation timestamp and reports matched the built-in example exactly. |
| Reports in both API responses | HTML, text, and CSV contain R03 and "Hint only."; each CSV has 18 lead rows, exactly two of them R03. |

These are direct HTTP and response-content checks. No new browser interaction,
download-button, accessibility, or real-screen-reader check is claimed. No
deliberate timeout, traffic-capacity, or Render memory test was performed.
The API exhibits the expected R03 behavior; no authenticated Render dashboard
was inspected during this follow-up.

Decision 71 remains unchanged: the brief's +$27 over example is covered by a
focused rule test, while the deterministic demo CSVs stay unchanged. This is a
documented test-data choice, not a missing scenario or an unfinished feature.
