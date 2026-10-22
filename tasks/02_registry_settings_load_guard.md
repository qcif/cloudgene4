# 02 — Stop a broken `settings.yaml` from uninstalling every workflow

## Overview

Cloudgene keeps the list of installed workflows in `settings.yaml` `apps[]`. The database only
holds a cache of that list (the `Workflow` rows), rebuilt by `registry.sync_all()`. A sync runs
lazily on the next `/api/` request after the file changes (`WorkflowSyncMiddleware`), on admin
writes, and from `manage.py sync_workflows`.

`load_settings()` is lenient by design: if the YAML does not parse, or a key has the wrong type,
it falls back to defaults instead of crashing, so the site stays up. For `apps`, the default is
`[]`. The sync then sees an empty app list and treats every registry-managed workflow as
removed. Rows with no jobs are deleted, and rows with jobs are marked `installed=false`,
`disabled`. A single stray tab or bad indent in a hand edit of `settings.yaml` therefore takes
every workflow off the site.

There is a second path to the same outcome. `update_settings()` (used by every registry write:
install, uninstall, access changes, group-delete pruning) starts from `default_settings()` when
the file does not parse, applies its change and writes the result. An admin who installs a
workflow while the file is broken therefore replaces the whole file, including every other
`apps[]` entry, with defaults plus that one app.

The intent of this task: when the app list could not be read reliably, the registry MUST NOT
act on it. It keeps the last good cache rows, refuses registry writes with a clear error, and
logs the reason. Once the file is fixed, the next request syncs as normal.

Source: spec/ISSUES.md WF-01 (BE-WREG-001, BE-WREG-010, major).

## Relevant spec

Read before starting:

- spec/constitution.md
- spec/backend/workflow-registry.md — sync (BE-WREG-008..013), lazy sync (BE-WREG-014..017),
  writes (BE-WREG-018..023), Behaviour "Settings-load failures", Known gaps.
- spec/backend/configuration.md — lenient load, `config_status()`, locked read-modify-write
  (`update_settings`).
- spec/backend/api-contract.md — error envelope and the error code tables.
- spec/backend/workflows-api.md — admin workflow operations that call the registry.
- spec/backend/management-commands.md — `sync_workflows`.
- spec/backend/logging.md — logger names (`cloudgene.workflows`).
- spec/backend/tests.md — test homes and the traceability table.

## Design

### When the app list is untrustworthy

Define one predicate in `core/config.py`, for example `apps_load_ok() -> bool` (name is up to
the implementer), computed from the last load:

| Load outcome | `apps` usable? |
|---|---|
| File parsed; no errors | yes |
| File parsed; errors only under other keys (e.g. `mail.port`) | yes |
| File parsed; errors under `apps[<i>]...` (one bad entry) | yes, since the scan already marks that entry invalid (BE-WREG-005) |
| File parsed; `apps` itself is not a list (error key exactly `apps`) | **no** |
| File did not parse (YAML error) | **no** |
| File unreadable (e.g. `PermissionError`) | **no** (today this raises out of `load_settings`; keep or convert, but the registry must not sync) |
| File missing | yes. A missing file is seeded from defaults (`_seed_settings`), which is a first-run case, not a broken edit. |

The predicate MUST use the same cached load result that `config_status()` reports, so the two
never disagree.

### Sync

`sync_all()` checks the predicate after loading settings and before scanning:

- When `apps` is untrustworthy, it MUST NOT write the DB: no upserts, no deletes, no
  `installed=false`. It raises a `RegistryError` with a new code (proposed: `settings_invalid`,
  status `409`) whose message names the problem, e.g.
  `settings.yaml could not be read; workflows were not synced: <first error>`.
- It MUST NOT update `_last_signature`, so the next request after the file is fixed (new
  mtime/size) syncs normally. While the file stays broken, `sync_if_changed()` will call
  `sync_all()` on each request. That is cheap because `load_settings()` is cached by stamp. Log the
  refusal at ERROR on `cloudgene.workflows` **once per settings stamp**, not once per request.

Callers:

| Caller | Behaviour while untrustworthy |
|---|---|
| `WorkflowSyncMiddleware` | Already logs and swallows. Must not log a stack trace per request for this expected error: catch `RegistryError` with this code quietly (the once-per-stamp log above is enough). |
| `list_apps()` (admin list) | Return the last statuses from this process if any. Otherwise, raise the error so `admin_workflows_list` returns 409 `settings_invalid`. Pick one, state it in the spec, and test it. Recommended: raise, so the admin sees why the list is wrong. |
| `admin_workflows_sync` | 409 `settings_invalid`. |
| `manage.py sync_workflows` | Print the error to stderr and exit non-zero. |
| Public `workflows_list` / `workflows_retrieve` | Unchanged: they read the existing cache rows, so users keep seeing the last good set. |

### Registry writes

`install`, `uninstall`, `update_access`, `set_nextflow_settings` (its `apps[]` part) and the
group-delete prune (BE-WREG-022) MUST refuse with the same 409 `settings_invalid` when the file
does not parse or `apps` is not a list. They MUST NOT write `settings.yaml`. Check inside the
`update_settings` callable (under the file lock) against the freshly read file, not the cache,
so a concurrent hand edit cannot slip in between.

The group-delete prune already must not block the delete (BE-WREG-022). It logs the refusal and
lets the delete continue.

Out of scope: the admin General settings save (`admin_settings_update`). It goes through
`update_settings` with a dict patch and today also rewrites a broken file from defaults, which
drops `apps[]`. This is a related risk but a separate decision; see Open questions.

### Interfaces

- New error code `settings_invalid` (409) on `admin_workflows_list`, `admin_workflows_sync`,
  `admin_workflows_install`, `admin_workflows_destroy` (uninstall),
  `admin_workflows_partial_update`/`update`, the Nextflow settings update operation, and
  `admin_groups_destroy` (logged only, not returned). Check exact `operationId`s in
  `schema.yaml`. The envelope shape is unchanged, so `schema.yaml` does not change (errors are
  `default: Error`). Run `python manage.py spectacular --file schema.yaml --validate` to
  confirm.
- Frontend: no code change is required, since the SPA already shows envelope messages. Check
  that Admin → Workflows shows the message, not a generic error. If it doesn't, fix it in this task.

## Steps

1. **Predicate** in `core/config.py`, recorded alongside the cached load errors. Distinguish
   "did not parse/read" and "`apps` not a list" from other errors.
2. **Sync guard** in `workflows/registry.py` `sync_all()`, plus the once-per-stamp log and the
   untouched `_last_signature`.
3. **Write guard** in the registry write functions (inside the `update_settings` callable).
4. **Callers**: middleware (quiet on this code), `admin_views` (map to 409), `sync_workflows`
   (non-zero exit).
5. **Unit tests**, in the existing homes named in spec/backend/tests.md:
   - `workflows/test_registry.py` (e.g. new `RegistrySettingsGuardTest`):
     - install two apps; corrupt `settings.yaml` (unparseable YAML) → `sync_all()` raises
       `settings_invalid`; both rows still exist, `installed=True`, status unchanged.
     - Same with `apps: "oops"` (not a list).
     - A bad unrelated key (`mail.port: abc`) still syncs normally.
     - One invalid `apps[]` entry still syncs the others (regression guard for BE-WREG-005).
     - After fixing the file, the next `sync_if_changed()` runs and syncs.
     - Refusal is logged once per settings stamp across repeated `sync_if_changed()` calls.
     - `install`/`uninstall`/`update_access` with a broken file raise `settings_invalid` and
       the file bytes are unchanged.
     - Deleting a group with a broken file still deletes the group, leaves the file unchanged,
       and logs.
     - Unreadable file (`chmod 000`, skip if running as root) → no DB writes.
   - `admin_panel/tests/test_api.py`: 409
     `settings_invalid` envelope from list, sync and install while broken.
   - `workflows/test_registry.py::CommandsTest` for `sync_workflows`: non-zero exit and stderr message while broken.
   - `core/tests/test_config.py`: the predicate for each row of the table above.
6. **E2E test** (Article 7.3): in `e2e/tests/test_admin_workflows.py`, with an installed public
   workflow, overwrite `settings.yaml` with invalid YAML, then check that the home page still
   lists the workflow and that Admin → Workflows shows the `settings_invalid` message. Restore
   the file, then check that the list recovers.
7. **Spec updates** (same change set):
   - spec/backend/workflow-registry.md: new requirement(s) (next free `BE-WREG-` IDs) for
     the sync guard and the write guard. Rewrite the "Settings-load failures" Behaviour
     paragraph. Remove the WF-01 Known gap row. Add Acceptance tests rows.
   - spec/backend/configuration.md: the predicate and its relationship to `config_status()`.
   - spec/backend/api-contract.md: add `settings_invalid` (409) to the view error-code table
     and the affected operations' "Notable errors" (marked as taken from code, per Article 5.3).
   - spec/backend/workflows-api.md, spec/backend/management-commands.md: the 409 and the
     non-zero exit.
   - spec/frontend/admin-workflows.md: only if the frontend changes.
   - spec/backend/tests.md: traceability rows and counts.
   - spec/ISSUES.md: drop WF-01.
8. Run the unit and e2e suites (`/tests` skill) and flake8.

## Acceptance criteria

- [ ] An unparseable `settings.yaml`, or one whose `apps` is not a list, never deletes,
      disables or uninstalls a `Workflow` row.
- [ ] Errors elsewhere in the file, or in a single `apps[]` entry, do not block the sync.
- [ ] Registry writes refuse with 409 `settings_invalid` and leave `settings.yaml` byte-for-byte
      unchanged while it is broken.
- [ ] Fixing the file restores normal syncing on the next `/api/` request without a restart.
- [ ] The refusal is logged at ERROR on `cloudgene.workflows` once per settings stamp.
- [ ] `sync_workflows` exits non-zero while the file is broken.
- [ ] `schema.yaml` is unchanged.
- [ ] Unit and e2e tests cover the above; suites pass; flake8 is clean.
- [ ] Spec files listed in step 7 are updated with new requirement IDs traced to tests.

## Open questions

Implement the stated default and copy the question into the relevant spec's Open questions.

- **Admin General settings save on a broken file.** `admin_settings_update` rebuilds a broken
  file from defaults plus the patch, which also drops `apps[]`. This is intended (QA_FINDINGS
  C-02: an admin can save a fix through the UI). Default: unchanged in this task. A follow-up
  could preserve the raw `apps:` block or refuse partial patches while the file does not parse.
- **Status code.** Default 409 `settings_invalid`. 503 is defensible too (a server-side
  configuration fault).
