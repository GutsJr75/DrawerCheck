# M8 delivery and verification checklist

Updated 2026-10-26. All seven M8 delivery blocks are complete, including the
README screenshots and interview notes. This is a learning demo with fictional
data. Delivery does not mean every manual validation item passed.

PASS means a check has supporting evidence. The evidence column distinguishes
historical agent checks, checks reported by the user, supplied dashboard
screenshots, and checks rerun during block 7. FAIL / unverified means the
required check has no result; it does not imply an observed application bug.

| Requirement | Result | Evidence and limits |
| --- | --- | --- |
| Shared Python calculations, labels, count totals, and reports | PASS | Existing web/core parity and combined-response-cap tests; full suite rerun in block 7. JavaScript handles interaction only. |
| Upload validation, independent temporary runs, and cleanup | PASS | Existing Flask request tests and real local Gunicorn timeout/recovery test; full suite rerun in block 7. Forced process death cannot guarantee Python cleanup. |
| All four browser views, filters, navigation, errors, and downloads | PASS | Block 5 browser checks, its correction, original block 6 public checks, and block 6 review are recorded in WEB_PLAN.md and the learning log. Remaining repair smoke checks were reported passing by the user. No new browser run was performed in this docs-only block. |
| Keyboard, reflow, text resize, zoom, themes, and reduced motion | PASS within tested scope | Recorded block 5 Chrome/WebKit checks and repair; not rerun in block 7. Known edge cases remain in WEB_PLAN.md. |
| Automated accessibility scans | PASS within tested scope | Block 5 recorded 136 axe scans with zero violations. An automated scan is not a full accessibility certification. |
| Real screen-reader announcements and tape row-header speech | FAIL / unverified | No real screen reader was run. The accessibility tree alone does not establish whether the operator is spoken twice. |
| Unfamiliar-person usability check | FAIL / deferred | User confirmed on 2026-10-26 that no one else has tried the app; a possible friend check is deferred until later. |
| Dated app screenshots and public URL | PASS | Existing committed timeline contains local and public captures. Block 7 reuses two inspected images with explicit dates and provenance; no old folder was modified. |
| Repair commit and two sync workers on Render | PASS from supplied screenshots | User's dashboard images show source 332f01b, Using worker: sync, and worker PIDs 59/60 on one instance at 03:17:27 PDT on 2026-10-24. Images were reviewed on 2026-10-26 and remain conversation attachments. |
| Repair demo, fake upload, report downloads, new wording, and refresh recovery | PASS, user-reported | User said the remaining verification steps were complete and working. Not an independent agent replay of these checks. Earlier public runs are recorded separately. |
| Processing timeout, cleanup, replacement, and recovery | PASS locally and in CI | Real local server test and repair CI include the regression. No intentionally stalled public request was sent; dashboard worker logs alone do not prove the timeout value. |
| Hosted Python 3.12/3.13/3.14 checks | PASS for repair commit | Run [40085196045](https://github.com/GutsJr75/DrawerCheck/actions/runs/40085196045) on 332f01b completed 2026-10-24; job steps independently inspected 2026-10-26. Lint, formatting, core tests, CLI help, and optional web/server tests succeeded. No hosted result is claimed for the subsequent docs commit. |
| Local tests and both Ruff checks | PASS | Block 7 commands and results are in LEARNING_LOG.md. The server test needs local Unix-socket permission. |
| README and interview material describe delivered features honestly | PASS | Public-demo entry point, existing screenshots, core/web setup, temporary results, hosting limits, tool explanations, pitches, interview answers, and sharing text updated in block 7. |
| Real-business readiness, full accessibility certification, uptime, capacity, and Render peak memory | Not claimed | Synthetic examples and local measurements do not establish these properties. |

## When the deferred checks are taken up

For the friend check, let someone unfamiliar with the project open the public
site without coaching. Ask them to run the example, find and explain one item
needing review, open its drawer, and download a report. Record where they pause,
misunderstand a label, or cannot find the next action. Do not record their name
or other personal data. The project owner doing the same steps is not this
independent check.

For the screen-reader check, use a real screen reader such as VoiceOver. Check
loading, results, and error announcements, then read the drawer tape's row
headers and cells. Determine whether the operator is spoken twice before
changing hidden text. Record the reader, browser, tested states, and actual
result. Any fixes require a separately authorized, contained repair.

## Evidence map

- [Website plan and block 5 evidence](WEB_PLAN.md#verification-and-expanded-definition-of-done)
- [Block 6 review](M8_BLOCK6_REVIEW.md)
- [Block 6 repair and public deployment follow-up](M8_BLOCK6_REPAIR.md)
- [Learning log](LEARNING_LOG.md)
- [Screenshot timeline](screenshots/README.md)
- [Historical core checklist](CORE_CHECKLIST.md)

No further implementation milestone is started by this wrap-up. Optional M9
rules remain opt-in. Suggested repository description/topics are text in the
interview notes, not changes to GitHub settings.
