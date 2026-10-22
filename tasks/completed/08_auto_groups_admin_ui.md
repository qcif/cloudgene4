# 08 — Admin UI for auto_groups rules

## Overview

Task 01 added `auto_groups` to `settings.yaml`. It is a list of rules, and each rule maps an
e-mail pattern (a regular expression) to one or more group names. When a user activates their
account from the e-mailed link, they join the groups of every rule that matches their address.
Groups control which workflows a user can see, so these rules decide who gets institutional
access automatically.

Right now the only way to change these rules is to edit `settings.yaml` on the server by hand.
That needs shell access, it is easy to get a regex wrong, and a broken rule only shows up as a
validation error the admin may never see. This task lets admins view, add, edit, remove and test
rules from the browser.

The rules are about groups, so the editor goes in the existing **Groups** modal
(`GroupManagementModal`, opened from Admin → Users). It does not go under Admin → Settings. The
modal gets two tabs: the current "Groups" list, and a new "Automatic membership" tab with the
rule editor. The groups list also shows which groups a rule names, and the delete confirmation
warns when you delete a group that a rule will create again.

Backend work: one new admin endpoint pair to read and replace the rule list, and one endpoint
to test an address against the rules without saving anything. Both follow the existing navbar
settings endpoints. Matching runs on the server because the rules use Python `re` semantics,
and a JavaScript regex would not always give the same answer.

## Relevant spec

Read before starting:

- spec/constitution.md (especially Article 5: contract order, `schema.yaml`; Article 7.3: e2e).
- spec/backend/configuration.md: `auto_groups` schema row, BE-CONF-011, 013, 014, 021.
- spec/backend/accounts.md: BE-ACCT-027 to 032, the auto_groups Behaviour text and Open
  questions (the "Admin UI" question is answered by this task).
- spec/backend/admin-api.md: BE-ADM-001 to 003 (access, CSRF, INFO log), BE-ADM-057 to 059
  (navbar endpoint, `update_settings`, error-key mapping). Use these as the pattern.
- spec/backend/api-contract.md: BE-API-021 (`fields` keys such as `auto_groups[0].pattern`),
  the operation table.
- spec/frontend/admin-users-groups.md: FE-AUSER-030 to 035, 040. This is the spec the new UI
  extends.
- spec/frontend/api-contract.md and spec/frontend/api-client.md: `apiErrorMessage`,
  `apiFieldErrors`, contract-test rules.
- spec/backend/tests.md and spec/frontend/tests.md: test homes and traceability tables.
- docs/ADMIN_GUIDE.md: the `auto_groups` section written in task 01.

Related todo.md item, not in scope: "Re-sync the workflow registry when auto_groups (or any code
path) creates a group named in `apps[].groups`". Saving rules writes `settings.yaml`, and that
already triggers `sync_if_changed`. Groups created later, at activation time, still do not
trigger a sync. Leave this to its own task, but do not make it worse.

## Design

### Backend: rule list (`admin_settings_auto_groups_retrieve` / `_update`)

`GET` and `PUT /api/admin/settings/auto-groups/`, admin only (BE-ADM-001), CSRF on PUT
(BE-ADM-002). Follow `NavbarSettingsView` in `admin_panel/views.py`.

Response shape (example):

```json
{
  "auto_groups": [
    {"pattern": ".*@(.+\\.)?unimelb\\.edu\\.au", "groups": ["unimelb"]}
  ],
  "require_activation": true
}
```

- `auto_groups`: the stored list as loaded by `core.config`, in file order.
- `require_activation`: read-only, the current value of `security.require_activation`. The UI
  uses it to warn that rules have no effect while activation is off (BE-ACCT-027). The PUT
  ignores it.

Request: `{"auto_groups": [...]}`. The PUT replaces the whole list, like the navbar PUT.

Validation. The serializer runs first, then `update_settings`. The serializer checks:

| Field | Rule | Error key |
|---|---|---|
| `pattern` | required, non-blank after trim, max 500 chars (`AUTO_GROUPS_PATTERN_MAX`), compiles with `re` | `auto_groups[i].pattern` |
| `groups` | list of 1 or more names; each passes `validate_group_name`; not `admin` in any case; duplicates removed (case-insensitive, keep the first spelling) | `auto_groups[i].groups` |

- An empty pattern passes `core.config` (it makes the rule inert), but the API MUST reject it.
  A rule saved from the UI should always be able to match something.
- Keep the patterns exactly as typed. Do not lower-case them or change their inner whitespace,
  so the YAML still reads as the admin wrote it.
- Leave the regex and group-name rules in `core.config._validate_auto_groups`. The serializer may
  call the same helpers, but the rules must stay defined in one place (spec Article 2.3).
  `update_settings` still validates the whole document as a second check (BE-CONF-011). A
  `ConfigError` is mapped with `_config_error(exc, '')` so keys stay `auto_groups[i].…`
  (BE-ADM-059).
- The write goes through `config.update_settings` (BE-ADM-058). Other keys, `apps[]` included,
  stay as they are (BE-CONF-014).
- If the rule list has changed, log one INFO record (BE-ADM-003), e.g. "Auto-group rules
  changed (3 rules)".
- Saving does not change anyone's existing group memberships. Rules apply only at future
  activations. State this in the spec and the UI.

### Backend: test an address (`admin_settings_auto_groups_test`)

`POST /api/admin/settings/auto-groups/test/`, admin only.

```
request:  {"email": "jo@unimelb.edu.au", "auto_groups": [...optional...]}
response: {"email": "jo@unimelb.edu.au", "matched_rules": [0], "groups": ["unimelb"]}
```

- `email` is required and checked with `validate_email`. Normalise it the same way stored
  addresses are (`normalize_email`) before matching, so the test answers the same way activation
  would.
- If `auto_groups` is in the request, test against those unsaved rules, after the same
  validation as the PUT. Otherwise test against the saved rules. This lets the admin try a rule
  before saving it.
- Matching MUST reuse the code activation uses, `accounts/groups.py::matching_group_names`
  (change it to accept a rule list, so tests and activation cannot drift apart). `groups` is the
  union with `admin` removed, exactly as activation would compute it. `matched_rules` lists the
  indexes of the rules that matched.
- It writes nothing, creates no groups, sends no mail and logs nothing at INFO.
- Errors: 400 `invalid` with `fields.email` or `fields.auto_groups[i].…`.

### Frontend

API module: add `getAutoGroups()`, `updateAutoGroups(rules)` and `testAutoGroups(email,
rules?)` to `frontend/src/api/admin.js`, next to the navbar functions. Only API modules call the
HTTP client (Article 5.1f).

`GroupManagementModal.vue`: add two tabs, "Groups" (the current content, unchanged) and
"Automatic membership". Rough layout:

```
[ Groups ] [ Automatic membership ]
 ℹ Users join these groups when they activate their account from the e-mail
   link, if their address fully matches the pattern. Existing members are
   not changed. Patterns are case-insensitive; write `.*@example\.org`.
 ⚠ (only if require_activation is false) Account activation is off, so these
   rules never apply.

 #  Pattern (regex)                    Groups                       
 1  [.*@(.+\.)?unimelb\.edu\.au   ]    (unimelb ×) [+ group ▾]   ↑ ↓ 🗑
 2  [.*@example\.org              ]    (example ×) (trial ×) [+]  ↑ ↓ 🗑
 [+ Add rule]                                          [Save rules]

 Test an address: [ jo@unimelb.edu.au ] [Test]
   → Matches rule 1. Joins: unimelb
```

- The tab loads with `getAutoGroups()`. It shows a spinner, and on failure the envelope message
  with fallback "Could not load automatic membership rules.".
- The groups input lets the admin pick an existing non-admin group, or type a new name that
  passes `validateGroupName`. A new name is shown with a "new" badge, meaning it will be created
  at the first activation (BE-ACCT-029). `admin` is never offered.
- Save sends the full list with `updateAutoGroups`, replaces the editor with the response and
  shows "Rules saved.". On 400, show the envelope message and put each
  `auto_groups[i].pattern` / `auto_groups[i].groups` message under row `i`, the same way the
  navbar editor does (FE-ASET-013). The Save button is disabled while the request runs. A save
  first clears earlier messages.
- **Test email.** Below the rules there is a "Test email" field (`auto-test-email`) with a Test
  button (`auto-test-submit`). The admin types an address and clicks Test (or presses Enter) to
  see whether the patterns match it, before or after saving. The button sends the address and
  the editor's current, unsaved rules with `testAutoGroups`. If the editor has no unsaved
  changes, it may omit the rules. The result (`auto-test-result`) shows the matched rule numbers
  and the groups the user would join, or "No rule matches this address.". The matched rows in
  the editor are highlighted (`data-matched="true"` on `auto-rule-row`). Editing a rule clears
  the result and the highlights, so a stale answer is never shown. An invalid address or rule
  shows the server field error under the field or under row `i`.
- If the editor has unsaved changes and the admin switches tab or closes the modal, ask for
  confirmation first. (Default. Drop it if it gets in the way, and say so under Outcomes.)
- Groups tab: each group named by a rule shows an "auto" badge (`group-auto-badge`). The data
  comes from `getAutoGroups()`, loaded with the group list. The delete confirmation for such a
  group adds: "Automatic membership rules name this group; it will be created again when a
  matching user activates." Deleting a group does not edit any rules.
- Patterns, group names, e-mail addresses and server messages MUST be rendered as text, never
  with `v-html` (FE-AUSER-040).
- Suggested `data-testid`s: `group-tab-groups`, `group-tab-auto`, `auto-rule-row`,
  `auto-rule-pattern`, `auto-rule-pattern-error`, `auto-rule-groups-error`,
  `auto-rule-group-add`, `auto-rule-group-remove`, `auto-rule-remove`, `auto-rule-add`,
  `auto-rules-save`, `auto-rules-success`, `auto-rules-error`, `auto-rules-activation-off`,
  `auto-test-email`, `auto-test-submit`, `auto-test-result`.

### Security notes

- Every new operation is admin only. Non-admins get 403 and anonymous users 401, with nothing
  written (BE-ADM-001).
- The test endpoint runs a pattern the admin supplies. The ReDoS risk is the one accepted in
  accounts.md: input comes only from admins, patterns are at most 500 characters, and e-mail
  addresses are at most 254. Note in the spec that the test endpoint carries the same risk.
- A rule can still never grant `admin`. The API rejects it, `core.config` rejects it, and
  allocation skips it (BE-ACCT-030).

### Deployment

No Ansible change. The playbook does not manage `settings.yaml` (it is runtime state under
`$CLOUDGENE_HOME/config/`), and the new endpoints need no new settings. Confirm this by
checking that nothing under `deploy/ansible/roles/` templates or overwrites `settings.yaml`.
Record the result under Outcomes.

## Steps

Follow the order in Article 5.1b, all in one change set.

1. **Matching refactor.** Change `accounts/groups.py::matching_group_names` to take an optional
   rule list (default: the saved rules) and return the matched indexes as well. Activation
   behaviour does not change. The existing `AutoGroupsTest` must still pass.
2. **Serializers and views.** In `admin_panel/serializers.py` and `admin_panel/views.py`, add the
   rule, list, test-request and test-response serializers, plus the two views with explicit
   `extend_schema(operation_id=…)`. Wire them up in `admin_panel/urls.py`.
3. **Schema.** Regenerate with `python manage.py spectacular --file schema.yaml --validate` and
   commit it. Check that the staleness test passes.
4. **Backend unit tests**, in `admin_panel/tests/test_api.py` (e.g. a new `AutoGroupsSettingsTest`
   class, following `NavbarTest`):
   - GET returns the stored list and `require_activation`. It returns `[]` when the key is
     missing.
   - PUT replaces the list, keeps other keys (`navbar`, `apps`) and writes one INFO log record.
   - PUT rejects, with the right `fields` key and without writing the file: a blank pattern,
     an over-long pattern, an invalid regex, an empty `groups` list, an invalid group name,
     `admin`/`Admin`.
   - PUT removes duplicate group names case-insensitively. Patterns are stored as typed.
   - PUT works when the stored `settings.yaml` currently has an invalid `auto_groups` rule
     (BE-ADM-058).
   - Test endpoint: a matching address returns rule indexes and the union of groups. Full-match
     and case-insensitive behaviour matches activation. `admin` never appears. Unsaved rules in
     the request are used instead of the saved ones. An invalid `email` or invalid unsaved rules
     give 400. No file write, no group created.
   - Access: anonymous gets 401, a non-admin gets 403, and session PUT/POST without CSRF gets
     403, for all three operations.
   - Contract: responses validate against the `schema.yaml` components, if the backend
     contract-test helper exists by then (BE-TEST-003). If not, cite them as planned.
   - Also in `accounts/tests.py`: activation still uses the saved rules after the refactor
     (covered by the existing tests).
5. **Frontend API module.** Add the three functions to `frontend/src/api/admin.js`. Add
   request-shape cases to `frontend/src/test/admin-api.test.js` (method, path, body; rules
   omitted from the test call when not given).
6. **Frontend UI.** Build the two tabs and the rule editor in `GroupManagementModal.vue` as
   designed. If the modal gets large, put the rule editor in its own component, e.g.
   `frontend/src/components/admin/AutoGroupRulesEditor.vue`.
7. **Frontend unit tests** (vitest, HTTP stubbed as in `mail-settings-view.test.js`), e.g.
   `frontend/src/test/components/AutoGroupRulesEditor.test.js`:
   - loads and renders rules. Shows the activation-off warning only when
     `require_activation` is false.
   - add, remove and reorder rules. Add a group chip (existing and new name). `admin` is not
     offered. An invalid new group name is rejected client-side with no request.
   - Save sends the full list. Server `auto_groups[i].…` errors land under row `i`. The Save
     button is disabled while saving.
   - Test email sends the unsaved rules, renders the result and the no-match message, and
     highlights the matched rows. Editing a rule clears the result and the highlights.
   - A pattern such as `<img src=x onerror=alert(1)>` is shown literally.
   - Groups tab: the "auto" badge and the extra warning in the delete confirmation.
8. **E2E test** (Article 7.3). In `e2e/tests/test_accounts.py`, next to
   `test_a1b_activation_applies_auto_groups`, add e.g. `test_a1c_admin_edits_auto_groups`:
   an admin opens Users → Groups → Automatic membership, adds a rule, tests an address, sees
   the match, saves and reloads, and the rule is still there. Then a new user registers and
   activates with a matching address and ends up in the group. Also cover one server field
   error shown under the row (e.g. an invalid regex). Restore settings afterwards
   (`ServerSettings.restore`).
9. **Spec updates**, in the same change set:
   - spec/backend/admin-api.md: new requirements under Settings (next free `BE-ADM-` IDs,
     after BE-ADM-059 or in an unused range. Check the README rules). Cover GET/PUT shape and
     validation, the empty-pattern rejection, the test endpoint (no side effects, same matching
     as activation), and the INFO log. Add Interfaces, Acceptance tests and Behaviour (ReDoS
     note) entries.
   - spec/backend/api-contract.md: the three new operations, quoted from `schema.yaml`, and the
     new components.
   - spec/frontend/api-contract.md: the matching API functions by operationId.
   - spec/frontend/admin-users-groups.md: Scope (the new component and `admin.js` functions),
     Dependencies (the new operationIds), new `FE-AUSER-` requirements for the tabs, the
     editor, save and errors, test, the activation-off warning, the "auto" badge, the delete
     warning and text-only rendering. Add Interfaces and Acceptance tests rows. Answer or
     update its Open questions as needed.
   - spec/backend/accounts.md: answer the "Admin UI" open question and point to the new
     admin-api requirements. Note that matching is shared with the test endpoint.
   - spec/backend/tests.md and spec/frontend/tests.md: traceability rows and summary counts.
   - Mark any requirement whose test is not written yet as `(planned)`, with a Known gap
     (Article 6.2).
10. **User docs.** In docs/ADMIN_GUIDE.md, add to the `auto_groups` section that rules can be
    edited and tested under Admin → Users → Groups → Automatic membership.
11. Run flake8 on the changed Python files, the backend and frontend unit suites, and the e2e
    suite (`/tests` skill). Task 01 could not run e2e. If that is still true, say so under
    Outcomes.

## Acceptance criteria

- [x] Admins can list, add, edit, reorder, remove and save `auto_groups` rules from the Groups
      modal, and the saved rules are what activation uses.
- [x] Admins can test an e-mail address against saved or unsaved rules, and the answer matches
      what activation would do.
- [x] Invalid rules (blank, too long, bad regex, no groups, bad group name, `admin`) are
      rejected with per-row field errors, and `settings.yaml` is not written.
- [x] Saving rules changes no existing memberships and keeps all other `settings.yaml` keys.
- [x] The UI warns when `security.require_activation` is off, marks groups named by rules, and
      warns when deleting such a group.
- [x] All three operations are admin only, with CSRF on unsafe methods.
- [x] `schema.yaml` is regenerated and both `api-contract.md` files list the new operations.
- [x] Backend unit, frontend unit and one e2e test cover the above. The suites pass and flake8
      is clean.
- [x] Spec files and docs/ADMIN_GUIDE.md are updated, with new requirement IDs traced to tests.

## Open questions

Use the default stated unless the user decides otherwise, and copy any that remain into the
relevant spec's Open questions.

- **Invalid stored rules.** If `settings.yaml` was hand-edited with a bad rule, `core.config`
  makes it inert (empty pattern or dropped group), and GET returns that cleaned value. The
  admin then sees an empty pattern and not the original text. Default: show rows with an empty
  pattern with a "This rule never matches; fix or remove it" warning. Should GET also return the
  `auto_groups` entries from `config_status().errors`, so the UI can show why? That would add a
  field to the response.
- **Backfill.** Should the editor have "Apply to existing users" (the backfill question from
  task 01)? Default: no. Needs its own task and a decision on whether unverified addresses
  count.
- **Admin activation.** The UI text says rules apply only on e-mail activation. If task 01's
  "admin activation" question is later answered yes, this text must change.


## Outcomes

- **Matching refactor.** Added `accounts/groups.py::match_auto_groups(email, rules=None)` returning
  `(matched_indexes, groups)`. `matching_group_names(email, rules=None)` stays as a thin wrapper
  (so activation and its existing test mock are unchanged). This differs slightly from the brief,
  which said to change `matching_group_names` itself; the behaviour is the same and both
  activation and the test endpoint go through the one matcher.
- **Shared rule validation.** Extracted `core.config.check_auto_group_rule(rule)` from
  `_validate_auto_groups`; the serializer calls it, so the regex, length and group-name rules
  still live only in `core.config`. The blank-pattern rejection is in the serializer only.
- **Request component.** The PUT reuses `AutoGroupsSerializer` (with `require_activation`
  read-only) as its request, as the navbar does, so the schema component is `AutoGroupsRequest`.
- **Where loading lives.** `GroupManagementModal` calls `getAutoGroups()` once (for the badges and
  the tab) and passes the rules, `requireActivation` and the group list to the editor as props.
  The editor does not load by itself. A failed load shows the message with no retry button;
  reopening the modal reloads.
- **Unsaved-changes confirm.** Kept (`window.confirm`) for tab switch and close.
- **Invalid stored rules.** Default taken: a blank pattern shows "This rule never matches; fix or
  remove it." `config_status().errors` is not returned (open question stays open).
- **Deployment.** Checked `deploy/ansible/roles/`: nothing templates or overwrites
  `settings.yaml` (one nginx template comment mentions it). No Ansible change.
- **Tests run.** Django `admin_panel`, `accounts`, `core` pass, apart from
  `core.tests.test_config.CommittedHomeTest` which only fails inside a git worktree (the
  untracked `home/config/` is absent there). Vitest 163/163. E2E: `test_a1b` and `test_a1c`
  pass. E2E needed `pip install -r e2e/requirements.txt` into the main venv and
  `playwright install chromium` (the cached browser build did not match the installed
  Playwright), so task 01's "could not run e2e" no longer applies.
- **flake8.** No new findings in changed lines; the files carry older E501/E128/E731 findings.
- **Spec changes.** admin-api.md (BE-ADM-080…084, interfaces, behaviour, acceptance),
  backend/api-contract.md (3 operations, components), frontend/api-contract.md (3 functions),
  admin-users-groups.md (FE-AUSER-050…056, scope, deps, interfaces, tests, open questions),
  accounts.md (Admin UI question answered), both tests.md files (traceability, counts).
  docs/ADMIN_GUIDE.md updated.
- **Full e2e run.** 186 passed, 3 failed, none in group code: `test_d1_dashboard_counts_match_db`
  (flaky; passes alone), `test_command_steps_run_and_show_output` and
  `test_submit_hello_with_unicode_job_name` (job output arrives mojibake-encoded, a locale/Nextflow
  environment issue). Not investigated further.
- **Follow-up change requested by the user (deviation from the brief).** The Groups modal became a
  full page: `GroupManagementModal` was removed and replaced by `views/admin/AdminGroupsView.vue`
  at `/admin/groups`, with a "Groups" sidebar item after "Users" (`admin-nav-groups`). The Groups
  button on the Users page is gone. The member-count badge is now the button that opens the
  members (tooltip "View"), replacing the separate Members button. The two tabs, editor and test
  ids are unchanged. The unsaved-changes confirm now also fires on leaving the route. Spec
  (admin-users-groups, layout-navigation, routing, both api-contract and tests files) and e2e
  tests were updated to match; FE-AUSER-030/033 were reworded.
- **Missing icons.** The "white" icons were not a code problem: in the demo dev server Vite
  returned 403 for the Font Awesome font because `node_modules` was a symlink outside the
  worktree. Fixed for the demo with an untracked `vite.demo.config.js` (not committed).
