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
| Python, web, and lint checks | PASS locally | After the [Python 3.14 test repair](M11_PY314_REPAIR.md): 825 passed and 14 opt-in browser cases skipped on Python 3.13.5; both Ruff checks. The earlier run with browser tests passed 838. The repaired CI matrix still needs verification |
| Chrome and WebKit flows | PASS locally | 14 committed browser cases, including enlarged text, including keyboard, refresh, Cancel, failures, late replies, and safe text ([block 9](M11_BLOCK9.md)). WebKit build 2370 is an unofficial pairing with Playwright 1.65 |
| Accessibility scans | PASS within tested scope | 128 axe-core 4.14.0 scans, no violations; tape contrast incomplete as in M10 |
| Text size, narrow screens, both themes | PASS within tested scope | 96 checks after two fixes: count lines stack at large text, and the closing sheet follows text size ([repair](M11_BLOCK9.md#repair-after-review-2026-11-04)); a committed browser test covers both |
| Unknown stays unknown; zero stays zero | PASS | Missing report, blank count lines, drop log, and times tests |
| Check coverage disclosed | PASS | Review and the closing sheet say which checks ran and which could not |
| Performance | No slowdown attributable to M11 | Eight alternating rounds within a few percent; first cross-day comparison retained |
| CSS and JavaScript budget | 79,117 of 90,000 bytes | `test_static_files_meet_the_performance_budget` |
| Participant usability | UNVERIFIED | No participant session; nobody contacted |
| Real screen reader | UNVERIFIED | Not used |
| Actual 400% browser zoom | UNVERIFIED | Not done |
| Hosted CI and public site for the repaired build | UNVERIFIED | The expanded CI run for `9a20875` passed Python 3.12/3.13 but failed one Python 3.14 test-message assertion. Its [test repair](M11_PY314_REPAIR.md) needs publication and a passing matrix; live verification remains open |

The public demo runs whatever was last deployed; that has not been checked
for M11. After the user publishes the repair, a hosted
follow-up should observe the CI run and the live Close a drawer, Review,
recount, and closing sheet before claiming them.
