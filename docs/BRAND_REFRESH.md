# DrawerCheck brand refresh

The user authorized a replacement for the drawer-and-tick icon on 2026-11-04.
Completed locally from `9a20875`; no push or deployment. The existing
uncommitted `docs/WEB_PLAN.md` edit was preserved and is not part of this block.

## Design and placement

An original geometric DC monogram now sits beside the DrawerCheck name in
the shared site header. Filled, joined letterforms give the name its own
brand mark, with pine ink for D and green for C. The existing Atkinson
wordmark is slightly heavier and more tightly spaced. No stock artwork,
external logo service, font download, dependency, or new colour was used.

- [Light logo](../src/drawercheck/static/logo.svg) and
  [dark logo](../src/drawercheck/static/logo-dark.svg) are transparent SVGs.
- The native `picture` element chooses the matching asset for the visitor's
  colour preference. Fill attributes avoid inline SVG styles under the
  existing security policy. Colour values mirror `text` and `ready` in
  `DESIGN.md` and the application stylesheet.
- [Favicon](../src/drawercheck/static/favicon.svg) uses the same geometry on
  pale paper, padded for a square browser tab.
- The visible product name labels the Home link. The adjacent image has an
  empty alternative so the name is not announced twice. Mark and gap scale
  with the wordmark, including the narrow header at 200% text.

## Verification

- 824 tests passed; 14 opt-in browser cases skipped. The focused page suite
  also passed all 25 tests. Both Ruff checks and `git diff --check` passed.
- Custom browser checks passed in Chrome 156 and WebKit build 2370: loaded
  image and correct theme asset, light/dark at 320 and 1,280 px, no document
  overflow, a fitting header at 320 px with 200% root text, keyboard Home
  navigation from Close, and the existing example Results and Drawer views.
  [Browser results](BRAND_REFRESH_BROWSER.json). WebKit 2370 remains an
  unofficial pairing with Playwright 1.65; no browser was downloaded.
- Eight axe-core 4.14.0 scans of the changed header across both engines,
  themes, and widths found no violations or incomplete results.
  [Header results](BRAND_REFRESH_AXE.json). This is not a full-page or
  screen-reader certification.
- The [static audit](BRAND_REFRESH_AUDIT.json) retains the seven existing
  actionless-button detections on old controls wired in external JavaScript.
  No new finding. It is not a clean static-audit pass.
- CSS/JS total 79,059 bytes of the 90,000-byte ceiling. All three SVGs parse
  correctly and are included by the existing package-data pattern.

The initial browser helper checked the hash before the Home view transition
had completed. It was corrected to wait for the visible Start view; the
initial four screenshots are retained. Use the ten `verified` captures and
the two `lockup` close-ups for the final appearance. All sixteen captures are
in the [dated folder](screenshots/2026-11-04-brand-refresh/).

The previously diagnosed Python 3.14 CI test-message mismatch is outside
this visual block and remains unresolved. No CI or hosted pass is claimed
for this commit. The pending test repair and M12 were not implemented.
