# DrawerCheck design guide

This guide covers the website and the existing M4 HTML report. M10 block 1,
authorized on 2026-10-26, applies the approved "Tick and tie" shared palette,
fonts, type/spacing, logo, header, breadcrumbs, and footer. M10 block 2 adds the
Full run Results slip and responsive review/sidebar layout. The other M8 view
structures remain until their later M10 blocks. See
[REDESIGN_PLAN.md](docs/REDESIGN_PLAN.md) for that delivery order.

The original M8 delivery history follows.
M8 block 1 built the page layout, tokens, fonts, demo notice, and footer in
`src/drawercheck/static/app.css`. Block 2 added the Start view with the example
tape and the Prepare files view with its checklist. Block 3 added Results and
Drawer details with the count sheet. Block 4 added filters, report downloads,
and the waiting states. Block 5 checked WCAG 2.2 AA in Chrome and WebKit and
made the small fixes noted below. The report's styles are unchanged.

Read this file for how the website should **look**. Read
[WEB_PLAN.md](docs/WEB_PLAN.md) for how it should **behave**: views, wording,
navigation, loading, uploads, and the checks that define done.

## Public app direction (approved 2026-10-22)

Design for visitors who may know neither coding nor cash-drawer work. The product
should feel like a familiar, focused work tool: minimal, professional, and easy
to understand. Use neutral backgrounds, one main accent, readable typography,
consistent spacing, and restrained borders. Every card, icon, colour, and control
must help explain the task or support an action. Avoid decorative charts,
marketing-heavy layouts, and motion that distracts from records or results.

Use one primary action per view. Organize the app around Start, Prepare files,
Results, and Drawer details; example users skip file preparation. Keep summaries
brief and reveal definitions, calculation steps, and preparation guidance when
requested. Keep navigation and labels consistent across views.

Start's upload action says "Upload demo CSVs" to reinforce the fake-data-only
boundary. Beside report downloads, remind visitors that refreshing or closing
the page removes its results and that a download keeps a copy. Use the existing
button and hint styles. The date filter remains a native HTML select; its
popup geometry and keyboard behavior belong to the browser and operating
system, while the page supplies its label and options.

Show the example-data notice, input errors, missing records, and unknown amounts
clearly. Use text as well as colour for statuses. Prefer familiar labelled
buttons, forms, and tables, with visible keyboard focus and usable narrow-screen
layouts. Optional explanations must work with keyboard and touch. Minimalism
reduces visual noise while preserving the guidance a beginner needs.

The user added on 2026-10-23 that the site must look distinctive, not like a
stock template or a typical AI-generated page, while meeting industry standards.
The sections below turn both requests into concrete rules.

## Standard to meet: WCAG 2.2 level AA

Every view must meet [WCAG 2.2](https://www.w3.org/TR/WCAG22/) level AA. In
practice, for this site:

- **Contrast:** body text at least 4.5:1; large text, control borders, and focus
  indicators at least 3:1. The tokens below were checked against these numbers.
- **Not colour alone:** every status has a written label.
- **Keyboard:** everything works with Tab, Shift+Tab, Enter, Space, and Escape,
  in a logical order, with a visible focus ring that is never hidden behind
  another element. Provide a "Skip to main content" link.
- **Targets:** every clickable control is at least 24 x 24 CSS pixels; main
  buttons and the file chooser are at least 44 pixels tall.
- **Reflow and zoom:** these are two separate checks.
  - *Reflow:* no sideways page scrolling at 320 CSS pixels wide. Test it on a
    narrow screen and with 400% browser zoom in a 1,280-pixel-wide desktop
    window, which [W3C](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)
    treats as the same 320-pixel width.
  - *Text resizing:* text enlarged to 200% loses no content or controls.
  - Data tables may scroll inside their own labelled region.
- **Announcements:** loading, results ready, and errors are announced to screen
  readers through a polite live region; error summaries take focus.
- **Structure:** one `h1` per view, headings in order, `lang="en"`, and a page
  title that names the current view.
- **Motion:** no animation is needed to understand anything. Honour
  `prefers-reduced-motion` by removing transitions.

## Visual system

### Colour

The approved M10 "Tick and tie" identity uses pale ledger-green paper,
blue-pen actions, red/amber review labels, and graphite Notes. Green has a
written status meaning, never proof of an independently verified match.
Light and dark follow the visitor's system setting. The report keeps its own
marine-teal palette. The values below are the website's shared runtime tokens.

| Token | Use | Light | Dark | Contrast on surface (light / dark) |
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

The notice reverses `text` and `surface`. The contrast tests cover page and
surface backgrounds, label backgrounds, errors, control edges, and the logo
mark; the button hover/active pair uses `surface` on `text`. All pairs must
meet their actual text or non-text threshold. This is a contrast check, not
full accessibility certification.

### Typography

- **Text:** Atkinson Hyperlegible Next. **Money:** Atkinson Hyperlegible Mono,
  right-aligned and exactly as Python formatted it. Both are self-hosted Latin
  variable WOFF2 fonts from Fontsource packages pinned to **5.3.0**, downloaded
  on 2026-10-26. They support upright weights 200 through 800; the UI uses
  400, 600, and 700. Body is 17 px / 1.55; headings use 700 / 1.2.
- **Sizes:** 52 px Start title on desktop, 34 px on phones; other page titles
  40 px on desktop, 30 px on phones; section titles 26 px, smaller headings
  19 px; supporting copy 15 px and status labels 14 px. Keep prose under 68ch.
- **Assets:** `atkinson-hyperlegible-next-latin-wght-normal.woff2` is 33,996
  bytes; `atkinson-hyperlegible-mono-latin-wght-normal.woff2` is 17,752 bytes.
  Total **51,748 bytes**. Preserve `LICENSE-next.txt` and `LICENSE-mono.txt`
  with their original copyright notices and SIL OFL 1.1 text.
- The page preloads the single Next file. Both font faces use `font-display:
  swap`; Mono loads when amounts appear. Keep the existing system sans and
  monospace fallbacks. No remote font or CSS requests at runtime.
- These letterforms help distinguish similar characters. They do not replace
  actual reading, narrow-screen, zoom, and assistive-technology checks.

Font package sources (no package is installed as a runtime dependency):

- [Next 5.3.0 archive](https://registry.npmjs.org/@fontsource-variable/atkinson-hyperlegible-next/-/atkinson-hyperlegible-next-5.3.0.tgz)
- [Mono 5.3.0 archive](https://registry.npmjs.org/@fontsource-variable/atkinson-hyperlegible-mono/-/atkinson-hyperlegible-mono-5.3.0.tgz)

### Spacing, shape, and layout

- **Three spacing roles:** item 8 to 12 px; group 16 to 24 px; new topic
  32 px on phones and 48 px on desktop, up to 64 px where a layout needs it.
  `--space-item`, `--space-group`, and `--space-topic` adapt the existing
  4/8/12/16/24/32/48/64 px scale. Headings stay near the content they introduce.
- **Corners:** 4 px status labels, 8 px controls, 12 px sheets. No shadows.
- **Width:** up to 1,200 px plus gutters; gutters 16/24/32 px at phone,
  640 px, and 1,024 px. Existing columns retain their current breakpoints
  until their M10 view blocks; the planned side column stacks below 960 px.
- **Shell:** surface header with a decorative drawer-and-tick mark beside the
  DrawerCheck home link. The top demo wording stays unchanged. Breadcrumbs
  use an ordered list in a named navigation landmark, linked ancestors, and
  plain current text marked `aria-current="page"`; slash separators are hidden
  from assistive technology. Results ancestors keep the active filters.
- **Footer:** one wrapping row with the learning-project and fictional-record
  boundary, not-for-real-cash-control wording, file deletion, and source/report
  links. Never fix its height or truncate its content to force one line.
- **Focus:** 3 px accent ring with a 2 px gap. Keep view-heading focus on
  navigation and the existing error-summary/row focus behavior.
- **Scroll ownership:** document scrolling; optional tables scroll internally.
  The root reserves its scrollbar gutter. Every owned scroll region uses
  `control` on `surface`, with `muted` hover and `text` active thumbs where
  supported. Use standards properties and a WebKit fallback; system colors
  take over in forced-colors mode. Never hide scrollbars.
- **Motion:** existing colour transitions are at most 150 ms and disabled for
  reduced motion. Block 2 draws the no-leads summary tick once per run over 600 ms.
  Returning from a drawer does not replay it; reduced motion shows it still.
  Hide it when no drawers qualify. Its wording is about no leads from these
  checks, never an exact match or a completed human review.

### Runtime token ownership and mapping

The existing CSS is the canonical runtime source (Model B). Edit the shared
`:root`/dark-mode tokens in `static/app.css` once; this guide mirrors their
accepted values and explains their use. There is no second theme adapter or
front-end framework. `tests/test_web_page.py` recalculates contrast and checks
local asset serving, font licences, package contents, and resource budgets.

| Design rule | Runtime target | Shared consumers |
| --- | --- | --- |
| Palette roles in the table above | Same-named `--page`, `--text`, `--accent`, etc. | All four views and the shared shell |
| Text and money fonts | `--font-sans`, `--font-mono`; local `@font-face` rules | Body, tables, tape, amounts |
| Item/group/topic spacing | `--space-item`, `--space-group`, `--space-topic` | Shared breadcrumbs, section gaps, footer |
| Label/control/sheet shape | `--radius-label`, `--radius-control`, `--radius-panel` | Statuses, buttons/inputs, sheets |
| Native date filter and shared navigation | Existing `app.js` and native HTML select | Results, drawer links, breadcrumbs |
| Scrollbars | Global CSS standards properties and pseudo-elements | Document and future overflow regions |

### Components

| Component | Rule |
| --- | --- |
| Main button | `accent` fill with `on-accent` text, 44 px tall. One per view. On hover it turns to `text` with `surface` lettering. |
| Secondary button | `surface` with a `control` border and `accent` text. |
| Status label | Short word on its tinted background: Note, Check, Needs review, Ready, Missing, Problem. "Waiting" uses `muted` text with a `line` outline. |
| File chooser | A normal labelled "Choose files" button; dragging files onto the list is optional extra help. |
| Help | Native `details` and `summary` elements ("What does this mean?"), so they work with keyboard and touch. |
| Filters | A native `select` and native radio buttons with `accent-color`, each with a visible label; no custom dropdown widget. The select drops its native look and draws its own arrow in the `text` colour, because WebKit ignores the 44 px height on native-looking selects. |
| Demo notice placement | Inside the `header` landmark, above the wordmark row, so every piece of content belongs to a landmark. |
| Favicon | `static/favicon.svg`: a drawer outline and green tick on pale paper, matching the decorative header mark. |
| Downloads | Three secondary buttons in the Results side column: "Web page (.html)", "Spreadsheet (.csv)", and "Text (.txt)". Below 960 px they follow the review list. |
| Waiting | The busy button's own words, a Cancel button beside it, and after 5 seconds a sentence with a `control` left rule. Failures show in `review` text with a "Try again" button. |
| Tables | Real `table` elements with captions and header cells; numbers right-aligned. |
| Demo notice | A full-width strip at the top of every view: "Example data only. Do not upload real store records." |
| Footer | Not for real cash control; files are deleted after each check; links to the code and the example report, both on GitHub. |

## Signature elements

These make the site recognisable by showing how cash is actually checked,
rather than by decoration. All numbers below are real values from the demo.

### The drawer tape (Drawer details)

The calculation is shown like a till receipt or adding-machine tape: an
operator column, a plain-language label, and the amount in Atkinson Hyperlegible Mono. A rule
line separates the inputs from the result, and the result line is emphasised.

```text
    Opening float               $200.00
  + Cash sales                $1,250.75
  + Paid-ins                      $0.00
  - Cash refunds                 $12.00
  - Paid-outs                    $20.00
  - Safe drops                  $900.00
  -------------------------------------
  = Expected cash               $518.75
    Counted cash                $498.75
  -------------------------------------
    Difference      -$20.00     Short     Needs review
```

- Build it as a table with row headers, so screen readers read each line as
  "Minus cash refunds, $12.00". The `+` and `-` symbols are visual only. On
  Drawer details each label sits inside its definition toggle, which does not
  count toward the row header's name, so each header also carries an
  `aria-label` with the whole line.
- Drawer details shows the tape and count sheet side by side only when both
  columns fit; with large text or a narrow window they stack.
- The paper is a `surface` panel whose bottom edge is torn like a till roll,
  drawn with a CSS gradient in the same colour. Rules are dashed `control`
  lines. This edge is the site's one decorative flourish; nothing else on the
  page gets one.
- Each label can open a one-sentence definition ("A safe drop is cash moved
  from the drawer to the safe during the shift"). On Drawer details each label
  is a `details` element with a dotted underline; each drawer opens with them
  closed. The Start example lists the same definitions in one section below it.
- A missing input shows "unknown" with the reason, and the expected line says
  why it cannot be calculated. It never shows `$0.00` for missing data.
- Every amount comes from the server. The browser does no arithmetic.

### The count sheet (Drawer details)

The counted cash appears like the paper count sheet a cashier fills in:

```text
  Bill or coin   Quantity     Line total
  $100.00               4        $400.00
  $50.00                1         $50.00
  $20.00                2         $40.00
  ...
  Counted cash                   $498.75
```

Line totals are calculated in Python and sent with the results (see
[WEB_PLAN.md](docs/WEB_PLAN.md#data-the-screens-need-from-python)).

The sheet is a `surface` panel with a thin `line` rule under each row. The total
follows the bookkeeping convention: a single `control` rule above "Counted
cash" and a double rule below it. Bills and coins label their rows on the left;
quantities and line totals are right-aligned. With no count rows, the sheet is
replaced by a sentence saying counted cash is unknown, not $0.00.

### The example tape on the Start view

Instead of a marketing banner, the Start view shows a small, clearly labelled
copy of the drawer tape for the demo shift `2026-09-03-R1`, captioned "Example
from the built-in demo". It teaches the idea in five seconds and sits beside
the main "Try the example" button.

### Results full-run summary and side column

M10 block 2 replaces the M8 facts line with one surface slip, using the shared
torn tape edge and the label "Full run". Its headline reads "9 of 60 drawers
have leads to check." Supporting text distinguishes 16 drawer leads from two
whole-day leads on two dates. A ruled line separates "51 drawers with no leads"
and "No leads found by these checks." The green tick has exactly that limited
meaning; a small difference within tolerance can have no lead. Zero drawers
uses "No drawers in this run." Singular/plural wording uses the response counts.

Keep the date range directly under Results and get every calendar label,
including the weekday and year, from Python's shared `labels.dates` map.
The full-run summary stays unchanged under filters. Detailed lead and severity
counts are in a closed disclosure below the review area, outside this slip.

At 960 px and above, the review list fills the main column and filters,
secondary report downloads, and level definitions occupy a 19rem side column.
Below that width, stack filters, review list, downloads, and definitions in
that order. There is only one set of controls. DOM and keyboard order put
filters before review links and downloads after them, with no positive tabindex.
Use the existing native select, radio group, buttons, status labels, and hints.

The lead list remains flat during block 2. Grouping, severity section counts,
and the complete More detail treatment belong to block 3. Results rows still
show the Python title/message, date, drawer or whole-day scope, and rule code.
M9's "Possible swapped digits" Notes retain their "Hint only" wording and the
shared Note treatment in both Results and Drawer details. All money, counts,
rule labels, and date wording remain Python-owned.

## What to avoid

These patterns make a site look generic or template-made, so do not use them:

- A centred hero banner with a gradient, stock illustration, or emoji.
- A grid of identical cards, each with an icon and a short phrase.
- Purple or rainbow gradients, glass effects, glowing borders, or heavy shadows.
- Pill-shaped buttons and labels everywhere, or all-capital headings.
- Shimmering placeholder blocks or spinners with no words.
- Vague buttons such as "Get started" or "Learn more". Say what will happen:
  "Try the example", "Check my files", "Download spreadsheet (.csv)".
- Charts that only decorate. A number in a sentence is clearer for this data.

## Performance budget

- No front-end framework and no third-party requests of any kind.
- Site CSS and JavaScript together under 60 KB before compression, excluding
  fonts; fonts under 200 KB in total.
- Results are usable immediately after the server responds; nothing waits on
  animation.

The current token values in the next section belong to the report's inline CSS.

## Existing M4 report

The report's job is to help a reader find incomplete dates and review leads,
then inspect the cash amounts behind them. Use a restrained close-review sheet
with a dark marine demo strip, clear section tabs, and readable accounting
tables. Avoid charts, decorative icons, large marketing claims, or animation.

Tokens live in the inline CSS in `reports/html.py` so the exported file has no
external dependencies:

| Token | Light | Dark |
| --- | --- | --- |
| Page | `#edf3f5` | `#13262f` |
| Paper | `#ffffff` | `#1b333e` |
| Text | `#162b35` | `#eff5f7` |
| Supporting text | `#48636f` | `#b4cbd4` |
| Accent | `#076f78` | `#80d8d3` |
| Border | `#cedce1` | `#3a5662` |

Use locally installed Iowan Old Style/Palatino for the single document title,
Avenir Next/Segoe UI/system sans-serif for body text, and tabular digits for
money. No downloaded fonts or assets. Severity is always written in words.

Keep daily summary, review leads, cashier totals, and shift calculations in
that order. Show unknown amounts explicitly. Cashier totals include all known
signed differences and label the known, open, and incomplete record counts.

On narrow screens, each table scrolls inside a labelled keyboard-focusable
region. The document itself should fit the viewport. Internal section links
have visible focus. Light/dark preference and printing use CSS only; there are
no scripts, loaders, forms, or remote calls. Every dynamic HTML value is escaped.

Keep the base theme in a valid top-level `:root` rule. The demo strip also has
a dark fallback background so its white warning remains readable when the
background variable is unavailable. Static stylesheet tests do not replace
browser checks of light, dark, narrow-screen, and print appearance.
