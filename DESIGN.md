# DrawerCheck design guide

Scope: the existing self-contained M4 HTML report and the approved direction for
the future M7/M8 public app. The app guidance below is a plan, not implemented or
visually verified screens. The M4 report's existing tokens remain unchanged.

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
requested. Keep navigation and labels consistent across views. The workflow,
wording examples, and acceptance checks live in [WEB_PLAN.md](docs/WEB_PLAN.md).

Show the example-data notice, input errors, missing records, and unknown amounts
clearly. Use text as well as colour for statuses. Prefer familiar labelled
buttons, forms, and tables, with visible keyboard focus and usable narrow-screen
layouts. Optional explanations must work with keyboard and touch. Minimalism
reduces visual noise while preserving the guidance a beginner needs.

The app will reuse the report's restrained visual language where appropriate.
Exact app tokens and component styles will be settled and documented during M8;
the current token values below belong to the report's inline CSS. This update
changes no runtime styles or report output and does not start M5 or M7/M8.

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
