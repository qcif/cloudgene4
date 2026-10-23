# Admin users and groups

## Purpose

Lets administrators find user accounts, change their group memberships, activate or deactivate
them, grant or remove admin rights, and delete them; and manage the groups that gate workflow
access (create, delete, see and remove members). The views send only the changes the admin made;
all permission and self-protection rules are enforced by the backend and mirrored in the UI only
to avoid offering actions that would fail.

## Scope

Covered:

- `frontend/src/views/admin/AdminUsersView.vue` (route `/admin/users`)
- `frontend/src/views/admin/AdminGroupsView.vue` (route `/admin/groups`)
- `frontend/src/components/admin/GroupMembersModal.vue`
- `frontend/src/components/admin/AutoGroupRulesEditor.vue` (the "Automatic membership" tab)
- Admin functions of `frontend/src/api/admin.js`: `getAutoGroups`, `updateAutoGroups`,
  `testAutoGroups`.
- Admin functions of `frontend/src/api/users.js`: `listUsers`, `getUser`, `updateUser`,
  `deleteUser`, `listGroups`, `createGroup`, `deleteGroup`.
- Client-side group-name check `validateGroupName` as used by the group modal (the rule itself
  is specified in [auth-views.md](auth-views.md) / [../backend/accounts.md](../backend/accounts.md)).

Out of scope:

- Profile functions of `users.js` (`getProfile`, `updateProfile`, …) — [profile.md](profile.md).
- Avatar helpers (`utils/avatar.js`) — [common-components.md](common-components.md).
- Route guards — [routing.md](routing.md). Server rules — [../backend/admin-api.md](../backend/admin-api.md).
- Group access per workflow — [admin-workflows.md](admin-workflows.md).

## Dependencies

- [../backend/admin-api.md](../backend/admin-api.md) — BE-ADM-020…027 (users), BE-ADM-030…032
  (groups), BE-ADM-080…084 (auto-group rules).
- [../backend/accounts.md](../backend/accounts.md) — K1 uniqueness (no duplicate users), group-name rule.
- [api-client.md](api-client.md) — `apiErrorMessage`, `apiFieldErrors`.
- [state-stores.md](state-stores.md) — `auth.user.id` to detect the admin's own row.
- Contract operations: `admin_users_list`, `admin_users_retrieve`, `admin_users_partial_update`,
  `admin_users_destroy`, `admin_groups_list`, `admin_groups_create`, `admin_groups_destroy`,
  `admin_settings_auto_groups_retrieve`, `admin_settings_auto_groups_update`,
  `admin_settings_auto_groups_test`.

## Requirements

### Access

- **FE-AUSER-001** `/admin/users` MUST be reachable only by a signed-in admin; a signed-in
  non-admin MUST land on `/` without the users table being rendered, an anonymous visitor on
  `/login?next=/admin/users`.

### User list

- **FE-AUSER-010** On mount the view MUST call `listUsers({page: 1, page_size: 20})`
  (`admin_users_list`) and `listGroups()` (`admin_groups_list`), showing a spinner until the
  user list arrives. The heading MUST show the server `count` (`admin-users-count`).
- **FE-AUSER-011** Search (`admin-users-search`, submit or Enter) MUST re-fetch page 1 with the
  trimmed `search` term; an empty term MUST be omitted. Paging MUST keep the current term.
- **FE-AUSER-012** Each fetch MUST replace the displayed rows with exactly the `results` of that
  response, keyed by `user.id`; rows MUST NOT be appended or merged across pages or searches,
  and the total MUST come from `count`, never from the number of rows held client-side. (Guards
  against re-introducing the duplicate-users symptom client-side.)
- **FE-AUSER-013** Each row (`admin-user-row`, `data-username`) MUST show the initials avatar,
  username, full name, e-mail, active/inactive badge (`admin-user-status`, `data-state`), an
  `admin` badge when `is_admin`, join date and last login ("–" when null), and the user's group
  chips excluding `admin`. An empty result MUST show "No users found." (`admin-users-empty`).
- **FE-AUSER-014** A load failure MUST show the envelope message (fallback "Could not load
  users." / "Could not load groups.") in `admin-users-error`.

### User actions

- **FE-AUSER-020** Adding a group (`admin-user-group-add`, only listing existing non-admin
  groups the user is not in) and removing a chip (`admin-user-group-remove`) MUST call
  `updateUser(id, {groups: [...]})` with the complete new list of non-admin group names. The
  `admin` group MUST NOT be sent or offered as a chip.
- **FE-AUSER-021** Activate/Deactivate (`admin-user-toggle-active`) MUST send only
  `{is_active: !current}`; Make admin/Remove admin (`admin-user-toggle-admin`) MUST send only
  `{is_admin: !current}`.
- **FE-AUSER-022** After a successful PATCH the row MUST be replaced by the returned `AdminUser`
  (same position, matched by `id`); group-changing and admin-changing actions MUST also re-fetch
  groups so member counts and choices stay current.
- **FE-AUSER-023** While a request for a row runs, that row's controls MUST be disabled. On
  failure the envelope message MUST be shown with the action-specific fallback ("Adding the
  group failed.", "Removing the group failed.", "Changing the account status failed.",
  "Changing administrator rights failed.") and the row MUST keep its previous values.
- **FE-AUSER-024** On the admin's own row the Activate/Deactivate, admin toggle and Delete
  buttons MUST be disabled; for a superuser who is admin the Remove admin button MUST be
  disabled (mirrors BE-ADM-024/026).
- **FE-AUSER-025** Delete (`admin-user-delete`) MUST open a confirmation
  (`admin-user-delete-dialog`) naming the user as text; confirming MUST call `deleteUser(id)`
  (`admin_users_destroy`) and re-fetch users and groups. If the deleted row was the only one on a
  page above 1, the previous page MUST be loaded. Cancel MUST make no request. A failure MUST
  show the envelope message (fallback "Delete failed.") and close the dialog.

### Groups page

- **FE-AUSER-030** `/admin/groups` (`AdminGroupsView`, `group-page`, reachable only by an admin
  like FE-AUSER-001) MUST load `listGroups()` and list each group (`group-row`, `data-group`)
  with its `member_count`, or "No groups yet." when empty. The `AdminSidebar` MUST link to it
  (`admin-nav-groups`) directly after Users. The Users page MUST NOT have a Groups button.
- **FE-AUSER-031** Creating a group MUST first validate the name with `validateGroupName` and
  show the message under the input (`group-create-error`) without a request when invalid. A
  valid name MUST be sent trimmed via `createGroup({name})`. A 400 with `fields.name` (e.g.
  "already exists", any case) MUST be shown under the input; other errors in the page alert
  (`group-error`). On success the input MUST clear and the list reload.
- **FE-AUSER-032** The Delete button of the `admin` group MUST be disabled. Deleting another
  group MUST ask for confirmation in a modal (`group-delete-dialog`, naming the group and member count; Cancel, the X and a backdrop click dismiss it) and
  then call `deleteGroup(id)`; success MUST reload the list.
- **FE-AUSER-033** The member count of each group MUST be a button (`group-members`, tooltip
  "View", containing `group-member-count`) that is the only control for opening
  `GroupMembersModal`
  (`group-members-modal`), which MUST load `listUsers({group: <name>, page_size: 200})` and
  list members (`group-member`, `data-username`), or "No members. Add users to this group from
  the user list." when empty.
- **FE-AUSER-034** Removing a member (`group-member-remove`) of the `admin` group MUST send
  `{is_admin: false}`; of any other group it MUST send `{groups: <user's groups without this
  group and without admin>}`. Success MUST reload the members and notify both parents; failure
  MUST show the envelope message (fallback "Removing the member failed.").
- **FE-AUSER-035** Closing (X, Close button or backdrop click) MUST close only the topmost modal.

### Automatic membership

- **FE-AUSER-050** `AdminGroupsView` MUST have two tabs, "Groups" (`group-tab-groups`, the
  default) and "Automatic membership" (`group-tab-auto`). The modal MUST load `getAutoGroups()`
  once with the group list and show a spinner on the second tab until it returns. On failure the
  tab MUST show the envelope message, fallback "Could not load automatic membership rules.".
  If the editor has unsaved changes, switching tab or leaving the page MUST ask for confirmation
  first and do nothing when declined.
- **FE-AUSER-051** The editor (`auto-rules-editor`) MUST explain that users join the groups when
  they activate their account from the e-mail link, that the address must fully match, that
  existing members are not changed and that patterns are case-insensitive. When
  `require_activation` is `false` it MUST show `auto-rules-activation-off` ("Account activation
  is off, so these rules never apply."), and MUST NOT show it otherwise.
- **FE-AUSER-052** The editor MUST let the admin add (`auto-rule-add`), edit, reorder
  (`auto-rule-up`/`-down`) and remove (`auto-rule-remove`) rules, shown as `auto-rule-row` with
  1-based numbers. A rule with a blank pattern MUST show "This rule never matches; fix or remove
  it.". Groups are chips. A select (`auto-rule-group-add`, first option "+ group") MUST offer the
  existing non-admin groups not already in the rule; choosing one adds it and resets the select.
  There is no free-text entry, so the editor cannot create groups. A group named by a rule that
  does not exist (for example from a hand-edited `settings.yaml`) MUST carry a "new" badge
  (`auto-rule-group-new`). Server errors for `groups` MUST be shown under the row
  (`auto-rule-groups-error`).
- **FE-AUSER-053** Save (`auto-rules-save`) MUST clear earlier messages, send the full list with
  `updateAutoGroups(rules)` and stay disabled while the request runs. On success it MUST replace
  the editor contents with the response and show "Rules saved." (`auto-rules-success`). On 400 it
  MUST show the envelope message (`auto-rules-error`) and put each `auto_groups[i].pattern` /
  `auto_groups[i].groups` message under row `i` (`auto-rule-pattern-error`,
  `auto-rule-groups-error`).
- **FE-AUSER-054** "Test email" (`auto-test-email`, `auto-test-submit`; Enter submits) MUST check
  the address with `validateEmail` before any request, then call `testAutoGroups(email, rules)`
  with the editor's rules when it has unsaved changes and without them otherwise. The result
  (`auto-test-result`) MUST list the matched rule numbers and the groups, or "No rule matches
  this address.". Matched rows MUST carry `data-matched="true"`. Editing a rule, adding, removing
  or reordering rules, adding or removing a group, or editing the address MUST clear the result
  and highlights. A 400 MUST be shown under the field (`auto-test-error`) for `fields.email`, or
  under row `i` for `fields.auto_groups[i].…`.
- **FE-AUSER-055** In the Groups tab, each group named by a rule (case-insensitive) MUST show an
  "auto" badge (`group-auto-badge`). Its delete confirmation MUST add "Automatic membership
  rules name this group; it will be created again when a matching user activates.". Deleting a
  group MUST NOT edit any rule.

### Rendering safety

- **FE-AUSER-040** Usernames, full names, e-mails and group names MUST be rendered as text in
  all three components (including the delete confirmations); none of them MAY use `v-html`.
- **FE-AUSER-056** `AutoGroupRulesEditor` MUST render patterns, group names, e-mail addresses
  and server messages as text; it MUST NOT use `v-html`.

## Interfaces

| UI action | API function (`src/api/users.js`) | operationId | Body / params |
|-----------|-----------------------------------|-------------|---------------|
| List / search / page users | `listUsers(params)` | `admin_users_list` | `{search?, page, page_size}`; members modal `{group, page_size: 200}` |
| Change groups / active / admin | `updateUser(id, data)` | `admin_users_partial_update` | one of `{groups}`, `{is_active}`, `{is_admin}` |
| Delete user | `deleteUser(id)` | `admin_users_destroy` | — |
| List groups | `listGroups()` | `admin_groups_list` | — (plain array) |
| Create group | `createGroup({name})` | `admin_groups_create` | `AdminGroupRequest` |
| Delete group | `deleteGroup(id)` | `admin_groups_destroy` | — |
| (unused by views) | `getUser(id)` | `admin_users_retrieve` | — |
| Load rules | `getAutoGroups()` (`admin.js`) | `admin_settings_auto_groups_retrieve` | — |
| Save rules | `updateAutoGroups(rules)` | `admin_settings_auto_groups_update` | `{auto_groups}` |
| Test an address | `testAutoGroups(email, rules?)` | `admin_settings_auto_groups_test` | `{email, auto_groups?}` |

`AutoGroupRulesEditor` props: `rules`, `requireActivation`, `existingGroups`; emits `saved` (the
`AutoGroups` response) and `dirty` (boolean).

Events: `GroupMembersModal` emits
`close`, `members-changed`. Shapes: `AdminUser`, `PaginatedAdminUserList`, `AdminGroup` — see
[api-contract.md](api-contract.md).

## Behaviour

- Row busy state is a map `{[user.id]: true}`; a row is dimmed and its controls disabled while
  its request runs. Other rows stay usable.
- Adding a group via the select resets the select to "+ group" before the request.
- The admin group is handled only through `is_admin` everywhere, matching BE-ADM-022/023: it is
  filtered from chips and from the add-group choices, and removal from the `admin` group in the
  members modal is translated to `is_admin: false`.
- Group modal and members modal are stacked (`z-index` 1060 for members); both refresh their
  own data and bubble a change event so the user table stays consistent.

## Acceptance tests

| Requirement | Test | Layer |
|-------------|------|-------|
| FE-AUSER-001 | `e2e/tests/test_accounts.py::test_a7_non_admin_blocked_from_admin_ui_and_api` | e2e |
| FE-AUSER-010, 011, 013 | `e2e/tests/test_accounts.py::test_d3_admin_users` (search, row, groups column); `frontend/src/test/contracts/users.test.js` › admin users › listUsers → GET /admin/users/ with params (paginated) | e2e, contract |
| FE-AUSER-012 | `e2e/tests/test_accounts.py::test_d3_admin_users` (one row per search; count unchanged after group edits, K1); `frontend/src/test/views/AdminUsersView.test.js` › page change replaces rows, no duplicates (planned) | e2e, unit |
| FE-AUSER-014, 023 | `frontend/src/test/views/AdminUsersView.test.js` › shows envelope message and keeps row on PATCH failure (planned) | unit |
| FE-AUSER-020, 021, 022 | `e2e/tests/test_accounts.py::test_d3_admin_users` (add/remove group, deactivate/activate); `frontend/src/test/contracts/users.test.js` › groups are names, not objects; › updateUser / deleteUser / getUser | e2e, contract |
| FE-AUSER-024 | `frontend/src/test/views/AdminUsersView.test.js` › own row and superuser buttons disabled (planned) | unit |
| FE-AUSER-025 | `e2e/tests/test_accounts.py::test_d3_admin_users` (delete) | e2e |
| FE-AUSER-030, 031, 032 | `e2e/tests/test_accounts.py::test_d3_admin_users` (member counts, create, duplicate in other case, admin delete disabled, delete); `frontend/src/test/contracts/users.test.js` › admin groups › listGroups / createGroup / deleteGroup; `frontend/src/utils/validation.test.js` | e2e, contract, unit |
| FE-AUSER-050 | `frontend/src/test/components/AutoGroupRulesEditor.test.js` › AdminGroupsView automatic membership › shows the load error and asks before discarding unsaved edits | unit |
| FE-AUSER-051, 052, 053, 054, 056 | `frontend/src/test/components/AutoGroupRulesEditor.test.js` › AutoGroupRulesEditor › *; `frontend/src/test/admin-api.test.js` (request shapes); `e2e/tests/test_accounts.py::test_a1c_admin_edits_auto_groups` | unit, contract, e2e |
| FE-AUSER-055 | `frontend/src/test/components/AutoGroupRulesEditor.test.js` › AdminGroupsView automatic membership › marks groups named by a rule and warns when deleting one | unit |
| FE-AUSER-033 (button) | `frontend/src/test/components/AutoGroupRulesEditor.test.js` › AdminGroupsView automatic membership › shows the member count as the button that opens the members | unit |
| FE-AUSER-033, 034 | `e2e/tests/test_admin_users.py::test_group_members_modal_remove_member` (planned) | e2e |
| FE-AUSER-035 | `frontend/src/test/components/GroupModals.test.js` › backdrop closes only top modal (planned) | unit |
| FE-AUSER-040 | `frontend/src/test/views/admin-no-vhtml.test.js` › user and group names render as text (planned) | unit |

## Known gaps

| Requirement | What the code does | Where | Severity |
|-------------|--------------------|-------|----------|
| FE-AUSER-033 | The members modal requests one page of at most 200 (`max_page_size`) and ignores `next`; a group with more than 200 members is silently truncated. | `frontend/src/components/admin/GroupMembersModal.vue:21` | minor |
| FE-AUSER-034 | The Remove button is disabled for every superuser in every group (`user.is_superuser`), not only in the `admin` group, so a superuser cannot be removed from e.g. `researchers` here. It is not disabled for the admin's own row in the `admin` group (server rejects with 400). | `frontend/src/components/admin/GroupMembersModal.vue:87` | minor |
| FE-AUSER-035 | Behaviour of the members modal backdrop relies on `@click.self` on separate overlays and is untested. `Escape` does not close either modal. | `GroupMembersModal.vue:57` | minor |
| FE-AUSER-012 | `fetchUsers` has no stale-response guard: a slow earlier request (e.g. previous page) can overwrite the rows of a later search. Rows are still replaced, not merged, so no duplicates appear. | `frontend/src/views/admin/AdminUsersView.vue:33-48` | minor |
| — | The `group` and `is_active` filters that `admin_users_list` supports are not offered in the user list UI. | `frontend/src/views/admin/AdminUsersView.vue:132-144` | minor |
| — | No component-level tests for the three components; coverage is the single e2e `test_d3_admin_users` plus API-module contract tests. | `frontend/src/test/` | minor |

## Open questions

- If task 01's "admin activation" question is answered yes, the editor's explanatory text
  (FE-AUSER-051) must change.
- Should the editor offer "Apply to existing users" (backfill)? Not today; it needs its own task
  and a decision on whether unverified addresses count.
- Should the API return the `config_status().errors` entries for `auto_groups`, so the editor can
  say why a hand-edited rule was made inert? Today the editor shows a blank pattern with a
  warning.
- Should the user list expose the `group` / `is_active` filters the API already supports?
- The members modal duplicates group editing that the user table offers; keep both?
