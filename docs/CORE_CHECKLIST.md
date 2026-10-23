# Core verification checklist

Status: M6 local deliverables and verification complete. A passing remote GitHub Actions run
has not been observed. M7/M8's web implementation is not started.

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
| GitHub CI is green for the M6 changes | FAIL: not observed | The new workflow must be published and run on GitHub. The connected repository is read-only and currently has no workflow runs. |

## Python versions and CI

The workflow targets Python 3.12, 3.13, and 3.14 on `ubuntu-latest`. Local
interpreters are Python 3.12.9 with SQLite 3.45.3 and Python 3.13.5 with SQLite
3.47.1. There is no local Python 3.14 interpreter available. A configured matrix
is not evidence that the hosted jobs passed.

Verification used two new local clones of an isolated Git snapshot of the M6
candidate files, with separate environments and no existing environments or
caches copied into them. Development wheels were downloaded to a temporary
folder, then both installs used that wheel folder with `--no-index`. The public
GitHub checkout does not contain the local M6 changes until they are published.
Later changes only record documentation results; runtime code and tests match
the verified snapshot.

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

## Remaining delivery step

Publish the reviewed local M6 commit to the intended GitHub branch and observe
all three workflow jobs. If a job fails, fix it and rerun it before marking the
remote CI row PASS. No passing remote run or complete hosted version matrix is
claimed by this checklist. M7 requires a separate user instruction after M6.
