# Cloudgene spec: aggregated issues

Aggregated from the **Known gaps** and **Open questions** sections of every file under `spec/`
(backend, frontend, deployment) as of 2026-10-23. This file is a working index for turning
issues into task briefs in `tasks/`. It is derived, not normative: the owning spec file's
Known gaps table remains the source of truth (constitution Article 6). When a gap is fixed, update
the owning spec file first, then drop the row here.

How to read it:

- Issues are grouped by theme, not by spec file, because most gaps span backend, frontend and
  deployment. Each group ends with a **Suggested task** that bundles its rows into one brief.
- Requirement IDs (`BE-…`, `FE-…`, `DEP-…`) locate the owning spec file by prefix. Code locations
  are in that file's Known gaps table.
- Severity is the spec's own (`major` / `minor`). No gap is marked `blocker`.
- Rows that appear in several spec files were merged and list all IDs.
- Part B lists the open questions that block or shape a task. Settle them before briefing.

Prefix to file: `BE-ACL` access-control, `BE-ACCT` accounts, `BE-ADM` admin-api, `BE-API`
api-contract, `BE-AUTH` authentication, `BE-CONF` configuration, `BE-DATA` data-model, `BE-PROG`
job-progress-outputs, `BE-QUEUE` job-queue-worker, `BE-RUN` job-runner, `BE-JAPI` jobs-api,
`BE-JSUB` job-submission, `BE-LOG` logging, `BE-CMD` management-commands, `BE-ARCH` overview,
`BE-SRV` server-pages-mail, `BE-WDEF` workflow-definition, `BE-WREG` workflow-registry, `BE-WAPI`
workflows-api, `BE-TEST` backend/tests. `DEP-*` files are under `deployment/`, `FE-*` under
`frontend/`.

---

# Part A: Issues

## 1. Security

Highest-impact group. Four majors share one root cause each, so fix them as units.

| ID | Issue | Refs | Sev |
|---|---|---|---|
| SEC-01 | Worker passes its full environment to every Nextflow/command step, leaking `DJANGO_SECRET_KEY`, `DATABASE_URL` (with DB password), mail settings and `CLOUDGENE_ADMIN_PASSWORD` to any pipeline. Shipped `nextflow.env` does not blank them. | BE-RUN-019, DEP-RT-013, DEP-ENV-029 | major |
| SEC-02 | Systemd units list the code checkout (`/opt/cloudgene`) in `ReadWritePaths=`, so a compromised web process or any workflow step can rewrite the application code. Also drives the `NXF_HOME` default (`/opt/cloudgene/.nextflow`, untracked, not in `.gitignore`) and the SQLite default location. | DEP-PROC-009, DEP-SEC-023, DEP-RT-015, DEP-RT-006, DEP-PROC-006 | major |
| SEC-03 | `settings.yaml` (holds plaintext `mail.password`) and new `nextflow.env` files are created `0644`. No unit sets `UMask=`, so workspaces, uploads, outputs and mail files are world-readable. No deploy check warns about secret-file modes. | BE-CONF-015, DEP-HOME-008, DEP-HOME-003, DEP-SEC-022 | major |
| SEC-04 | No rate limiting anywhere (DRF or nginx). Password spraying across accounts and mail flooding via register/reset are unbounded. `NUM_PROXIES` is unset, so a per-IP throttle would treat all clients as `127.0.0.1`. | BE-AUTH-026, BE-AUTH-027, BE-ACCT-013, DEP-SEC-026 | major |
| SEC-05 | No Content-Security-Policy, and page HTML, footer, workflow `description` and input `label` are rendered with `v-html` unsanitised, so a compromised admin or workflow repo runs script for every visitor. `ConfirmDialog` also renders `message` with `v-html`, relying on callers to escape. | DEP-PROXY-021, BE-SRV-012, FE-PAGE-031/033, FE-FORM-017, FE-UI-023, BE-WDEF (open q) | major |
| SEC-06 | The placeholder `DJANGO_SECRET_KEY` in `cloudgene.env.example` is 84 chars and not in the weak list, so `check --deploy` passes if an operator forgets to replace it. The key is public. | DEP-ENV-034 | major |
| SEC-07 | All jobs run as one OS user with no per-job sandbox; workspaces are `0755`, so any step can read or modify other users' job data. | DEP-RT-018 | major |
| SEC-08 | `create_admin` accepts any password (bypassing registration validation) and prints a generated password to stdout (journald/CI logs). | BE-CMD-014, BE-CMD-012, BE-ACCT-002, DEP-INST-011 | major |
| SEC-09 | Account lockout is per account only: anyone can lock out a known username, and the 429 / early return (faster than `check_password`) enumerates usernames. | BE-AUTH-003 | minor |
| SEC-10 | API tokens never expire, are stored in plaintext, and are not deleted on user deactivation; `auth_logout_create` does not revoke them. Inactive-user rejection is untested. | BE-AUTH-022, open qs | minor |
| SEC-11 | Password-reset confirm ignores `is_active`: a link issued before deactivation still changes the password. | BE-ACCT-015 | minor |
| SEC-12 | `/api/health/` returns `config.errors` (key names and messages) to anonymous callers. | BE-SRV-034, DEP-OBS (gap) | minor |
| SEC-13 | `/api/schema/` and Swagger UI are public (`AllowAny`) and Swagger UI loads JS/CSS from a public CDN, which blocks a strict CSP. | BE-ARCH-008, DEP-SEC-025, DEP-PROXY open q 3 | minor |
| SEC-14 | Activation keys and reset tokens are URL path segments and so appear in every access log. | DEP-OBS-007 | minor |
| SEC-15 | Admin-supplied paths are unvalidated: `install` takes any absolute server path, Nextflow `script` may be absolute or contain `..`, `mail.file_path` / `work_dir` may point anywhere, and the trace `workdir` is opened unchecked. Acceptable under the admin-trusted model; confirm. | BE-WAPI (open q), BE-WDEF (open q), BE-CONF (gap), BE-PROG-005 | minor |
| SEC-16 | Workflow categories are public and never pruned, so category names of private or uninstalled workflows are visible to anonymous callers. | BE-WAPI-007 | minor |
| SEC-17 | Gunicorn trusts forwarded headers from `127.0.0.1`, so workflow steps can reach the loopback port and forge `X-Forwarded-*`. | DEP-RT-020 | minor |
| SEC-18 | No dependency audit/Dependabot; transitive Python deps unpinned (no lock file or hashes). `server_tokens` not disabled in nginx. | DEP-SEC-029, DEP-PROXY-025 | minor |
| SEC-19 | Secret-key bootstrap race: a second process can read an empty `config/secret_key`; an existing empty file also stops start-up until deleted. | DEP-SEC-020, DEP-ENV-032 | minor |
| SEC-20 | Nextflow log tails in the job log can expose resolved config and environment details to non-admin owners; Nextflow stdout ignores the `stdout:`/`stderr:` visibility flags. | BE-PROG-022/023 (open q) | minor |
| SEC-21 | Frontend: ids interpolated into API paths without `encodeURIComponent`; `isInternal` accepts `//evil.example`; `safeNext` accepts `/\evil.example` (throws instead of redirecting). Same-origin only, so defence in depth. | FE-CLIENT-001, FE-API-003, FE-NAV-013, FE-ROUTE-021 | minor |

**Suggested tasks:** (a) scrub step environment, with an allow-list design (SEC-01); (b) harden systemd
sandbox: read-only checkout, `UMask=`, `NXF_HOME` and SQLite relocation (SEC-02, SEC-03, SEC-17); (c) throttling
plus proxy-aware client IP (SEC-04, SEC-09); (d) CSP plus sanitisation decision (SEC-05, SEC-13);
(e) `create_admin` hardening (SEC-08); (f) secret-key hygiene (SEC-06, SEC-19); (g) minor auth
cleanups (SEC-10, SEC-11, SEC-14).

---

## 2. API contract and `schema.yaml` (constitution Article 5)

The schema does not fully describe the API, and nothing validates against it, so drift goes
unnoticed on both sides.

| ID | Issue | Refs | Sev |
|---|---|---|---|
| API-01 | No backend test validates any response against `schema.yaml`; contract tests assert hand-picked fields. No OpenAPI validator is a dependency. | BE-API-006, BE-ADM (5.1d), BE-JAPI-024, BE-WAPI-020, BE-TEST-003/004 | major |
| API-02 | Frontend contract tests use hand-written JSON Schemas, not `schema.yaml` components. No request-body validation against `*Request` components. | FE-API-012, FE-API-014, FE-TEST-003, FE-AUTHV, FE-PROF | major |
| API-03 | Hand-written frontend schemas and fixtures encode shapes the server never sends: `workflows_list` as a plain array (server sends `PaginatedWorkflowList`), `category_name: null` fixture, `User` mock missing required fields, extra enums for job `state` and input `type`. | FE-API-013 | major |
| API-04 | `jobs_create` documents only `workflow` and `job_name`. Per-input fields (multipart parts keyed by input id), `workflow_id`/`name` aliases and `x-www-form-urlencoded` are undocumented. | BE-API-004, BE-API-052, BE-JSUB-002, FE-API-004 | major |
| API-05 | `me_destroy` requires a JSON body `{"password"}` that drf-spectacular drops on DELETE, so the shape lives outside `schema.yaml`. | BE-ACCT-023, BE-API-004, FE-API-004, FE-PROF-042 | major |
| API-06 | Error statuses are collapsed to a single `default: Error` response; status codes come from code, not schema. | BE-API-007 | major |
| API-07 | `JobList/JobStatus/JobDetail.expires_at` is declared required and non-nullable, but is `null` for every unfinished job (and when retention ≤ 0). Violates the contract for all active jobs. | BE-JAPI-007, BE-API-008, FE-JDET (gap) | major |
| API-08 | `Workflow.category_name` declared non-nullable string; server returns `null` with no category. | BE-API-008, FE-API-013 | minor |
| API-09 | `health` returns `503` with a `Health` body when the DB is down; the schema documents only 200. `last_seen` uses `+00:00` rather than `Z`. | BE-API-028, BE-SRV-035 | major |
| API-10 | Query parameters missing from schema (`workflows_list.category`, `jobs_outputs_retrieve.inline`); `AdminUserViewSet` class-level params leak onto retrieve/patch/destroy; `jobs_list.state` declared single-value but comma lists are used (`Active` sends `waiting,running`). | BE-API-003, BE-WAPI-003, BE-JAPI-020, BE-JAPI-006, FE-JLIST-008 | minor |
| API-11 | Untyped fields: `WorkflowInput.value`, `JobInput.value`/`files`, `WorkflowInput.checkbox_values`, `SystemLog.metadata`, `NextflowSettings.variables`, `WorkflowInput.type`; job/step `state` have no enum (`JobStatusEnum` override unused). | BE-API-004, FE-JLIST-017 | minor |
| API-12 | `jobs_outputs_retrieve` documents only `application/octet-stream`; real types and the 404 envelope body are undocumented. | BE-API-053, BE-JAPI-019 | minor |
| API-13 | Admin workflow responses are dicts that bypass `AdminWorkflowSerializer`, so the serializer never checks them. | BE-API-004 | minor |
| API-14 | DRF `DefaultRouter` root view and format-suffix routes (`/api/`, `/api/workflows.json`) probably exist outside the schema and the 404 catch-all. Unverified. | BE-API-003 | minor |
| API-15 | 34 of 65 `operationId`s are auto-derived and rename silently with URLs. Schema cannot express admin-only operations. | BE-API-005, BE-API-033 | minor |
| API-16 | `admin_workflows_install` returns code `not_found` with status `400` (also `BE-WREG-002`); every other `not_found` is 404. | BE-API-024, BE-WAPI-019, BE-WREG-002 | minor |
| API-17 | No `handler500`: an exception outside a DRF view on `/api/` returns Django's HTML. nginx 413/502/504 are also HTML, so the SPA shows generic errors. | BE-ARCH-016, DEP-PROXY-013, DEP-PROXY-014, FE-FORM-030 | minor |
| API-18 | `PUT` on admin workflows behaves as partial update. | BE-WAPI-018 | minor |
| API-19 | The staleness gate "CI fails" has no CI. The frontend/backend operation catalogues are not checked against each other; the shared `validation_cases.json` is imported from outside `frontend/` (pending amendment P2). | BE-API-002, FE-API-011, FE-API-017 | minor |

**Suggested tasks:** (a) fix the schema gaps API-04..API-16, since each is small and they touch
`SPECTACULAR_SETTINGS` / serializers together; (b) backend schema-validating contract tests (API-01), which
needs the validator decision from Part B; (c) switch frontend contract tests to schema-derived
validators and remove the shape-tolerance fallbacks (API-02, API-03, FE-04). (c) depends on (a).

---

## 3. Deployment and operations

| ID | Issue | Refs | Sev |
|---|---|---|---|
| DEP-01 | Nothing runs `manage.py` with the unit environment. The documented `migrate`, `collectstatic`, `create_admin`, `check --deploy` silently use SQLite at `/opt/cloudgene/db.sqlite3`; production PostgreSQL is never migrated and the admin lands in the wrong DB. The env file is root-only, so the `cloudgene` user cannot source it. | DEP-API-005, DEP-DB-020, DEP-INST-008, DEP-INST-021 | major |
| DEP-02 | Static assets: production serves the build dir via `WHITENOISE_USE_FINDERS=True` (so `collectstatic` isn't required and the smoke test can't detect a miss); `SPA_INDEX_FILE` is read from the build dir per request; build-in-place leaves new page loads blank/503 during build → migrate → collectstatic → restart. | DEP-STATIC-011, DEP-STATIC-012, DEP-STATIC-031 | major |
| DEP-03 | Old chunks survive redeploys only because `collectstatic` runs without `--clear`; this is undocumented and untested, nothing prunes them, and the smoke script clears `staticfiles/`. An open tab cannot lazy-load unvisited routes after a redeploy (no `router.onError`). | DEP-STATIC-030, DEP-STATIC-032, DEP-HARN-017, FE-ROUTE-052 | major |
| DEP-04 | Hashed Vite assets get `max-age=60`, not immutable; no precompressed files and no gzip in the nginx example; the commented `/static/` block sets `expires 30d` on unhashed files; the nginx comment about far-future headers is untrue. | DEP-STATIC-020, DEP-STATIC-024, DEP-PROXY-016/017, nginx comment | minor |
| DEP-05 | Large output downloads to slow clients are truncated: sync gunicorn workers die at `timeout` (300 s) beyond nginx's 1 GiB temp buffer. | DEP-WEB-015 | major |
| DEP-06 | `client_max_body_size` equals `max_upload_mb` with no multipart headroom; `max_upload_mb` can be raised at runtime with no nginx check. | DEP-WEB-031, DEP-PROXY-012, DEP-WEB-038 | minor |
| DEP-07 | `TimeoutStopSec` is fixed (120 s) while shutdown stops jobs serially (~10 s each), so more than ~12 running jobs get the worker SIGKILLed; default `KillMode` means systemd signals Nextflow directly too. | DEP-PROC-024, DEP-PROC-023, BE-QUEUE-014 | minor |
| DEP-08 | Gunicorn stop uses `graceful_timeout` (30 s), not the 300 s the unit comment and `TimeoutStopSec=310` assume; uploads >30 s are cut on every restart. | DEP-PROC-013 | minor |
| DEP-09 | `ExecReload=HUP` with `preload_app` does not load new code. | DEP-WEB-016 | minor |
| DEP-10 | Every upgrade fails all running jobs (no drain/"restart when idle"); no `migrate --check` at start; no rollback tooling; no expand-then-contract migration rule. | DEP-INST-024, DEP-INST-031, DEP-DB (open q 5) | minor |
| DEP-11 | `cloudgene-cleanup.service` runs two `ExecStart=` lines, so a failing `cleanup_jobs` skips `cleanup_logs`. | DEP-PROC-034, DEP-API-062 | minor |
| DEP-12 | `ReadWritePaths` is hard-coded, so a different `CLOUDGENE_HOME` or an external `work_dir` silently becomes read-only. `ProtectHome=true` with a home under `/home` breaks `~/.nextflow`. Units use `After=network.target` only (remote PostgreSQL). | DEP-HOME-004, DEP-PROC-006, DEP-ARCH-021, DEP-PROC-008 | minor |
| DEP-13 | Env example omits `CLOUDGENE_ADMIN_PASSWORD` and nine `GUNICORN_*` variables; bad integer env values abort start-up with an unnamed `ValueError` (settings) or silently fall back (gunicorn); `API_JSON_BODY_MAX_MB` > 10 has no effect. | DEP-API-003, DEP-ENV-050, DEP-ENV-012, DEP-ENV-013, DEP-ENV-027 | minor |
| DEP-14 | No warning when `CLOUDGENE_HOME` is unset or `DATABASE_URL` is missing with `DEBUG=False` (data lands in the checkout; silent SQLite fallback). | DEP-ENV-041, DEP-HOME-001, DEP-DB-002 | minor |
| DEP-15 | `/api/health/` is blind to a stuck queue (worker alive, jobs not starting, queue paused) and to a missing Java/Nextflow. | DEP-OBS-016, DEP-RT-001/003 | major |
| DEP-16 | Logging: gunicorn lines stay plain text under `LOG_FORMAT=json`; gunicorn's `%(h)s` is always 127.0.0.1; `LOG_LEVEL=DEBUG` can't enable `cloudgene.*` debug; no metrics endpoint. | DEP-OBS-003, DEP-OBS-006 | minor |
| DEP-17 | `CLOUDGENE_HOME` is never seeded (`ensure_home()` is never called), so a fresh production home has no pages or `settings.yaml`. Default `mail.backend: file` accumulates tokens forever. Upload temp files use the unit's private `/tmp` with no `FILE_UPLOAD_TEMP_DIR`. | DEP-HOME-007, DEP-HOME-016, DEP-HOME-012 | minor |
| DEP-18 | External `work_dir`s (Nextflow work) are never cleaned by delete/restart/retention/vanish and often hold the most data. | BE-QUEUE-027, DEP-HOME-015 | major |
| DEP-19 | PostgreSQL: `CONN_HEALTH_CHECKS` unset, so one request per worker fails after a DB restart. No backup/restore tooling or test. | DEP-DB-005, DEP-DB-040 | minor |
| DEP-20 | Single-worker guarantee is a host-local `flock`; two hosts sharing one DB each fail the other's jobs every tick. | BE-QUEUE-011/016, DEP-ARCH-011, DEP-PROC-021, DEP-DB-030 | minor |
| DEP-21 | `check --deploy` with `DJANGO_SECURE_SSL_REDIRECT=1` makes a local `/api/health/` probe return 400/301. Smoke script uses `|| true` and sets no TLS variables. | DEP-API-033, DEP-SEC-009, DEP-TEST-006 | minor |
| DEP-22 | Python/Node/Java/Nextflow versions are pinned nowhere (no `.python-version`, `.nvmrc`, `engines`). No resource limits (`MemoryMax=`, `TasksMax=`). | DEP-ARCH-022, DEP-STATIC-005, FE-ARCH-043, DEP-RT-017 | minor |
| DEP-23 | `run_worker` doesn't handle `HUP`; `--once` installs no SIGTERM/SIGINT handler. | DEP-API-061, BE-QUEUE-015 | minor |

**Suggested tasks:** (a) `manage-prod` wrapper or env-file loading (DEP-01, depends on the Part B
decision); (b) static asset release strategy (DEP-02, DEP-03, DEP-04, the `router.onError` fix in FE-02); (c) worker shutdown/drain
and systemd tuning (DEP-07..DEP-12, DEP-23); (d) external `work_dir` cleanup (DEP-18); (e) download path
(DEP-05); (f) health/queue observability (DEP-15, DEP-16).

---

## 4. Job queue, runner and job lifecycle

| ID | Issue | Refs | Sev |
|---|---|---|---|
| JOB-01 | Worker updates `current_step`, step `processes` and messages without touching `Job.updated_at`. The SPA's change detection compares only `updated_at`, so live progress lags up to 10 s instead of 2 s. | BE-QUEUE-028, FE-JDET-010 | major |
| JOB-02 | Cancel adds "Cancellation requested." to a job that finished in the race window. | BE-QUEUE-019 | minor |
| JOB-03 | Queue limit race: waiting jobs are counted then inserted without a lock, so concurrent submits can exceed `max_queue_size`. Restart skips maintenance mode and the queue limit. | BE-JSUB-027, BE-ADM-042 | minor |
| JOB-04 | `max_upload_mb` is checked only after Django has spooled the whole body; chunked requests skip the `Content-Length` guard. | BE-JSUB-023, BE-ARCH-010 | minor |
| JOB-05 | Output listing: the 5 000-file cap only breaks the inner loop (can list far more), truncation is silent, and nested directory symlinks are silently omitted. | BE-PROG-018 | minor |
| JOB-06 | No cap on messages per job; every status poll returns all messages and steps; `queue_position` and `expires_at` cause N+1 queries on lists. | BE-PROG-007, BE-JAPI-010 | minor |
| JOB-07 | Trace row lacking `hash` and `task_id` gets an unstable key and inflates task counts (hand-edited configs only). | BE-PROG-012 | minor |
| JOB-08 | Nextflow killed by signal reports `exited with code -9`; uninstalled workflow gives a confusing "cannot find project" error. | BE-RUN-022, BE-RUN-008 | minor |
| JOB-09 | Job `inputs` falls back to all raw parameters (including hidden inputs and file paths) when stored YAML can't parse. | BE-JAPI-009 | minor |
| JOB-10 | Workspace removal ignores errors silently after the row is marked deleted; `download_count` increments before streaming and on `HEAD`. | BE-JAPI-014, BE-JAPI-018 | minor |
| JOB-11 | Admin dashboard counts include soft-deleted jobs; legacy-model indirection and a dead `queue_summary()` remain. | BE-ADM-011, BE-ADM-010 | minor |
| JOB-12 | `run_worker --once` exits 0 after `--timeout` although it stopped jobs. | BE-CMD-043 | minor |
| JOB-13 | Job-name sanitiser strips only ASCII controls (C1 controls and U+202E remain). | BE-JSUB-008 | minor |
| JOB-14 | `JobOutput` has no `(job, output_id, path)` uniqueness; `Job.status` values aren't DB-constrained; `Workflow.category` cascades on delete; legacy `Workflow` columns and `maintenance` status are unused. | BE-DATA-005/009, data-model gaps, BE-WREG | minor |

**Suggested tasks:** (a) JOB-01 alone, since it is the only major and has a frontend half (touch `updated_at`, or add a
dedicated progress token); (b) output listing and messages caps (JOB-05, JOB-06); (c) the rest bundled as
"worker/job hardening".

---

## 5. Workflow definition, registry and workflow API

| ID | Issue | Refs | Sev |
|---|---|---|---|
| WF-01 | When `settings.yaml` is unreadable, `load_settings` falls back to `apps: []` and the next sync deletes or uninstalls every registry-managed workflow. Sync should be skipped on load errors. | BE-WREG-001, BE-WREG-010 | major |
| WF-02 | An invalid earlier entry with a readable `id` claims it, so a later valid entry is marked duplicate; duplicate ids `<id>~<n>` break `app_config_dir` and the Nextflow settings endpoints return 500. | BE-WREG-007, BE-WREG-024, BE-WAPI-017/018 | minor |
| WF-03 | `copy=True` copies the directory before the duplicate-id check, so a 409 leaves it behind. Uninstall never removes the copy or `apps/<id>/nextflow.*`. | BE-WREG-018, BE-CMD-024 | minor |
| WF-04 | Sync: change signature ignores unresolved entries; YAML re-read after validation; first request in every process runs a full sync; per-process lock only. | BE-WREG-017, -008, -016, -014 | minor |
| WF-05 | `install_workflow` help text says `$CLOUDGENE_HOME/apps` then cwd, but code tries cwd first; `sync_workflows` help claims it runs at worker start; `sync_workflows` always exits 0 on invalid apps. | BE-CMD-022, BE-CMD-030, open q | minor |
| WF-06 | Group names: `--groups`, `admin_workflows_update` and `install` bypass the group-name rule and case-insensitive duplicate check that `admin_groups_create` applies. Deleting a group leaves its name in `apps[].groups`. | BE-CMD-021, BE-WAPI-013, FE-AWF-032, BE-ADM (open q 1) | minor |
| WF-07 | Definition parsing is lenient: unknown keys silently ignored, out-of-range `number` defaults accepted, `version: 1.10` becomes `'1.1'`; unsupported steps stay loadable. | BE-WDEF-029/030/010 | minor |
| WF-08 | Visibility rule is implemented three times (`can_access`, `WorkflowViewSet` filter, `is_admin_user`); `IsAdminOrReadOnly` unused. | BE-ACL-001, BE-ACL-003 | minor |

**Suggested task:** WF-01 alone first (data-loss risk); WF-02..WF-04 as "registry robustness".

---

## 6. Accounts, admin API, logging, configuration

| ID | Issue | Refs | Sev |
|---|---|---|---|
| ADM-01 | Two password policies: API flows ignore `AUTH_PASSWORD_VALIDATORS`; `create_admin` skips `validate_email`; its `--email` collision raises `IntegrityError`; existing user's `--email`/`--full-name` silently ignored. | BE-ACCT-002, BE-CMD-015 | minor |
| ADM-02 | Admin-action audit trail is inconsistent: user/group changes and logins pass no `extra={'user'}`; lockout events file under `accounts`; config/health errors log on `core.*`, so they never reach Admin → Logs; `cleanup_*` commands log nothing. | BE-ADM-003, BE-LOG-009/011/007, BE-CONF-004, BE-SRV-031 | minor |
| ADM-03 | `SystemLog` inserts are synchronous inside the caller's transaction without a savepoint (poisons PostgreSQL transactions; dropped on rollback; dropped silently on locked SQLite); `timestamp` is insert time. | BE-LOG-008, data-model gap | minor |
| ADM-04 | Admin settings: `config` and `env` are two non-atomic writes; `nextflow.env` lines unvalidated; SMTP test runs synchronously (up to 30 s) and returns raw exception text; all SMTP sends block web workers. | BE-ADM-056, BE-ADM-054, BE-SRV-054 | minor |
| ADM-05 | Invalid `is_active` filter values are silently ignored instead of 400. | BE-ADM-020 | minor |
| ADM-06 | Config: typo'd keys silently ignored; several fields not format-checked; `worker.lock` missing from `.gitignore`; `ensure_home()` never called. | BE-CONF (gaps), BE-CONF-019, DEP-HOME-022 | minor |
| ADM-07 | CLI argument handling: `cleanup_logs --days -5` message wrong; `cleanup_jobs --days` accepts negatives silently. | BE-CMD-060, BE-CMD-050 | minor |
| ADM-08 | Mixed `request.path` vs `path_info` under `SCRIPT_NAME` prefixes (sync middleware, JSON CSRF). | BE-ARCH-011 | minor |

---

## 7. Frontend: functional defects

| ID | Issue | Refs | Sev |
|---|---|---|---|
| FE-01 | Home page fetches only the first page of `workflows_list` (20), so workflows beyond that are invisible with no indication. | FE-PAGE-005, FE-API-007 | major |
| FE-02 | No `router.onError` handler, so after a redeploy an open tab silently fails to navigate to unvisited routes. | FE-ROUTE-052 | major |
| FE-03 | Admin dashboard ignores `config {ok, errors}`, so admins get no signal that `settings.yaml` is invalid. | FE-ADASH-018 | major |
| FE-04 | Fallbacks for non-contract shapes (`data.results ?? data`, legacy `job.status` etc.) hide contract breaks. Also legacy-shape branches in `apiErrorMessage` and e2e helpers. | FE-API-006, FE-STORE-030, FE-JLIST, FE-ADASH, FE-PAGE-005, FE-AWF, FE-CLIENT-031, DEP-HARN-041 | minor |
| FE-05 | Stale-response / route-param reuse bugs: job detail and workflow settings/run pages don't react to param changes; overlapping polls (dashboard, user search, static page slug, `server.load`) can apply out of order. | FE-JDET-030, FE-AWF-030, FE-FORM, FE-ADASH-010, FE-AUSER-012, FE-PAGE-020, FE-NAV-002, FE-STORE-022 | minor |
| FE-06 | Polling doesn't pause on hidden tabs; job detail keeps polling after 404; refresh errors silently swallowed; elapsed time uses browser clock instead of server `duration_seconds`. | FE-JDET-012/013/005, FE-JLIST-011/013 | minor |
| FE-07 | Buttons derived from hard-coded state lists instead of `can_cancel`/`can_restart`, leading to 409s; duplicate job API functions; hard-coded `jobLogUrl` instead of `log_url`. | FE-ADASH-034, FE-API-008/009/002, FE-JDET-025 | minor |
| FE-08 | Logout failure leaves the user on a protected page with an unhandled rejection. | FE-AUTHV-020, FE-NAV-017 | minor |
| FE-09 | Pagination issues: deleting the only job on the last page 404s with stale table; page size hard-coded to 20; group members modal truncates at 200; non-paginated assumptions. | FE-JLIST-018, FE-ADASH-033, FE-AUSER-033, FE-API-007 | minor |
| FE-10 | Admin forms: unsaved edits lost silently; General Save reverts concurrent maintenance changes; field errors shown only for some inputs; install not disabled while busy; `Promise.all` makes a Nextflow-call failure hide the whole workflow page; free-text group input skips validation. | FE-ASET-003/011/041, FE-AWF-018/030/032/033 | minor |
| FE-11 | Run form: submit enabled despite `definition_errors`; raw input ids in 400 messages; number inputs drop non-numeric text; file removal doesn't reset the input; checkbox/terms help ignored; radio groups can't be cleared; unknown input type renders a label with no control; `separator` label dropped. | FE-FORM-006/013/014/022/027/029, open qs | minor |
| FE-12 | Profile: password change leaves stale token on screen; token regenerate/revoke has no confirmation; `last_admin` error marks password invalid; Cancel keeps typed password; store holds `Profile` instead of `User`; `_clear()` is a private action used externally. | FE-PROF-022/036/043/040/004, FE-STORE-009/008 | minor |
| FE-13 | Auth/routing: logged-in users can open `/login` and `/register`; login/register inputs use `autocomplete="off"`; `Login to run` drops `next`; no 404 page (redirect to `/`); no `scrollBehavior`; non-admin redirect gives no message; boot-time `auth_me` failure logs user out; failed `server_info` is silent. | FE-AUTHV-004/014, FE-PAGE-006, FE-ROUTE-012/051, FE-STORE-004/024, FE-NAV-003 | minor |
| FE-14 | CSRF failure surfaces as raw "CSRF Failed" with no recovery; no request timeouts; four views check `err.response?.status` instead of `apiErrorCode`. | FE-CLIENT-012/050/034, FE-ARCH-021 | minor |
| FE-15 | Remaining: no `document.title`; `Back to top` appends `#`; navbar stays open on mobile; `AdminLayout` not responsive; fixed 70px body offset; `Escape` doesn't close modals; `home` failure silently ignored. | FE-ROUTE-050, FE-NAV-052/053/050, FE-PAGE-003/007 | minor |
| FE-16 | Admin lists omit supported filters (`search` on jobs; `group`/`is_active` on users; log `level`; component list); `GroupManagementModal` has an unused `show` prop; Remove button wrongly disabled for all superusers. | FE-ADASH-031, FE-AUSER-034 (+ gaps), FE-ASET-050 | minor |

## 8. Frontend: accessibility and shared components

| ID | Issue | Refs | Sev |
|---|---|---|---|
| A11Y-01 | `ConfirmDialog` lacks `role="dialog"`, `aria-modal`, labelling, focus management, `Escape`; three different destructive-confirm implementations. | FE-UI-024, FE-UI-020 | minor |
| A11Y-02 | `Pagination`: disabled buttons stay focusable and can emit `change(0)` or out-of-range pages; no window; no `aria-current`. | FE-UI-032/033 | minor |
| A11Y-03 | Decorative icons lack `aria-hidden`; icon-only status badge relies on `title`; radio group has no accessible name. | FE-UI-052, FE-JLIST-019, FE-FORM | minor |

## 9. Frontend: dead code and housekeeping

| ID | Issue | Refs | Sev |
|---|---|---|---|
| CLEAN-01 | Dead code: `useJobsStore`, `listCategories`, `getUser`, `jobOutputUrl`, `adminListJobs`/`adminCancelJob`, `restartJob`; transitional `data.message` shim; unused custom matchers. | FE-STORE-032, FE-API-016, FE-CLIENT-035, FE-TEST-003 | minor |
| CLEAN-02 | Vite template leftovers (`hero.png`, `vite.svg`, `icons.svg`); stock `frontend/README.md`; `chart.js` installed but unused; comments cite superseded `plans/SPEC.md`. | FE-ARCH-044, open q, FE-CLIENT, FE-STORE | minor |
| CLEAN-03 | Naming: `PasswordResetView`/`PasswordRecoveryView` are inverted relative to the API; `data-testid` fall-through on the job-detail dialogs overrides `ConfirmDialog` ids. | FE-AUTHV, FE-JDET | minor |
| CLEAN-04 | `npm run test:coverage` fails (`@vitest/coverage-v8` missing). | FE-TEST-012 | minor |

---

## 10. Testing, CI and traceability

| ID | Issue | Refs | Sev |
|---|---|---|---|
| TEST-01 | No hosted CI at all. Schema staleness, migrations check, PostgreSQL, smoke and e2e run only by hand; the PostgreSQL-only claim concurrency test is skipped in routine runs, so BE-QUEUE-006 is unproven. | BE-TEST-019, BE-TEST-009/010, DEP-HARN-070..075, DEP-TEST-012, DEP-DB-053 | major |
| TEST-02 | Playwright is not pinned (README claims it is); `e2e/requirements.txt` uses `>=` ranges, so e2e is unreproducible. README and `e2e/README.md` give conflicting install instructions. | DEP-HARN-050, BE-TEST-021 | major |
| TEST-03 | Spec coverage: 192 deployment, 75 backend and ~107 frontend MUST requirements have only planned tests; none of the planned procedure scripts (`smoke_install/upgrade/backup_restore/runtime.sh`) exists; 76 requirements cite planned `dep-files::` tests, while only 1 of 7 `deploy/` files is tested. | DEP-TEST-003/007/011, BE-TEST-017, FE-TEST-006 | major |
| TEST-04 | Frontend: 0 of 21 route views mounted in vitest; no test injects markup and asserts it renders as text; several user flows have only planned e2e tests. | FE-TEST-006/007/010 | major |
| TEST-05 | `smoke_gunicorn.sh`: readiness loop never fails; `Cache-Control` and health not asserted; `check --deploy` ignored; clears the checkout's `staticfiles/`; SQLite only; not run by `scripts/test.sh`; `--skip-build` only as first arg. | DEP-HARN-015/016/017, DEP-TEST-005/006 | major |
| TEST-06 | `e2e` harness: `--postgres` ignored silently; no `--strict-markers`; `serial` marker unenforced; `xfail_strict=false` while spec requires strict; e2e stack uses `runserver`, not gunicorn; hard-coded `/usr/bin/*` in a fixture; pre-T01 fallbacks hide renamed endpoints. | DEP-HARN-004/027/034/035/041, BE-TEST-015/016 | minor |
| TEST-07 | `scripts/test.sh` can't run a single Django test or a vitest-only gate; unit mode needs Node. | BE-TEST-001, FE-TEST-001 | minor |
| TEST-08 | Traceability is checked by hand/one-off script; citations inconsistent (layers, formats, paraphrased names, 41 planned vitest files in 5 locations). | BE-TEST-020, DEP-TEST-001/008/011, FE-TEST-013/014 | minor |
| TEST-09 | Missing tests for: schema lint, error-code registry, authorisation matrix, runner isolation, secret-key generation, idempotent queue actions, SIGTERM handling, logging layout, `DATABASES` settings, nginx/systemd/gunicorn config. | BE-TEST-006/007/008/011, BE-ARCH-019/025, BE-ADM-014/027/043, BE-QUEUE-014/022, BE-LOG-001, DEP-DB-001/004/010, DEP-API-020/021 | minor |
| TEST-10 | Vitest HTTP not blocked by default; no e2e id existence check; no coverage measurement. | FE-TEST-002/008, backend gap | minor |

**Suggested tasks:** (a) minimal CI (TEST-01, TEST-02), which unlocks most others; (b) fix `smoke_gunicorn.sh`
(TEST-05); (c) config-file tests for `deploy/` (TEST-03); (d) a traceability checker script (TEST-08).

---

## 11. Docs vs code discrepancies (`docs/DEPLOYMENT.md` and others)

Not code bugs, but each needs a decision on which side is right.

| ID | Discrepancy | Refs |
|---|---|---|
| DOC-01 | Docs say the worker takes an "exclusive DB lock"; code uses a host-local `flock`. | DEP-ARCH (open q 1) |
| DOC-02 | Docs say running jobs survive a worker restart / no drain step; code fails them. | DEP-INST (open q 5) |
| DOC-03 | Docs say `settings.yaml` is created by `ensure_home()` on first run; code never calls it. | DEP-HOME (open q 1) |
| DOC-04 | Docs and code disagree on whether `DJANGO_SECRET_KEY` is required in production. | DEP-ENV (open q 1) |
| DOC-05 | `docs/DEPLOYMENT.md` §1 `useradd --create-home` then `git clone` into it fails; build steps run as the wrong user. | DEP-INST (open q 1) |
| DOC-06 | Docs say production serves from `STATIC_ROOT`; code uses finders. | DEP-STATIC-011 |
| DOC-07 | Docs name the log `.nextflow.log`; runner writes `logs/nextflow.log`. | DEP-HOME (open q 3) |
| DOC-08 | Docs' SystemLog retention wording reads opposite to the code. `client_max_body_size >= max_upload_mb` guidance lacks the headroom the spec requires. | DEP-OBS (open q 4), DEP-WEB (open q 4) |
| DOC-09 | Docs say `check --deploy` "must report no issues", but the smoke test ignores its result. | DEP-SEC (open q 5) |
| DOC-10 | The documented user commands (`sudo -u cloudgene … manage.py`) use the wrong environment (see DEP-01). | DEP-API-005 |
| DOC-11 | Root README says Playwright is pinned in `requirements.txt` (it isn't). | DEP-HARN-050 |

---

# Part B: Open questions that need a maintainer decision

Grouped by the tasks they gate. Questions marked ★ block a Part A suggested task.

### Security and trust model
- ★ **Sanitise or CSP?** Sanitise page HTML / workflow descriptions server-side, client-side, both, or rely on CSP alone? (Also: should `img-src` allow `https:`; Swagger UI exempt, self-hosted or disabled?) Refs: BE-ADM q3, FE-PAGE q1, DEP-PROXY q1–3, BE-WDEF q1, FE-FORM q1.
- ★ **Is per-job isolation in scope** (DEP-RT-018), or is Cloudgene single-tenant with mutually trusting users? Determines SEC-07 and how far SEC-01 must go.
- ★ **Should `CLOUDGENE_SMTP_PASSWORD` keep reaching every step** (Cloudgene 3 compatibility), or become opt-in per app? Also: should the worker get its own env file; should it strip `DJANGO_*`/`DATABASE_URL`?
- Should install be restricted to directories under `$CLOUDGENE_HOME`? Should the parser reject Nextflow `script` paths outside the app dir?
- Lockout: keep per-account, or key on account + client address? Should tokens be hashed/expire? Should logout revoke the token? Should login accept e-mail?
- Should `/django-admin/` stay enabled in production (IP-restrict)? Support `SECRET_KEY_FALLBACKS` for rotation?
- Move the SMTP password out of `settings.yaml` (env var / separate `0600` file) rather than just tightening the mode?

### Deployment
- ★ **How do operator commands get the unit environment**: shipped wrapper (e.g. `systemd-run --uid=cloudgene --property=EnvironmentFile=…`) or settings loading the env file (`CLOUDGENE_ENV_FILE`)? Gates DEP-01.
- ★ **Static assets**: confirm `collectstatic` becomes mandatory and production serves from `STATIC_ROOT` only; prune via cleanup timer or upgrade step; immutable-header mechanism (`WHITENOISE_IMMUTABLE_FILE_TEST` vs `CompressedManifestStaticFilesStorage`); is 7 days the right chunk retention? Gates DEP-02..DEP-04.
- ★ **Fix for large-download truncation**: `X-Accel-Redirect`, `gthread` workers or bigger nginx temp buffer? Gates DEP-05.
- ★ **Upgrade model**: require pausing the queue, or build a drain mode? Should the worker unit use `KillMode=mixed`, derive `TimeoutStopSec` from `max_running_jobs`, or stop jobs in parallel? Is any start order required for web and worker? Gates DEP-07, DEP-10.
- Should `graceful_timeout` match `timeout` (restarts then take up to 5 min)? Should `ExecReload` be removed, or `preload_app` default off?
- Should settings refuse to start with `DEBUG` off and no `DATABASE_URL`/`CLOUDGENE_HOME`? Is SQLite-with-`DEBUG`-off a supported config? Enable `CONN_HEALTH_CHECKS` whenever `DB_CONN_MAX_AGE > 0`? Adopt an expand-then-contract migration rule?
- Should the app seed `CLOUDGENE_HOME` from `home/` at start-up (mode `0600`), or should docs describe manual seeding? Ship a `systemd-tmpfiles` snippet? Should `cleanup_jobs` prune `mail/` or production forbid `mail.backend: file`? Put `FILE_UPLOAD_TEMP_DIR` under `CLOUDGENE_HOME`?
- Where should `NXF_HOME` live by default, and must the checkout be cloned as root (needed once it is read-only)? Which Nextflow/Java versions are supported, and should `check --deploy` verify them?
- Is multi-host in scope? If not, should the worker refuse to start when the heartbeat names a different live host?
- Is a non-loopback gunicorn bind (restricted by firewall) allowed?
- Metrics: Prometheus endpoint, or health + logs enough? Should health gain a `queue` block, and stay anonymous? Route gunicorn logs through Django `LOGGING`?
- Should `/api/health/` be exempt from `SECURE_REDIRECT_EXEMPT` and accept `127.0.0.1`? Hide `config.errors` from anonymous callers?
- Error envelope for upstream failures (502/503/504): `server_error` or a new `service_unavailable`? Enable gzip for `application/json`?

### API and data
- ★ **Schema validator choice** (`openapi-core` vs `jsonschema` + `referencing`) and the name of the dev requirements file. Gates API-01.
- ★ **`jobs_create` shape**: move to a documented shape (`inputs` JSON part plus file parts) or add an `additionalProperties` note? Gates API-04.
- Should the strict frontend enums (job `state`, input `type`) be added to the backend schema (preferred) or kept as local overlays? `Workflow.category_name`: nullable in schema, or send `""`?
- Should `health` keep its own body on 503? Should errors be listed per operation (`add_error_envelope` map vs `extend_schema`)? Is `/api/schema/` public in production, documented, or admin-only?
- Admin cross-user job behaviour: may admins delete through `jobs_destroy`, should `jobs_list` offer other users' jobs, should admin restart honour maintenance/queue limits?
- Should `queue_position` stay global? Should `jobs_status_retrieve` support incremental messages (`?after=`)? Should `workflows_list` omit `inputs`/`outputs` for list items? Drop `status` from the public serializer?
- Should unactivated accounts/keys expire? Should e-mail change require confirmation? Should account deletion be refused while jobs run? Should `is_staff` and the `admin` group remain equivalent? Does the dashboard `admins` count include inactive admins?
- Data model: add `CheckConstraint` on statuses? Drop legacy `Workflow` columns? Switch `Workflow.category` to `SET_NULL`?
- Registry: give invalid never-valid apps a cache row? Should uninstall remove copied dirs? Should unsupported steps be errors? Should unknown keys in known config sections warn?
- Should orphaned jobs with no started process be re-queued? Warn on stale worker heartbeat? Should Nextflow stdout respect step flags, and should `report.html`/`timeline.html` be downloadable? Should `submitted` be redefined? Unify Nextflow vs command-step log filenames? Preserve folder-upload structure? `Retry-After` on 429/503? Does the queue limit apply to admins?
- Logging: automatic SystemLog retention? Keep the attempted username in failed-login messages? `sync_workflows` non-zero exit on invalid app? `create_admin` refuse to print passwords when stdout isn't a TTY? Should cleanup commands log summaries?

### Frontend
- Home page: page through `workflows_list`, or backend offers an unpaginated list? Group by category (is `categories_list` needed)?
- Dashboard charts: spec them, or drop `chart.js`? Pause polling on hidden tabs (dashboard, logs)? Maintenance toggle in one place or two?
- Client: default timeout (30 s, exempt uploads/log downloads)? Auto-retry once after `csrf_failed`? Remove the legacy-shape fallbacks (treat as contract violations)?
- Routing: "Page not found" view? Redirect logged-in users away from auth pages? Named routes? Set `document.title` from `server.name`? Periodic server-info re-check for the maintenance banner? Re-check auth on tab visibility?
- Remove `useJobsStore` or move `JobListView` onto it (also lets list keep page/filter)? List refresh rate 3 s vs 2 s?
- `ConfirmDialog`: drop HTML messages entirely (text `message` + `subject`)? Migrate inline confirmations to it (profile deletion, admin users, group modal)? Rename password views / require click on `/activate/:key`?
- Job detail: poll logs while running? Inline results view (`inline=1`)? Use server `duration_seconds`?
- Group names on the workflow settings page: same rule as group creation? Install form `enabled: false`? Upload size and queue-full warnings before submit? Directory picker for folder inputs?
- Logs view: fixed component list? Users: expose `group`/`is_active` filters? Keep members modal duplication?

### Testing
- ★ **CI host**; PostgreSQL on every PR or nightly; e2e on PRs touching `frontend/`, `e2e/` or API modules? Gates TEST-01.
- Playwright install policy (README vs `e2e/README.md`). Boot gunicorn in e2e? Disposable host for procedure scripts (VM, systemd container, `systemd-nspawn`)? Run `nginx -t` / `systemd-analyze verify` in config tests when present? Smoke against PostgreSQL when `TEST_DATABASE_URL` is set?
- Should e2e validate every observed `/api/` response against `schema.yaml`? Accept `axe-core` as an e2e dependency? Coverage thresholds? Confirm the vitest layout (`src/test/views/<ViewName>.test.js`, PascalCase).

---

# Part C: Suggested order

1. **Decide the ★ questions** in Part B, since they unblock most briefs.
2. **Small, self-contained majors**: WF-01 (settings fallback wipes workflows), JOB-01 (progress lag), SEC-06 (placeholder key), FE-01 (home page pagination), FE-03 (config errors), SEC-08 (`create_admin`).
3. **Foundations**: TEST-01/02 (CI, Playwright pin), then API-01 (schema validation), which makes API-04..API-16 verifiable.
4. **Deployment hardening bundle**: DEP-01, SEC-01..SEC-03, SEC-17 and DEP-07..DEP-12 share unit files and the env contract, so brief them together or in a strict sequence.
5. **Static asset release strategy**: DEP-02..DEP-04 with FE-02.
6. **Everything minor**: fold into themed clean-up tasks using the "Suggested task" lines.
