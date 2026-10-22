# 03 — Remove server secrets from workflow step environments

## Overview

The worker runs each workflow step (a Nextflow run or a command step) as a child process. The
child's environment is built by `build_env()` in `jobs/runner.py`. That function starts from a copy
of the worker's own `os.environ`, adds `nextflow.env` files and adds the job's `CLOUDGENE_*`
variables (BE-RUN-017).

Under systemd, the worker's environment is everything in `/etc/cloudgene/cloudgene.env`. On the
Ansible deployment this includes `DJANGO_SECRET_KEY` and `DATABASE_URL` (with the PostgreSQL
password), plus `ALLOWED_HOSTS`, `DJANGO_*` hardening flags, `LOG_*` and so on. Separately,
`cloudgene_variables()` deliberately exports `CLOUDGENE_SMTP_PASSWORD` (the `mail.password`
from `settings.yaml`) to every job. As a result, every pipeline, every Nextflow plugin, every
container that passes the environment through, and every command step can read the database
password, the key that signs sessions and tokens, and the mail password.

No workflow needs any of these values. This task removes them from the step environment
entirely: server variables are stripped from the inherited environment, and
`CLOUDGENE_SMTP_PASSWORD` is no longer exported. There is no opt-in. This is a deny rule, not an
allow-list. Ordinary process variables (`PATH`, `HOME`, `LANG`, `TMPDIR`, systemd's own
variables, `JAVA_*`/`NXF_*` set by the operator) still pass through.

Source: spec/ISSUES.md SEC-01 (BE-RUN-019, DEP-RT-013, DEP-ENV-029, major). This also settles
the open question "should `CLOUDGENE_SMTP_PASSWORD` keep reaching every step": no.

## Relevant spec

Read before starting:

- spec/constitution.md
- spec/backend/job-runner.md — Environment (BE-RUN-017, -018, -019), Known gaps.
- spec/backend/workflow-registry.md — `template_utils.VARIABLES` (BE-WREG-028), Open questions
  (SMTP password).
- spec/deployment/environment-config.md — the inventory of every variable `cloudgene.env` may
  hold, DEP-ENV-029 (`CLOUDGENE_ADMIN_PASSWORD`).
- spec/deployment/workflow-runtime.md — DEP-RT-013 (interim blanking in `nextflow.env`),
  DEP-RT-014 (blanking is not isolation), the environment-source table.
- spec/deployment/api-contract.md — the environment section that cites the leak.
- spec/frontend/admin-workflows.md / admin-settings.md — where the admin UI lists the
  `CLOUDGENE_*` variables (it renders `VARIABLES` verbatim).
- spec/backend/tests.md — the planned test home `jobs-worker::test_server_secrets_not_in_step_env`.

## Design

### What is removed

Two sources, both removed before the process starts:

1. **Inherited server variables.** Before env files are applied (first step of BE-RUN-017), drop
   from the copied base environment every variable the server reads from `cloudgene.env`:
   - exact names: every variable listed in the spec/deployment/environment-config.md inventory
     that is not a plain process variable. At least `DATABASE_URL`, `DEBUG`, `ALLOWED_HOSTS`,
     `CSRF_TRUSTED_ORIGINS`, `CLOUDGENE_HOME`, `CLOUDGENE_ADMIN_PASSWORD`, `DEFAULT_FROM_EMAIL`,
     `API_JSON_BODY_MAX_MB`, `INSECURE_FAST_PASSWORD_HASHING`, `LOG_LEVEL`, `LOG_FORMAT`;
   - prefixes: `DJANGO_`, `DB_`, `EMAIL_`, `GUNICORN_`.

   Keep the list as one module-level constant (names plus prefixes) next to `build_env`, with a
   comment pointing at the environment-config spec inventory.
2. **`CLOUDGENE_SMTP_PASSWORD`.** Remove it from `VARIABLES` and from `cloudgene_variables()` in
   `workflows/template_utils.py`. The other `CLOUDGENE_SMTP_*` values are not secrets and stay
   (Cloudgene 3 compatibility).

### Env files

`nextflow.env` files (global and per-app) are admin-controlled and are applied *after* the strip,
so an admin can still set a variable of the same name deliberately (for example a pipeline that
needs its own `DATABASE_URL`). That is an explicit admin choice, not an inherited leak. `$VAR`
expansion in env files runs against the stripped environment, so `DB_PASSWORD=$DATABASE_URL`
expands to empty. State both points in BE-RUN-017/019.

### Guarding against drift

A new settings variable could be added later without updating the strip list. Add a unit test
that collects every environment variable name read by `cloudgene_django/settings.py`,
`core/config.py` and `deploy/gunicorn.conf.py` (by parsing the source for `os.environ`/`getenv`
and the settings env helpers) and asserts each is either covered by the strip list or listed in
a small explicit "safe to pass" set in the test. A new variable then fails the test until someone
decides.

### What this does not fix

Steps still run as the same OS user as the worker. They can read `/proc/<worker pid>/environ`,
`config/settings.yaml` (which holds `mail.password`) and `config/secret_key` (DEP-RT-014). Closing
that requires a separate OS user per job or for the worker, which is SEC-07 in spec/ISSUES.md
and out of scope. The deployment mitigations in DEP-RT-014 (root-only `cloudgene.env`, DB refuses
password-less local access) stay in force. Say so plainly in the spec. This task removes the
casual, default-on leak, so a pipeline that dumps its environment into a log, a report or a
container no longer exposes secrets.

### Interim mitigation retired

DEP-RT-013 currently requires the global `nextflow.env` to blank server variables as an
interim measure. Once the code strips them, that requirement becomes unnecessary. Mark it
`(withdrawn)` (IDs are never reused, Article 4.2), remove the interim block from the
workflow-runtime spec example, and update the environment-source table.

### Interfaces

- No HTTP change. `schema.yaml` is unchanged (the variables list in the admin UI is static
  frontend text or a backend constant; check which). If the admin UI's variable list comes
  from the API, the response shape is unchanged; only the content changes.
- Workflows that referenced `$CLOUDGENE_SMTP_PASSWORD` will now see it unset. There are none in
  `apps/`, fixtures or `e2e/`; check again before merging.

## Steps

1. **Strip list and strip** in `jobs/runner.py` `build_env()`, applied to the base env before
   PATH handling and env files.
2. **Remove `CLOUDGENE_SMTP_PASSWORD`** from `workflows/template_utils.py` (`VARIABLES` and
   `cloudgene_variables()`), and from any frontend listing or docs that names it.
3. **Unit tests**, in the existing homes (spec/backend/tests.md):
   - `jobs/tests/test_worker.py::test_server_secrets_not_in_step_env` (the planned name). Use a
     `base_env` containing `DJANGO_SECRET_KEY`, `DATABASE_URL`, `DB_CONN_MAX_AGE`,
     `EMAIL_HOST_PASSWORD`, `GUNICORN_BIND`, `CLOUDGENE_ADMIN_PASSWORD`, `ALLOWED_HOSTS`,
     `DEBUG`, `CLOUDGENE_HOME`, plus `PATH`, `HOME`, `LANG`, `NXF_OPTS`. None of the server
     variables appear in `build_env()`'s result; the process variables do.
   - Same module: an env file that sets `DATABASE_URL=x` explicitly keeps it (admin intent);
     `FOO=$DJANGO_SECRET_KEY` in an env file expands to empty.
   - Same module or `jobs/tests/test_command_steps.py`: an end-to-end worker run of a command
     step that runs `env` (or `printenv`) and writes its output to the workspace. The output has no
     `DJANGO_SECRET_KEY`, `DATABASE_URL` or `CLOUDGENE_SMTP_PASSWORD`, while
     `CLOUDGENE_JOB_ID` is present.
   - `cloudgene_variables()` no longer returns `CLOUDGENE_SMTP_PASSWORD` even when
     `mail.password` is set; `VARIABLES` no longer lists it (update the existing
     `SubstitutionTest::test_build_variables` and any test that expects it).
   - The drift test described above (suggested home: `jobs/tests/test_runner.py`).
4. **Frontend**: if the admin variable list is hard-coded in the SPA, remove the entry and update
   its vitest test or fixture.
5. **Spec updates** (same change set):
   - spec/backend/job-runner.md: BE-RUN-019 loses `(planned)` and states the exact strip
     rule (names + prefixes, applied before env files). Update BE-RUN-017 to say the base is the
     *stripped* worker environment. Update BE-RUN-018 so that "SMTP values" excludes the
     password. Remove the Known gap. Add Acceptance tests rows.
   - spec/backend/workflow-registry.md: BE-WREG-028 variable list. Close the SMTP-password
     open question.
   - spec/deployment/workflow-runtime.md: withdraw DEP-RT-013, revise DEP-RT-014 (no longer
     "receive `CLOUDGENE_SMTP_PASSWORD` by design"), update the environment-source table and
     the example `nextflow.env`, and remove the Known gap.
   - spec/deployment/environment-config.md: DEP-ENV-029 rationale (the leak is fixed; keeping
     `CLOUDGENE_ADMIN_PASSWORD` out of `cloudgene.env` remains good practice). Remove the
     Known gap and update the open-question text that cites BE-RUN-019.
   - spec/deployment/api-contract.md: the environment section.
   - spec/backend/tests.md and spec/deployment/tests.md: traceability rows and counts.
   - spec/ISSUES.md: drop SEC-01 and the SMTP-password open question.
6. **User docs**: docs that list `CLOUDGENE_*` variables or describe the env passthrough
   (check `docs/ADMIN_GUIDE.md`, `docs/DEPLOYMENT.md`, any workflow-author guide). Remove
   `CLOUDGENE_SMTP_PASSWORD` and state that server variables are not passed to workflows.
7. Run the unit and e2e suites (`/tests` skill) and flake8.

## Acceptance criteria

- [ ] No step process receives `DJANGO_*`, `DB_*`, `EMAIL_*`, `GUNICORN_*`, `DATABASE_URL`,
      `CLOUDGENE_HOME`, `CLOUDGENE_ADMIN_PASSWORD` or any other variable from the
      environment-config inventory, unless an admin sets it explicitly in a `nextflow.env` file.
- [ ] `CLOUDGENE_SMTP_PASSWORD` is neither exported nor listed in `VARIABLES`.
- [ ] Process variables (`PATH`, `HOME`, `LANG`, `NXF_*`, …) still pass through.
- [ ] A drift test fails when the server reads a new environment variable that is not covered.
- [ ] `schema.yaml` is unchanged.
- [ ] Unit tests cover the above; suites pass; flake8 is clean.
- [ ] Spec and docs updated as in steps 5–6; DEP-RT-013 is withdrawn.

## Open questions

Implement the stated default and copy the question into the relevant spec's Open questions.

- **Should env files be allowed to re-add stripped names?** Default: yes, because env files are
  admin-controlled. The alternative is to strip after env files too, which would stop an admin
  from passing a pipeline its own `DATABASE_URL`.
- **`/proc/<pid>/environ` and `settings.yaml` readability.** These remain readable by steps
  until per-job isolation (SEC-07) is decided. No change here.
