# M10 redesign verification checklist

Updated 2026-10-28. All four views are implemented. Block 7 local verification
and documentation are complete with the limits below. Two local fixes still
need publication and final hosted verification; this is not a full acceptance
or accessibility certification.

| Check | Status | Evidence |
| --- | --- | --- |
| Shared Tick and tie design, grouped Results, Drawer details, Start, Prepare files | Implemented | Blocks 1 to 6; current rules in DESIGN.md and WEB_PLAN.md |
| Local Python, lint, formatting, whitespace | PASS | 729 tests, both Ruff checks, git diff --check |
| Pre-redesign comparison | PASS | All 60 full drawer records match after excluding the added limit_text field; all 18 global flags and all three reports agree |
| Accessibility scans | PASS within tested scope | Final 216 axe-core 4.14.0 scans: 27 states, two engines, two themes, two widths; zero detected WCAG A/AA or best-practice violations. Incomplete results retained for review |
| Themes, widths, native controls, and keyboard | PASS within tested scope | Chrome/WebKit at 320/1,280 px; 959/960 breakpoint; radios, disclosures, error focus, announcements, count toggle, named tape/table scrolling |
| Text enlarged to 200% | PASS within tested scope | Four views, both themes, both engines at a 1,280 px viewport; no page overflow or detected clipping |
| Equivalent narrow reflow | PASS within tested scope | Four views, both themes, both engines at 320 x 200; tables remain internal scroll regions |
| Actual 400% browser zoom | UNVERIFIED | Native app control timed out twice. Viewport/device-scale emulation is not an actual browser-zoom pass |
| Screen-reader announcements and tape speech | UNVERIFIED | No real screen reader used. Accessibility-tree/live-region checks do not prove actual speech |
| First-time-user usability | UNVERIFIED | Remains deferred; no new participant session |
| Counts, unknown/zero/open states, Notes, bank-only dates, long IDs, navigation | PASS within tested scope | Edge fixtures and all 60 demo drawers in Chrome/WebKit; filtered Next does not wrap |
| Caps, cleanup, and safe insertion | PASS within tested scope | Existing regression suite; 8,701,107-byte combined response, strict cap retained; CSS/JS 59,987 bytes and fonts 51,748 bytes |
| Generic premium static audit | Seven known findings remain | Exit 1 for external-handler detection; actual button behavior has browser evidence. This is not a clean static-audit pass |
| Block 6 GitHub CI | PASS, observed | Run 40664015982 for 17875c1; Python 3.12/3.13/3.14 including optional web/server steps |
| Existing public runtime | PASS within smoke scope | Assets match 17875c1; real example/upload each return 60 drawers and 18 leads; drawer, reports, and refresh work |
| Block 7 fixes on hosted CI/public site | PENDING publication | Valid tape-region wrapper and wrapping count chips are local changes; no push or deployment performed |
| README, interview notes, and screenshot timeline | Updated | Current screenshots and honest local/hosted/manual distinctions |

Two defects found and fixed during block 7: a region role placed on a figure,
and a Chrome-only overflow when full lead-count chips were expanded. Initial
and final scans/screenshots are retained. After publication, inspect the CI
for the new commit, confirm matching deployed assets, and repeat the public
example, fake upload, and all report downloads. Carry the manual checks above
forward until they are actually observed.

See [block 7 evidence](M10_BLOCK7.md) for exact checks, raw files, browser
limitations, and screenshot provenance. The remaining M9 rules still require
separate authorization.
