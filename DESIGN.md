# DrawerCheck report design

Scope: the self-contained M4 HTML report, a static document for reviewing fake
cash drawer records. The M7/M8 public application is separate future work.

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
