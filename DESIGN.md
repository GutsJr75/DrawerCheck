# DrawerCheck design guide

This guide covers two things: the M8 website and the existing M4 HTML report.
M8 block 1 built the page layout, tokens, fonts, demo notice, and footer in
`src/drawercheck/static/app.css`. Block 2 added the Start view with the example
tape and the Prepare files view with its checklist. Results and Drawer details
come in block 3, and the full accessibility check is block 5. The report's
styles are unchanged.

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

The website reuses the report's marine teal so the site and the downloaded
report feel like one product. Light and dark themes follow the visitor's system
setting. Contrast ratios were calculated for each pair listed.

| Token | Use | Light | Dark | Checked contrast (light / dark) |
| --- | --- | --- | --- | --- |
| `page` | Page background | `#edf3f5` | `#13262f` | |
| `surface` | Panels, tables, inputs | `#ffffff` | `#1b333e` | |
| `text` | Main text | `#162b35` | `#eff5f7` | 14.7:1 / 12.0:1 on surface |
| `muted` | Supporting text | `#48636f` | `#b4cbd4` | 5.7:1 / 7.8:1, worst case |
| `line` | Dividers only, never control edges | `#cedce1` | `#3a5662` | decorative |
| `control` | Input and button borders | `#6b8792` | `#86a3ae` | 3.4:1 / 5.0:1, worst case |
| `accent` | Main button, links, focus ring | `#076f78` | `#80d8d3` | 5.3:1 / 8.0:1, worst case |
| `on-accent` | Text on the main button | `#ffffff` | `#0d2a30` | 5.9:1 / 9.1:1 |
| `note` text / background | "Note" label | `#076f78` / `#e6f3f2` | `#80d8d3` / `#1e4148` | 5.2:1 / 6.7:1 |
| `check` text / background | "Check" label | `#7a4d00` / `#fdf1dc` | `#ffd28a` / `#3b3122` | 6.5:1 / 9.0:1 |
| `review` text / background | "Needs review" label | `#963a32` / `#fbeae8` | `#ffb2a8` / `#45292b` | 6.1:1 / 7.6:1 |
| `ready` text / background | "Ready" file status | `#2d6a3e` / `#e6f2e9` | `#9ad8a8` / `#20402c` | 5.6:1 / 7.0:1 |

`accent` is the only decorative colour. The four status colours appear only on
status labels and their related text, never as large fills or backgrounds.

The demo notice reverses `text` and `surface` (14.7:1 light, 12.0:1 dark), so
it needs no extra token: a dark strip in light mode and a light strip in dark
mode. `tests/test_web_page.py` recalculates every pair above, plus this one,
from the stylesheet, so a token change that breaks contrast fails the tests.

### Typography

- **Fonts:** IBM Plex Sans for text and IBM Plex Mono for money, served from the
  site itself as WOFF2 files (regular and semibold, Latin subset), with their SIL
  Open Font License included. No font is loaded from another website. Fallbacks:
  `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` and
  `ui-monospace, Menlo, Consolas, monospace`. Use `font-display: swap`.
- **Font files:** the Latin1 WOFF2 files from IBM's GitHub releases
  `@ibm/plex-sans@1.1.0` and `@ibm/plex-mono@2.5.0`, with IBM's own
  `unicode-range` values. The four files total 78,660 bytes. The page preloads
  the two Sans files; the browser fetches Mono only when money appears.
- **Why Plex:** it reads clearly at small sizes, has a slightly technical,
  ledger-like character that suits cash records, and looks the same on every
  device, unlike the report's system fonts.
- **Sizes:** 14, 16, 18, 20, 24, and 32 pixels (32 becomes 28 on phones). Body
  text is 16 px with 1.5 line height; headings use 1.25. Keep paragraphs under
  about 68 characters wide.
- **Weights:** 400 for text, 600 for headings, labels, and key amounts. Use
  sentence case everywhere; no all-capital labels.
- **Money:** always IBM Plex Mono, right-aligned in columns, exactly as Python
  formatted it, for example `$1,250.75` or `-$20.00`. Next to a signed
  difference, also write the word: "Short", "Over", or "Balanced".

### Spacing, shape, and layout

- **Spacing scale:** 4, 8, 12, 16, 24, 32, 48, and 64 px. Use nothing else.
- **Corners:** 4 px on buttons, inputs, and labels; 8 px on panels. No pill
  shapes.
- **Depth:** separate areas with `line` borders and spacing. No drop shadows.
- **Width:** content up to 1,120 px wide; side margins of 16 px on phones,
  24 px on tablets, and 32 px on desktops.
- **Breakpoints:** 640 px and 1,024 px. Below 640 px, results tables become
  stacked rows, one review item per row.
- **Focus ring:** 3 px solid `accent` with a 2 px gap, on every interactive
  element.
- **Transitions:** at most 150 ms on colour changes; none when reduced motion is
  requested.

### Components

| Component | Rule |
| --- | --- |
| Main button | `accent` fill with `on-accent` text, 44 px tall. One per view. On hover it turns to `text` with `surface` lettering. |
| Secondary button | `surface` with a `control` border and `accent` text. |
| Status label | Short word on its tinted background: Note, Check, Needs review, Ready, Missing, Problem. "Waiting" uses `muted` text with a `line` outline. |
| File chooser | A normal labelled "Choose files" button; dragging files onto the list is optional extra help. |
| Help | Native `details` and `summary` elements ("What does this mean?"), so they work with keyboard and touch. |
| Tables | Real `table` elements with captions and header cells; numbers right-aligned. |
| Demo notice | A full-width strip at the top of every view: "Example data only. Do not upload real store records." |
| Footer | Not for real cash control; files are deleted after each check; links to the code and the example report, both on GitHub. |

## Signature elements

These make the site recognisable by showing how cash is actually checked,
rather than by decoration. All numbers below are real values from the demo.

### The drawer tape (Drawer details)

The calculation is shown like a till receipt or adding-machine tape: an
operator column, a plain-language label, and the amount in Plex Mono. A rule
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
  "Minus cash refunds, $12.00". The `+` and `-` symbols are visual only.
- The paper is a `surface` panel whose bottom edge is torn like a till roll,
  drawn with a CSS gradient in the same colour. Rules are dashed `control`
  lines. This edge is the site's one decorative flourish; nothing else on the
  page gets one.
- Each label can open a one-sentence definition ("A safe drop is cash moved
  from the drawer to the safe during the shift").
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

### The example tape on the Start view

Instead of a marketing banner, the Start view shows a small, clearly labelled
copy of the drawer tape for the demo shift `2026-09-03-R1`, captioned "Example
from the built-in demo". It teaches the idea in five seconds and sits beside
the main "Try the example" button.

### Results summary as plain facts

The top of Results is one line of labelled numbers, not a grid of icon cards.
Keep counts of leads and counts of drawers separate. For the demo:
"60 drawers checked", "4 drawers need review", "16 leads in total", and
"2 days with bank-deposit leads".

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
