# 06 — Minimal hosted CI (GitHub Actions) and a reproducible e2e harness

## Overview

Cloudgene has a complete local test entry point (`scripts/test.sh`: Django checks, migrations
check, Django tests including the `schema.yaml` staleness test, vitest; plus Playwright e2e),
but nothing runs it automatically. The constitution's API rule says "CI fails when
`schema.yaml` is stale" (Article 5.1c), yet there is no CI. The PostgreSQL-only claim
concurrency test (`ClaimConcurrencyTest`) is skipped in every routine run, so the worker's
"one claim per job" guarantee (BE-QUEUE-006) has never been demonstrated on the database that
production uses. The `.claude/skills/fix-ci` skill exists but records "Workflows: TBC (None
yet)".

The e2e harness is not reproducible either. `e2e/requirements.txt` uses `>=` ranges. The root
README claims `playwright==1.56.0` is pinned in `requirements.txt`, but it isn't. The README and
`e2e/README.md` give different install instructions. A fresh machine (or a CI runner) can
therefore install a Playwright whose browser build differs from the one tests were written
against.

This task adds GitHub Actions workflows that run the unit suite on SQLite and PostgreSQL and the
gunicorn smoke test on every push and pull request, and the e2e suite nightly and on demand. It
pins the e2e dependencies so those runs are reproducible. Most other test gaps in spec/ISSUES.md
(schema-validating contract tests, config tests for `deploy/`, a traceability checker) build on
this.

Source: spec/ISSUES.md TEST-01, TEST-02 (BE-TEST-019, BE-TEST-021, DEP-HARN-050,
DEP-HARN-070..075, DEP-TEST-012, DEP-DB-053; also DOC-11). CI host decided: GitHub Actions (the
repository is on GitHub; `gh` and `fix-ci` already assume it).

## Relevant spec

Read before starting:

- spec/constitution.md (Article 5.1c, Article 7)
- spec/deployment/test-harness.md — DEP-HARN-050 (pins), DEP-HARN-070..075 (CI jobs, required
  checks, Postgres concurrency test, nightly e2e, toolchain pins, artifacts, no secrets).
- spec/deployment/tests.md — DEP-TEST-012 and the commands section.
- spec/backend/tests.md — BE-TEST-019, BE-TEST-021, the PostgreSQL run, staleness test
  (BE-TEST-002), migrations check (BE-TEST-005).
- spec/frontend/tests.md — FE-TEST-001 (vitest gate).
- spec/deployment/database.md — the PostgreSQL version production requires.
- spec/deployment/overview.md — DEP-ARCH-022 (Python/Node/Java versions).
- README.md, e2e/README.md, `scripts/test.sh`, `scripts/smoke_gunicorn.sh`.

## Design

### Workflows

Two workflow files under `.github/workflows/`. File names are up to the implementer; record them
in the `fix-ci` skill.

**`ci.yml`, on `push` and `pull_request`:**

| Job | Runs | Notes |
|---|---|---|
| `unit-sqlite` | `scripts/test.sh unit` | Python 3.12, Node 22; pip and npm caches. |
| `unit-postgres` | `scripts/test.sh unit --postgres` | `services: postgres:<version from database.md>`; role with `CREATEDB`; `TEST_DATABASE_URL` set. MUST fail if `ClaimConcurrencyTest` is skipped (DEP-HARN-072), e.g. run that class separately with verbosity 2 and grep for `skipped`, or have the test fail instead of skip when an env flag like `CLOUDGENE_REQUIRE_POSTGRES_TESTS=1` is set. The env-flag approach is preferred: it is explicit and testable. |
| `smoke` | `scripts/smoke_gunicorn.sh` | Builds the frontend. See "Smoke script" below. |

**`e2e.yml`, nightly (`schedule`), on release tags, on `workflow_dispatch`, and on pull
requests that touch `frontend/**`, `e2e/**` or `*/api*`/`*/views*`/`*/serializers*` (DEP-HARN-073):**

| Job | Runs |
|---|---|
| `e2e` | `pytest e2e -n 4 -m "not serial"`, then `pytest e2e -m serial` (SQLite) |
| `e2e-postgres` | the same with `E2E_DATABASE_URL` pointing at a Postgres service; nightly/tag/dispatch only |

Both install Java 21 and a pinned Nextflow (use the version from
`deploy/ansible/group_vars/all/vars.yml` `nextflow_version`, so CI and production match), plus
the pinned Playwright Chromium (`python -m playwright install --with-deps chromium`). On
failure they upload `e2e/.artifacts/` (DEP-HARN-074).

Shared rules:

- No secrets (DEP-HARN-075): only the harness's fixed test credentials. No `secrets.*` references.
- Pin action versions by tag at minimum (`actions/checkout@v4`, `actions/setup-python@v5`,
  `actions/setup-node@v4`, `actions/setup-java@v4`), or by SHA if the user prefers.
- `concurrency:` per ref, cancelling superseded runs.

### Required checks (DEP-HARN-071)

`unit-sqlite`, `unit-postgres` and `smoke` should be required status checks on `main`. That is
a repository setting, not a file. Do **not** change branch protection without asking the user.
Give them the exact `gh api` command or settings path in the final report.

### Pins (TEST-02)

- `e2e/requirements.txt`: every line `==`. `playwright==<version>` must match the Chromium
  build the suite currently passes with. Check what is installed in the environment the user
  runs e2e from (`scripts/test.sh e2e` uses `./venv/bin/python`; Playwright is **not** currently
  in `./venv`, so find out where it comes from before pinning). The README says 1.56.0; confirm
  that before using it.
- Fix the root README and `e2e/README.md` so both name `e2e/requirements.txt` as the single
  install file, with the same command (DEP-HARN-050, DOC-11).
- Add `.python-version` (3.12) and `.nvmrc` (22) or a `frontend/package.json` `engines` field,
  and have the workflows read them, so local and CI toolchains come from one place. This is the
  toolchain half of DEP-22. Do the Java/Nextflow pins only in CI here.

### Smoke script

`scripts/smoke_gunicorn.sh` has known defects (TEST-05). Its readiness loop never fails, and it
clears the checkout's `staticfiles/`. As a required job it must at least fail when gunicorn never
becomes ready. Fix only that, and the `|| true` on `check --deploy` if it hides a real failure
in CI. List any other TEST-05 defect you find in `tasks/todo.md`, not here.

### `scripts/test.sh` changes

Only if needed for CI, e.g. honouring `PYTHON`, which it already does. Keep `scripts/test.sh
unit` the single command that CI calls, so local and CI runs cannot drift.

## Steps

1. Pin `e2e/requirements.txt`; fix README/e2e README install instructions; add toolchain version
   files.
2. Add the Postgres-required flag to `ClaimConcurrencyTest` (fail instead of skip when set).
3. Fix the smoke readiness loop.
4. Add `.github/workflows/ci.yml` and `.github/workflows/e2e.yml`.
5. Push a branch and run both workflows (`workflow_dispatch` for e2e). Ask the user before
   pushing. Iterate until green using the `fix-ci` procedure.
6. **Tests:**
   - `jobs/tests/test_claim_concurrency.py`: with the flag set and SQLite in use, the test
     fails (not skips). Verify by hand once, or add a small test of the skip-or-fail decision
     helper.
   - `core/tests/test_deploy_files.py` (planned config-test home): a `CiConfigTest` that parses
     the workflow YAML and checks job names, the Postgres service, the no-secrets rule and the
     artifact upload (DEP-HARN-070..075). Also a test that every line of `e2e/requirements.txt`
     uses `==` (BE-TEST-021).
7. **Update `.claude/skills/fix-ci/SKILL.md`** "Facts": workflow file names, job names, how to
   re-run, where artifacts land. Add a catalogue entry for each class of failure fixed during
   step 5.
8. **Spec updates** (same change set):
   - spec/deployment/test-harness.md: DEP-HARN-050, -070..075 lose `(planned)` where met; remove
     Known gaps; record workflow file names and the Postgres-required flag.
   - spec/deployment/tests.md: DEP-TEST-012; traceability rows and counts.
   - spec/backend/tests.md: BE-TEST-019, BE-TEST-021; note that `ClaimConcurrencyTest` runs in
     `unit-postgres`; traceability rows and counts.
   - spec/frontend/tests.md: note that vitest runs in CI.
   - spec/ISSUES.md: drop TEST-01, TEST-02, DOC-11, and the CI-host open question.
9. Run the unit suite, smoke script and e2e locally (`/tests` skill) and flake8.

## Acceptance criteria

- [ ] Every push and pull request runs `unit-sqlite`, `unit-postgres` and `smoke` on GitHub
      Actions, and they pass on `main`.
- [ ] `unit-postgres` fails if `ClaimConcurrencyTest` is skipped.
- [ ] A stale `schema.yaml`, a missing migration or a failing vitest fails CI.
- [ ] e2e runs nightly, on tags, on manual dispatch and on relevant pull requests, and uploads
      `e2e/.artifacts/` on failure.
- [ ] `e2e/requirements.txt` is fully `==`-pinned, Playwright matches the browser in use, and
      both READMEs give the same single install command.
- [ ] No workflow uses repository secrets.
- [ ] The user has the command to make the three unit/smoke jobs required checks.
- [ ] `fix-ci` skill facts are filled in; spec updated as in step 8.

## Open questions

Implement the stated default and copy the question into the relevant spec's Open questions.

- **PostgreSQL on every PR, or nightly only?** Default: every PR (the spec requires it, and the
  unit suite is quick). Revisit if it makes PRs slow.
- **e2e on PRs.** Default: path-filtered as above. If the e2e suite proves flaky in CI, keep it
  nightly-only and record the flaky tests in `tasks/todo.md` rather than retrying them silently.
- **Which repository?** `origin` is `qcif/cloudgene4` and `neoformit` is a second remote.
  Workflows run wherever they are pushed. Ask the user which repository's Actions and branch
  protection to configure.
