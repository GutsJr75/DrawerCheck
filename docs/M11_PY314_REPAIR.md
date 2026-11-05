# Python 3.14 deep-JSON test repair

Authorized on 2026-11-04 by the user's "go fix" annotation on the contained
repair plan. Started from `d620c3f`. Application code and the user's existing
uncommitted `docs/WEB_PLAN.md` edit are unchanged. No push or deployment.

## Cause and repair

The expanded [CI run for 9a20875](https://github.com/GutsJr75/DrawerCheck/actions/runs/41951907510)
passed Python 3.12 and 3.13, but failed one assertion on Python 3.14. The
16,000-level array parsed on that runner, then failed the drawer's object
shape validation. The endpoint returned HTTP 400 with the shape-error
message. The test assumed parsing must raise a recursion error and required
the unreadable-request message instead.

The deep-array case now has its own test. It still requires HTTP 400 and
one of the two exact complete plain-error replies. Other malformed and
wrong-shape cases keep their exact-message checks. A separate test forces
the parser to raise `RecursionError` and requires its exact friendly reply,
so that handler is covered on every interpreter. The parser is restored
before Flask decodes the response JSON.

No runtime change, dependency, relaxed input limit, or version skip was
needed. No page appearance changed, so no new screenshots were taken.

## Local verification

- Reproduced the old message mismatch with a temporary pytest probe that
  makes decoding the deep array succeed, matching the CI path. The old
  unreadable-request group had one failure and five passes.
- After the repair, all 18 drawer endpoint tests passed with the normal
  local parser. Both new tests also passed with the parser-success probe.
- Full suite on Python 3.13.5: 825 passed, 14 opt-in browser cases skipped.
- Both Ruff checks and `git diff --check` passed.

The temporary probe was kept outside the repository and is not part of the
application or normal test suite. Python 3.14 is not installed locally;
simulating its observed parser outcome is not a passing Python 3.14 run.
Publication, a passing GitHub matrix on 3.12/3.13/3.14, and live closing-flow
verification remain the next handoff block. M12 has not started.
