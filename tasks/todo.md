- Re-sync the workflow registry when auto_groups (or any code path) creates a group named in `apps[].groups`, so new group members see restricted workflows immediately (from task 01).
- Decide whether `home/config/settings.yaml` should be committed; BE-CONF-018 says it is, but it is git-ignored (from task 01).

## From the spec/ISSUES.md triage (2026-10-23)

Briefed already: WF-01 (task 02), SEC-01 (task 03), SEC-02/03/17 + DEP-12 (task 04), JOB-01 (task 05), TEST-01/02 (task 06), SEC-04 (task 07).

Next up (small, no decision needed):
- Quick-fixes bundle: FE-03 (admin dashboard ignores `config.errors`), SEC-08 (`create_admin` skips password/e-mail validation and prints generated passwords), SEC-06 (add the `cloudgene.env.example` placeholder key to the weak-key list; the Ansible host uses a vault key, so it only affects manual installs). Optionally SEC-19 (secret-key bootstrap race).
- FE-01: home page shows only the first 20 workflows. Brief it once the deployment has (or expects) more than 20.
- DEP-01 is solved in practice by the Ansible `cloudgene-manage` wrapper. Update spec/deployment (DEP-API-005, DEP-INST-008/021, the planned `scripts/manage_prod.sh`) to adopt a shipped wrapper, and fix `docs/DEPLOYMENT.md` (DOC-10). Mostly a spec/docs change.

Blocked on a decision (see spec/ISSUES.md Part B):
- SEC-05: CSP plus HTML sanitisation for pages, workflow descriptions and `ConfirmDialog` (with SEC-13 Swagger UI). Decide: are admins and workflow repos trusted? Sanitise server-side, client-side, or rely on CSP?
- SEC-09: per-account lockout enables username enumeration and lockout-DoS. Decide whether to key on account + address once task 07's throttles exist (from task 07).
- SEC-07: per-job OS isolation. A scope decision (single-tenant with trusted users, or not), not a task yet.
- DEP-02, DEP-03, DEP-04 + FE-02: static asset release strategy (mandatory `collectstatic`, serve from `STATIC_ROOT`, immutable headers, chunk pruning, `router.onError`).
- DEP-05: large downloads truncated by gunicorn sync-worker timeout. Decide: `X-Accel-Redirect`, `gthread`, or larger nginx buffers.
- DEP-07, DEP-08, DEP-10, DEP-23: worker drain and upgrade model, `KillMode=mixed`, `TimeoutStopSec`, `graceful_timeout`.

Later:
- DEP-18: external Nextflow `work_dir`s are never cleaned. Low priority while the only production app uses a remote `az://` work dir; becomes major for any local `work_dir`.
- API-01..API-16: schema-validating contract tests and schema gaps. Do after task 06 (CI) lands; needs the validator choice (`openapi-core` vs `jsonschema`).
- TEST-05: remaining `smoke_gunicorn.sh` defects not fixed by task 06 (`Cache-Control`/health not asserted, clears checkout `staticfiles/`, SQLite only, not run by `scripts/test.sh`).
- DEP-15/DEP-16: health endpoint blind to a stuck queue or missing Java/Nextflow; gunicorn logs not JSON.

Follow-ups raised while briefing:
- Steps can still read the worker's `/proc/<pid>/environ` (same UID) after task 03. Consider `prctl(PR_SET_DUMPABLE, 0)` in the worker so its environ is root-owned. Clearing `os.environ` is not enough, because `/proc/<pid>/environ` shows the original block. Ties into SEC-07 (from task 03).
- `admin_settings_update` on an unparseable `settings.yaml` rebuilds the file from defaults and drops `apps[]` (by design per QA C-02). Consider preserving the raw `apps:` block or refusing partial patches (from task 02).
- e2e harness: allow one test to boot a stack with custom env (e.g. low throttle rates), if it can't already (from task 07).
