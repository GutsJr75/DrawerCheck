# M11 closing workflow checklist

Updated 2026-11-04 at the end of block 9. All nine M11 blocks are complete
locally. This is a record of what was checked and what was not; it is not an
acceptance or accessibility certification.

| Check | Status | Evidence |
| --- | --- | --- |
| Fictional walkthrough packet with expected answers | Done | [Block 1](M11_BLOCK1.md), [participant packet](M11_PARTICIPANT_PACKET.md) |
| README leads with the product | Done | [README](../README.md) |
| Input and check contract | Reviewed and implemented | [Contract](M11_CONTRACT.md) |
| One-drawer check matches the CSV path | PASS | Block 4 parity tests for every walkthrough case, with and without sign-off |
| Close a drawer, Review a drawer, recount, closing sheet | PASS locally | [Block 5](M11_BLOCK5.md), [block 6](M11_BLOCK6.md), [block 7](M11_BLOCK7.md), [block 8](M11_BLOCK8.md) |
| Python, web, and lint checks | PASS | 824 passed and 12 opt-in skipped; 836 with browser tests; both Ruff checks |
| Chrome and WebKit flows | PASS locally | 12 committed browser cases, including keyboard, refresh, Cancel, failures, late replies, and safe text ([block 9](M11_BLOCK9.md)). WebKit build 2370 is an unofficial pairing with Playwright 1.65 |
| Accessibility scans | PASS within tested scope | 128 axe-core 4.14.0 scans, no violations; tape contrast incomplete as in M10 |
| Text size, narrow screens, both themes | PASS within tested scope | 96 checks after one fix (stacking count lines at large text) |
| Unknown stays unknown; zero stays zero | PASS | Missing report, blank count lines, drop log, and times tests |
| Check coverage disclosed | PASS | Review and the closing sheet say which checks ran and which could not |
| Performance | No slowdown attributable to M11 | Eight alternating rounds within a few percent; first cross-day comparison retained |
| CSS and JavaScript budget | 79,117 of 90,000 bytes | `test_static_files_meet_the_performance_budget` |
| Participant usability | UNVERIFIED | No participant session; nobody contacted |
| Real screen reader | UNVERIFIED | Not used |
| Actual 400% browser zoom | UNVERIFIED | Not done |
| Hosted CI and public site for M11 | UNVERIFIED | The user pushed up to `56a99b8` (blocks 1 to 5); blocks 6 to 9 are local. No M11 CI run or live check has been observed |

The public demo runs whatever was last deployed; that has not been checked
for M11. After the user publishes the remaining M11 commits, a hosted
follow-up should observe the CI run and the live Close a drawer, Review,
recount, and closing sheet before claiming them.
