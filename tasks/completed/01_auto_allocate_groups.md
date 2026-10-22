# 01 — Auto-allocate users to groups on activation

## Overview

Cloudgene grants access to non-public workflows through Django groups: an app in
`settings.yaml` `apps[]` lists the groups that may use it, and a user sees the workflow only if
they belong to one of those groups (spec/backend/access-control.md, BE-ACL-007). Today, putting
a user in a group is always a manual admin step (`admin_users_partial_update` with `groups`).
For a service used by whole institutions this is tedious: every new user from, say, the
University of Melbourne has to wait for an admin to add them to the `unimelb` group before they
can run the workflows meant for them.

This task lets the operator declare, in `settings.yaml`, a list of rules that map e-mail address
patterns (regular expressions) to group names. When a user activates their account by clicking
the e-mailed activation link, every rule whose pattern matches the user's e-mail address adds
the user to that rule's groups. Activation is the trigger because it is the moment Cloudgene
has proven that the user controls the address. Matching on an unverified address would let
anyone claim institutional access by typing someone else's domain into the registration form.

The feature is additive only. It never removes a user from a group, never touches the `admin`
group, and does not re-run when a user later changes their e-mail address.

## Relevant spec

Read before starting:

- spec/constitution.md
- spec/backend/accounts.md — registration and activation (BE-ACCT-008, 010, 011, 012),
  group name rule (BE-ACCT-002), Open questions.
- spec/backend/configuration.md — `settings.yaml` schema, `ListOf`, cross-field rules
  (BE-CONF-004, 008), committed defaults (BE-CONF-018).
- spec/backend/access-control.md — the `admin` group and its protection (BE-ACL-001, 002).
- spec/backend/workflow-registry.md — how `apps[].groups` names resolve to `Group` rows
  (BE-WREG-011, 018).
- spec/backend/logging.md — logger names and what reaches Admin → Logs.
- spec/backend/tests.md — test homes and the traceability table.
- docs/ADMIN_GUIDE.md — the `settings.yaml` key table (user-facing; update it).

## Design

### Configuration

A new top-level list key in `settings.yaml`, validated by `core/config.py` like `navbar` and
`apps`:

```yaml
auto_groups:
  - pattern: '.*@(.+\.)?unimelb\.edu\.au'
    groups: [unimelb]
  - pattern: '.*@example\.org'
    groups: [example, trial-users]
```

| Field | Type | Default | Rule |
|---|---|---|---|
| `auto_groups` | list of mappings | `[]` | |
| `auto_groups[i].pattern` | str, required | `''` | MUST compile as a Python regular expression; max 500 chars |
| `auto_groups[i].groups` | list of str, required | `[]` | each name MUST pass the group name rule (BE-ACCT-002); `admin` (any case) MUST be rejected |

Validation follows the existing fail-safe rules (BE-CONF-004): a bad value is recorded under its
dotted path (e.g. `auto_groups[1].pattern`) and made inert, never raising on load. Suggested
handling, mirroring `navbar[i].url` in BE-CONF-008:

- pattern that does not compile or is too long → error, pattern becomes `''`.
- `''` pattern → the rule never matches (it is not "match everything").
- invalid or `admin` group name → error on `auto_groups[i].groups`, that name is dropped; other
  names in the rule are kept.

A write through `update_settings` with any of these errors raises `ConfigError` as usual
(BE-CONF-011), so a future admin API cannot save a broken rule.

### Matching

- The pattern is matched with a **full match**, case-insensitive, against the stored
  (stripped, lower-cased) e-mail address. Full match is chosen over search so that
  `@unimelb\.edu\.au` cannot accidentally match `x@unimelb.edu.au.evil.com`; operators write
  `.*@domain` explicitly. Document this in docs/ADMIN_GUIDE.md with an example.
- Every matching rule applies; the result is the union of their groups. Rule order does not
  matter.
- Named groups that do not exist are created (as `install` does, BE-WREG-018). Note that
  `apps[].groups` links only existing groups at sync time (BE-WREG-011), so a newly created
  group grants workflow access only after the next registry sync; check whether creating a
  group should trigger a re-sync of apps that name it, and record the finding under Outcomes.
- Existing memberships are kept. Membership already held is not an error.

Pseudocode:

```
on first successful activation of user:
    rules = config.get('auto_groups')
    names = union of rule.groups for rule in rules
            if rule.pattern and fullmatch(rule.pattern, user.email, IGNORECASE)
    for name in names:
        group = get_or_create(name)
        user.groups.add(group)
    if names: log INFO "Auto-assigned <username> to groups <names>" on cloudgene.auth
```

Put this in one function (e.g. `accounts/groups.py::apply_auto_groups(user)` or similar) so the
trigger points and tests share it.

### When it runs

| Event | Allocation? | Why |
|---|---|---|
| First valid use of the activation link (`auth_activate_create` → `status: activated`) | yes | address proven |
| Later use of the same link (`already_active`) | no | not a new activation |
| Registration with `security.require_activation: false` | no | address not proven |
| Admin sets `is_active: true` via `admin_users_partial_update` | no | out of scope (see Open questions) |
| User changes e-mail via `me_partial_update` | no | address not proven; no re-evaluation |
| `create_admin` | no | |

Allocation MUST NOT make activation fail. If it raises (bad data, DB error), the activation
still succeeds with the normal 200, and the error is logged at ERROR on `cloudgene.auth` with
the username. Run allocation after the activation is saved, outside its transaction, or in a
savepoint, so a failure cannot roll back the activation.

### Interfaces

No HTTP interface changes: `ActivateResponse` is unchanged, so `schema.yaml` does not change
and the frontend is untouched. Confirm with
`python manage.py spectacular --file schema.yaml --validate` that the schema is unchanged.

Editing `auto_groups` from the admin UI is out of scope; operators edit `settings.yaml` by hand.
Any admin save keeps the key, because unknown-to-the-endpoint keys are preserved by
`update_settings` (BE-CONF-014).

### Security notes

- A pattern is admin-controlled input executed by Python `re`, which has no timeout. A
  catastrophic pattern could stall the activation request. Accept this risk (admin-only input,
  e-mail ≤ 254 chars) and cap pattern length; state it in the spec's Behaviour section.
- Rules MUST NOT be able to grant admin (the `admin` group is rejected at validation and skipped
  again at allocation time as defence in depth).

## Steps

1. **Config schema** — add `auto_groups` to `SCHEMA` in `core/config.py` with the per-item
   fields above and the cross-field checks (regex compiles, length cap, group names valid, no
   `admin`). Add `auto_groups: []` to the committed `home/config/settings.yaml` (BE-CONF-018).
2. **Allocation function** — implement the matching and group assignment described above.
3. **Trigger** — call it from `ActivateAccountView` on the `activated` path only.
4. **Unit tests** (backend, in the existing homes named in spec/backend/tests.md):
   - `core/tests/test_config.py` — `auto_groups` defaults to `[]`; a valid rule loads; an
     invalid regex, an over-long pattern, an invalid group name and `admin`/`Admin` each record
     an error under the right dotted path and are made inert while other rules keep working;
     `update_settings` with a bad rule raises `ConfigError` and leaves the file unchanged; the
     committed `settings.yaml` still validates and is complete.
   - `accounts/tests.py` (e.g. a new `AutoGroupsTest` class) — matching user is added to the
     group on activation; full match semantics (`x@unimelb.edu.au.evil.com` does not match
     `.*@unimelb\.edu\.au`); case-insensitive; several matching rules give the union; a
     non-matching user gets no groups; missing groups are created; existing memberships are
     kept; `already_active` re-use does not allocate (e.g. after an admin removed the group);
     registration with `require_activation: false` does not allocate; e-mail change via
     `me_partial_update` does not allocate; an `admin` name that bypassed validation is still
     skipped; an exception inside allocation still returns 200 `activated` and logs at ERROR;
     an INFO record is written on allocation.
5. **E2E test** (Article 7.3: activation is a browser flow that reaches the API) — in
   `e2e/tests/test_accounts.py`, register through the UI, set an `auto_groups` rule matching the
   test address, activate from the mailed link, and verify the user can see a workflow
   restricted to that group (or that `admin_users_retrieve` lists the group). The
   `ServerSettings` fixture in `e2e/conftest.py` only updates mapping sections; add a way to set
   a top-level list key.
6. **Spec updates** (same change set):
   - spec/backend/configuration.md — schema table row(s) for `auto_groups`, a new requirement
     for its validation (next free `BE-CONF-` ID), Acceptance tests rows.
   - spec/backend/accounts.md — new requirements (next free `BE-ACCT-` IDs) covering: when
     allocation runs and when it does not, full-match case-insensitive semantics, union of
     rules, additive only, group creation, `admin` never granted, failure does not block
     activation, INFO/ERROR logging. Add Behaviour text, Acceptance tests rows, and the ReDoS
     note. Add `configuration.md` `auto_groups` to Dependencies.
   - spec/backend/access-control.md — one line in Behaviour noting that group membership can
     also come from `auto_groups` at activation, linking to accounts.md.
   - spec/backend/tests.md — traceability rows and summary counts.
   - Any requirement whose test is not yet written is marked `(planned)` with a Known gap
     (Article 6.2).
7. **User docs** — add `auto_groups` to the settings table in docs/ADMIN_GUIDE.md with an
   example, the full-match rule, and the fact that it only applies on e-mail activation.
8. Run the unit and e2e suites (`/tests` skill) and flake8.

## Acceptance criteria

- [x] `auto_groups` is part of the `settings.yaml` schema, defaults to `[]`, and invalid rules are
      reported in `config_status()` without breaking load.
- [x] Activating an account by e-mail link adds the user to every group whose rule fully matches
      their e-mail address, creating missing groups.
- [x] No other event (re-activation, activation-free registration, admin activation, e-mail
      change) allocates groups.
- [x] The `admin` group can never be granted by a rule.
- [x] An allocation failure never fails activation.
- [x] `schema.yaml` is unchanged.
- [ ] Unit tests and one e2e test cover the above; the backend and e2e suites pass; flake8 is
      clean. (Backend passes; e2e written but NOT run, see Outcomes.)
- [x] spec/backend/configuration.md, accounts.md, access-control.md and tests.md are updated,
      with new requirement IDs traced to tests.
- [x] docs/ADMIN_GUIDE.md documents `auto_groups`.

## Open questions

Raise these with the user if they block the work; otherwise implement the default stated and
copy the question into the relevant spec's Open questions.

- **Admin activation.** An admin can activate a pending user with `is_active: true`; this does
  not set `activated_at` and does not verify the address. Default: no allocation. Should it
  allocate?
- **`require_activation: false`.** Default: rules never apply, because no address is verified.
  Should `config_status()` warn when `auto_groups` is non-empty while activation is off?
- **Existing users.** Rules are not applied retroactively. Is a management command to backfill
  existing active users wanted (separate task)?
- **Admin UI.** Should `auto_groups` be editable from Admin → Settings (separate frontend +
  admin API task, which would change `schema.yaml`)?

## Outcomes

- Implemented on branch `task-01-auto-groups`: `core/config.py` (schema + `_validate_auto_groups`),
  `accounts/groups.py::apply_auto_groups`, trigger in `ActivateAccountView`, unit tests
  (`AutoGroupsTest`, config tests), e2e test `test_a1b_activation_applies_auto_groups` plus
  `ServerSettings.set_key`, spec (BE-CONF-021, BE-ACCT-027..032, access-control, tests.md) and
  `docs/ADMIN_GUIDE.md`. `schema.yaml` is unchanged (verified with `spectacular --validate`).
- **E2E not run.** The project venv has no pytest/playwright and the `/tests` rules forbid
  installing them. The new e2e test is only compile-checked; run `scripts/test.sh e2e` before merge.
- **Re-sync finding.** `registry.sync_if_changed()` re-syncs only when `settings.yaml` or a
  `cloudgene.yaml` changes. Creating a group at activation does not, so a workflow that lists a
  newly created group becomes visible to its members only after the next sync. Not changed here
  (the brief asked only for a finding); recorded in the accounts.md Behaviour text and todo.md.
- **`home/config/settings.yaml` is git-ignored**, though BE-CONF-018 calls it "committed", so
  `auto_groups: []` was added to the local file only and is not in the commit. In a fresh
  worktree `CommittedHomeTest` needs that file copied in. Existing spec/code mismatch.
- Open questions copied into spec/backend/accounts.md Open questions.
- Flake8: the repo uses ~110-column lines; new code is clean at `--max-line-length=110`
  (remaining warnings are pre-existing lines).
- Plain `manage.py test` also tries to import `e2e.*` modules and errors without pytest; unit
  suites were run per app (`accounts admin_panel core jobs workflows`): 418 OK.
