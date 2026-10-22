# 04 — Harden the systemd sandbox: read-only code, private files, no loopback trust

## Overview

The web, worker and cleanup services run as the `cloudgene` user under a systemd sandbox
(`ProtectSystem=strict`, `ReadWritePaths=`, `PrivateTmp`, `NoNewPrivileges`). Three weaknesses
in that sandbox matter because the worker runs third-party workflow code as the same user:

1. **The code is writable.** Every unit lists the checkout `/opt/cloudgene` in
   `ReadWritePaths=`, and the Ansible deployment clones, builds and `pip install`s it *as*
   `cloudgene`. A workflow step (or a compromised web process) can therefore edit Python files,
   the virtualenv or the built SPA. The change survives restarts and runs as the web app.
2. **New files are world-readable.** No unit sets `UMask=`, and `write_text_atomic()` creates new
   files `0644`. A fresh `settings.yaml` (which holds `mail.password` in plain text), per-app
   `nextflow.env` files, job workspaces, uploads and outputs are readable by every local
   user. No deploy check warns about it.
3. **Workflow steps can impersonate nginx.** gunicorn listens on `127.0.0.1:8000` and trusts
   `X-Forwarded-*` from `127.0.0.1`. A step can connect to that port directly and forge the
   client address. This defeats per-IP throttling (task 07) and poisons logs.

There are also smaller unit problems that sit in the same files: `ReadWritePaths` is
hard-coded, so a different `CLOUDGENE_HOME` or a local `work_dir` outside it silently becomes
read-only; and the units order only `After=network.target`, which is too early for a remote
PostgreSQL.

The intent: after this task, nothing the services run can modify application code, and
nothing they create is readable by other users. Only nginx can reach the gunicorn listener, and
a misconfigured path fails loudly at start-up instead of failing jobs later.

Source: spec/ISSUES.md SEC-02, SEC-03, SEC-17, DEP-12 (DEP-PROC-009, DEP-SEC-023, DEP-RT-015,
DEP-RT-006, DEP-PROC-006, BE-CONF-015, DEP-HOME-003, DEP-HOME-008, DEP-SEC-022, DEP-RT-020,
DEP-HOME-004, DEP-ARCH-021, DEP-PROC-008).

## Relevant spec

Read before starting:

- spec/constitution.md
- spec/deployment/process-management.md — common unit options (DEP-PROC-001..009), per-unit
  sections, Known gaps.
- spec/deployment/security-hardening.md — DEP-SEC-020..026.
- spec/deployment/cloudgene-home.md — layout and modes (DEP-HOME-003, -004, -008, -009).
- spec/deployment/workflow-runtime.md — `NXF_HOME` (DEP-RT-006), DEP-RT-014/015, loopback
  reachability (DEP-RT-020).
- spec/deployment/web-server.md and spec/deployment/reverse-proxy.md — gunicorn bind,
  `forwarded_allow_ips`, the nginx upstream.
- spec/deployment/overview.md — DEP-ARCH-020/021 (paths and the service user's home).
- spec/deployment/install-upgrade.md — install and upgrade procedure (who owns the checkout,
  who builds).
- spec/backend/configuration.md — BE-CONF-015 (settings file mode).
- spec/deployment/tests.md — the planned config-test home `core/tests/test_deploy_files.py`
  (`SystemdUnitsTest`, `GunicornConfigTest`, `NginxExampleTest`).
- deploy/ansible/ — roles `common`, `cloudgene`, `runtime`, `nginx`. The live deployment uses
  these, so they change in the same task.

## Design

### A. Read-only checkout

- Remove `/opt/cloudgene` from `ReadWritePaths=` in all three service units. Writable paths
  become `CLOUDGENE_HOME` (`/var/lib/cloudgene`) only, plus whatever an operator adds for
  local Nextflow work directories (DEP-PROC-006).
- The checkout, virtualenv and build outputs (`static/frontend`, `staticfiles/`) are owned by
  `root` and read-only for `cloudgene`. Ansible changes:
  - `common`: create `/opt/cloudgene` as `root:root 0755`.
  - `cloudgene`: run `git`, `pip`, `npm ci && npm run build` and `collectstatic` as root, not
    `become_user: cloudgene`. `migrate`, `create_admin`, `check --deploy` and
    `ensure_workflow` stay as `cloudgene`. The `cloudgene-manage` wrapper works for root
    because the env file is `root:cloudgene 0640`.
  - One-off migration for the existing host: `chown -R root:root /opt/cloudgene`. Make it an
    idempotent task that runs before the checkout task.
- `NXF_HOME`: the Ansible host already sets the service user's home to `CLOUDGENE_HOME`, so
  Nextflow uses `/var/lib/cloudgene/.nextflow`. Make this the documented default for every
  install: the worker sets `NXF_HOME=$CLOUDGENE_HOME/.nextflow` in the step environment
  unless an env file sets it (a new, explicit step in BE-RUN-017, after env files). The `runtime`
  role's pre-download uses the same path. This replaces DEP-ARCH-021's "home inside
  `/opt/cloudgene`" rule. Task 03 strips `CLOUDGENE_HOME` from the step environment, so the
  value must be computed in code, not written as `$CLOUDGENE_HOME` in `nextflow.env`.
- Default SQLite path: `DATABASE_URL` unset falls back to `BASE_DIR/db.sqlite3`, inside the
  checkout. Do not move the development default. Instead, `check --deploy` MUST warn when the
  SQLite database file is inside `BASE_DIR` (new deploy check, next free `cloudgene.W0xx` ID).
- Remove `/opt/cloudgene/.nextflow` from consideration: add `.nextflow/` to `.gitignore` in case
  of old dev runs, and document that it is unused in production.

### B. Private files

- Add `UMask=0027` to all three service units (DEP-HOME-003). Group-readable is kept so an
  operator in the `cloudgene` group can inspect jobs; others get nothing.
- `write_text_atomic()` creates new files `0600` instead of `0644`. An existing file's mode is
  preserved, as today (BE-CONF-015, DEP-HOME-009). Every new file under `config/` and
  `apps/<id>/` is then private no matter which process creates it.
- Ansible seeds `config/nextflow.env` and `config/nextflow.config` with `0600`, and any seeded
  `settings.yaml` with `0600` (DEP-HOME-008).
- Deploy check (DEP-SEC-022, planned): `check --deploy` warns when `config/secret_key`,
  `config/settings.yaml` or any `nextflow.env` under `CLOUDGENE_HOME` is readable by group or
  others, and when `CLOUDGENE_HOME` itself is accessible to others. Use the next free
  `cloudgene.W0xx` IDs. The Ansible play already runs `check --deploy --fail-level WARNING`, so
  a bad mode fails the deploy.

### C. gunicorn reachable only by nginx

Steps run as `cloudgene`, the same UID as gunicorn, so file permissions on a socket that
gunicorn creates do not help, and a UID-based firewall rule cannot tell steps apart from the web
app. Use systemd socket activation so the socket is created and owned by systemd:

- New unit `deploy/systemd/cloudgene-web.socket`: `ListenStream=/run/cloudgene/web.sock`,
  `SocketUser=root`, `SocketGroup=www-data`, `SocketMode=0660`. Only root and nginx
  (`www-data`) can connect; `cloudgene` cannot.
- `cloudgene-web.service` gains `Requires=`/`After=cloudgene-web.socket`. gunicorn picks up the
  inherited socket (it supports `LISTEN_FDS`). Confirm the gunicorn version in
  `requirements.txt` supports this, and that `GUNICORN_BIND` is ignored or unset in that mode.
- nginx proxies to `unix:/run/cloudgene/web.sock` (both `deploy/nginx.conf.example` and the
  Ansible template).
- `forwarded_allow_ips`: check how the pinned gunicorn treats UNIX-socket peers. The effective
  result MUST be that `X-Forwarded-For`/`-Proto` from nginx are honoured over the socket and
  that no TCP listener trusts them. Remove the `127.0.0.1` TCP default from the production
  path. Keep `127.0.0.1:8000` available for development and the smoke script when no socket is
  inherited.
- Health probes and the smoke script that `curl 127.0.0.1:8000` switch to
  `curl --unix-socket` in production docs. The smoke script may keep TCP.

### D. Unit robustness (DEP-12)

- `After=network-online.target postgresql.service` and `Wants=network-online.target` on all
  units that need the database (DEP-PROC-008).
- `ReadWritePaths` stays a literal path (systemd cannot read `CLOUDGENE_HOME` from the env
  file). Instead, fail loudly: at start-up the worker MUST check that `CLOUDGENE_HOME`, the
  jobs directory and every **local** configured work directory (`nextflow.work_dir`,
  `apps[].work_dir`; remote URIs such as `az://` are skipped) are writable. It logs ERROR naming
  the path and the `ReadWritePaths=` fix for each one that is not. It does not exit, so jobs
  for other apps keep running. The same check runs in `check --deploy` as a warning.
- `ProtectHome=true` stays. Document that `CLOUDGENE_HOME`, `NXF_HOME` and app directories must
  not be under `/home`.

### Interfaces

- No HTTP change; `schema.yaml` is unchanged.
- New unit file `cloudgene-web.socket`; changed nginx upstream; new deploy check IDs; new
  default `NXF_HOME` in the step environment; `write_text_atomic` default mode `0600`.

## Steps

1. **Units** (`deploy/systemd/`): drop `/opt/cloudgene` from `ReadWritePaths`, add `UMask=0027`,
   network-online ordering, and the socket unit with its web-service wiring.
2. **gunicorn/nginx**: socket activation in `deploy/gunicorn.conf.py` (only if config is
   needed), `deploy/nginx.conf.example` upstream.
3. **Code**: `write_text_atomic` mode; `NXF_HOME` default in `jobs/runner.py` `build_env`;
   worker start-up writable-path check; new deploy checks in the module behind
   `check --deploy` (see `core/tests/test_deploy.py` for where existing checks live).
4. **Ansible**: root-owned checkout and builds, chown migration, `0600` seeds, socket unit in
   the unit list (enable `cloudgene-web.socket`), nginx template upstream, `runtime` role
   `NXF_HOME`. Run `ansible-playbook --check --diff` against the host before a real run, and
   ask the user before deploying.
5. **Unit tests**:
   - `core/tests/test_deploy_files.py` (planned home; create it with the classes named in
     spec/deployment/tests.md as needed): `SystemdUnitsTest`. No unit lists `/opt/cloudgene` in
     `ReadWritePaths`; every service unit sets `UMask=0027` and orders after
     `network-online.target`; the web service requires the socket; the socket is `0660`
     `root:www-data`. `NginxExampleTest`: upstream is the UNIX socket.
   - `core/tests/test_config.py`: a new file written by `write_text_atomic` is `0600`; an
     existing `0640` file keeps `0640`.
   - `core/tests/test_deploy.py`: each new deploy check warns on the bad case and is silent on
     the good one (world-readable `settings.yaml`, `secret_key`, `nextflow.env`; SQLite inside
     `BASE_DIR`; unwritable work dir).
   - `jobs/tests/test_runner.py`: `NXF_HOME` defaults to `$CLOUDGENE_HOME/.nextflow`, and an
     env-file value wins.
   - `jobs/tests/test_worker.py`: start-up check logs ERROR for an unwritable local work dir
     and ignores a remote URI.
6. **Smoke**: run `scripts/smoke_gunicorn.sh` to confirm TCP mode still boots. If feasible,
   add a step that boots with an inherited socket (e.g. `systemd-socket-activate`) and sends one
   request through it.
7. **Spec updates** (same change set):
   - spec/deployment/process-management.md: DEP-PROC-009 now met (remove gap); new
     requirements for `UMask`, network-online ordering, the socket unit, and the worker's
     writable-path check; update the unit listings.
   - spec/deployment/overview.md: rewrite DEP-ARCH-021 (service home = `CLOUDGENE_HOME`;
     `NXF_HOME` default).
   - spec/deployment/workflow-runtime.md: DEP-RT-006 default `NXF_HOME`; DEP-RT-020 (gunicorn
     no longer reachable from steps; PostgreSQL still is); remove gaps.
   - spec/deployment/cloudgene-home.md, security-hardening.md, web-server.md,
     reverse-proxy.md, install-upgrade.md: modes, deploy checks, socket upstream, root-owned
     checkout and build order.
   - spec/backend/configuration.md: BE-CONF-015 loses `(planned)`.
   - spec/backend/job-runner.md: BE-RUN-017 adds the `NXF_HOME` default step.
   - spec/deployment/tests.md and spec/backend/tests.md: traceability rows and counts.
   - spec/ISSUES.md: drop SEC-02, SEC-03, SEC-17, DEP-12 and the `NXF_HOME` open question.
8. **User docs**: `docs/DEPLOYMENT.md` install steps (clone and build as root; socket unit;
   nginx upstream; health probe via `--unix-socket`; `ReadWritePaths` for local work dirs).
9. Run the unit and e2e suites (`/tests` skill), the smoke script, and flake8.

## Acceptance criteria

- [ ] No unit can write the checkout; on the deployed host `/opt/cloudgene` is root-owned and a
      `sudo -u cloudgene touch /opt/cloudgene/x` fails.
- [ ] All service units set `UMask=0027`; new files written by Cloudgene are `0600`;
      `check --deploy` warns on group/other-readable secret files.
- [ ] gunicorn in production listens only on a systemd-owned UNIX socket that `cloudgene`
      cannot connect to; nginx proxies through it; client IPs in logs are real.
- [ ] `NXF_HOME` defaults to `$CLOUDGENE_HOME/.nextflow` and Nextflow jobs run on the deployed
      host after the change.
- [ ] An unwritable local work dir is reported at worker start-up and by `check --deploy`.
- [ ] `schema.yaml` is unchanged.
- [ ] Unit and config tests cover the above; suites pass; flake8 is clean.
- [ ] Spec and docs updated as in steps 7–8.

## Open questions

Implement the stated default and copy the question into the relevant spec's Open questions.

- **Build as root?** Default: yes. `npm ci` as root runs package install scripts as root.
  The alternative is a separate unprivileged `cloudgene-build` user that owns the checkout,
  distinct from the service user. Raise this with the user if `npm ci` warnings or failures
  appear.
- **`UMask=0027` vs `0077`.** Default `0027`, so admins in the `cloudgene` group can read job
  data.
- **PostgreSQL on loopback.** Steps can still reach PostgreSQL on `127.0.0.1:5432`. Once task 03
  removes the password from their environment, they need a password to connect. Restricting
  this further (`pg_hba` by UID is not possible over TCP) is out of scope.
