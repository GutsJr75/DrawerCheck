# M9 block 1: possible swapped digits

Authorized and verified locally on 2026-10-26. M9 is split into three blocks:
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

No M9 push, hosted CI result, Render setting change, or deployment is claimed.
The last independently verified hosted run is for M8 repair commit 332f01b.
The last verified public M8 demo has 16 leads until an updated deployment is
observed. The 18-lead source and sample are locally verified.

No new full accessibility, cross-browser, light-theme, zoom, capacity, or Render
memory audit was run. Earlier M8 evidence remains historical. A real screen
reader and the user-deferred friend usability check remain open.

Next, after **next**, implement R06 (high cash sales with no recorded safe
drop) using the existing example threshold. R07 needs its historical median
details settled before its later block. No R06 or R07 rule is registered here.
