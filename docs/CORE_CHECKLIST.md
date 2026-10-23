# Core verification checklist

Status: M6 complete. Local checks and the hosted Python 3.12/3.13/3.14 matrix
have passed. This is the historical M6 core checklist; M7's request layer is now
locally verified, and M8's screens/deployment remain planned. See the learning
log and web plan for M7 results.

This checklist follows the original core definition of done. PASS means the
check was actually run successfully; FAIL includes checks not yet verified.
The [learning log](LEARNING_LOG.md) records commands, environments, and outcomes.

| Core requirement | Result | Evidence or remaining work |
| --- | --- | --- |
| Fresh checkout, isolated install, pytest, and both Ruff checks | PASS | Fresh local clones of the M6 candidate snapshot passed 559 tests and both Ruff checks under Python 3.12.9 and 3.13.5. |
| Default demo-data, import, reconcile, and date-range report chain | PASS | The exact default command sequence ran in both fresh clones, with 60 shifts, 30 completion dates, and 16 flags. |
| Worked S1 explanation | PASS | Both installed commands showed $518.75 expected, $498.75 counted, -$20.00 difference, and $1,198.75 contribution, with R01/R02 and no R05. |
| Complete golden flag set and documented scenarios agree | PASS | Both full suites verified every expected date, shift, rule, and severity, with no extra flags. |
| Every troubleshooting symptom has a matching CLI test | PASS | All ten guide entries were reproduced by `tests/test_troubleshooting.py`. |
| CSV formula-protection checks | PASS | Both full suites passed all sanitizer/export checks; actual CSV exports contained 16 flag rows. |
| Finished README, sample, and explicit screenshot placeholder | PASS | README includes setup, three demo steps, terminal output, limitations, concept links, and documentation links. No actual screenshot is claimed. |
| GitHub CI is green for the M6 changes | PASS | [Core checks run 1](https://github.com/GutsJr75/DrawerCheck/actions/runs/39912675717) passed for commit `75c221c5e362345dffd6d420bd877d81a0628f6d`; all three Python jobs passed 559 tests, both Ruff checks, and installed help. |

## Python versions and CI

The workflow targets Python 3.12, 3.13, and 3.14 on `ubuntu-latest`. Local
interpreters are Python 3.12.9 with SQLite 3.45.3 and Python 3.13.5 with SQLite
3.47.1. There is no local Python 3.14 interpreter available; its successful
hosted job now supplies that version's test evidence. All three job summaries
and test logs were inspected, rather than inferring success from configuration.

Verification used two new local clones of an isolated Git snapshot of the M6
candidate files, with separate environments and no existing environments or
caches copied into them. Development wheels were downloaded to a temporary
folder, then both installs used that wheel folder with `--no-index`. The user
published the M6 commit, which the hosted run tested. This completion update
only records documentation results; runtime code, tests, and the workflow are
unchanged from the tested commit.

Each clone also passed `pip check`, repeated imports and reconciliation, a
foreign-key check, all three exports, and comparison of the generated offline
HTML sample apart from its timestamp. A separate core-only installation had no
pytest, Ruff, or Flask and completed the demo/import/reconcile/HTML workflow.

The workflow follows [GitHub's Python guide](https://docs.github.com/en/actions/tutorials/build-and-test-code/python).
The guide still shows older action tags; the release pages were checked on
2026-10-22 and the workflow uses
[checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1) and
[setup-python v7.1.0](https://github.com/actions/setup-python/releases/tag/v7.1.0).
It grants read-only repository access and runs the repository's install, Ruff,
pytest, and installed-help commands without publishing a package or a website.

## Observed hosted run

The push-triggered [run](https://github.com/GutsJr75/DrawerCheck/actions/runs/39912675717)
completed successfully on 2026-10-22 in America/Los_Angeles
(2026-10-23 06:38 UTC). Each job passed installation, lint, formatting, tests,
and installed CLI help:

- [Python 3.12](https://github.com/GutsJr75/DrawerCheck/actions/runs/39912675717/job/120279029010): 559 tests passed.
- [Python 3.13](https://github.com/GutsJr75/DrawerCheck/actions/runs/39912675717/job/120279028772): 559 tests passed.
- [Python 3.14](https://github.com/GutsJr75/DrawerCheck/actions/runs/39912675717/job/120279029217): 559 tests passed.

All eight original core checklist rows are now PASS. This does not claim
browser verification or public-app deployment. M7 was subsequently authorized
on 2026-10-23; its local results are recorded separately in the learning log.
