# Workflow Tests

Tests for workflow listing, access control, category filtering, the job submission form, and admin workflow management.

Assumes `BASE`, `APP`, `USER_TOKEN`, and `ADMIN_TOKEN` are set as described in [README.md](README.md).

---

## Test Data Setup

Before running these tests, ensure at least the following workflows exist. Use the Django admin (`http://localhost:8000/admin/`) or the shell to create them:

```bash
python manage.py shell -c "
from workflows.models import Workflow, WorkflowCategory
from django.contrib.auth import get_user_model

User = get_user_model()
admin = User.objects.get(username='adminuser')

cat, _ = WorkflowCategory.objects.get_or_create(name='Genomics')

# Public workflow (visible to everyone)
Workflow.objects.get_or_create(
    name='Public Workflow',
    defaults=dict(
        description='A public test workflow',
        version='1.0',
        category=cat,
        status='enabled',
        public=True,
        created_by=admin,
        yaml_config='',
    )
)

# Private workflow (visible only to members of 'internal' group)
from django.contrib.auth.models import Group
grp, _ = Group.objects.get_or_create(name='internal')
wf, _ = Workflow.objects.get_or_create(
    name='Private Workflow',
    defaults=dict(
        description='A group-restricted test workflow',
        version='1.0',
        category=cat,
        status='enabled',
        public=False,
        created_by=admin,
        yaml_config='',
    )
)
wf.allowed_groups.add(grp)

# Disabled workflow (hidden from non-admins)
Workflow.objects.get_or_create(
    name='Disabled Workflow',
    defaults=dict(
        description='This workflow is disabled',
        version='1.0',
        category=cat,
        status='disabled',
        public=True,
        created_by=admin,
        yaml_config='',
    )
)

print('Done')
"
```

---

## 1. Workflow Listing Access Control

### WFLOW-01 — Anonymous user sees only public workflows

- **Preconditions:** At least one `public=True, status=enabled` workflow and one `public=False` workflow exist.
- **Steps (API):**
  1. Send without any auth token:
     ```bash
     curl -s "$BASE/workflows/"
     ```
- **Expected result:** HTTP 200. The response array contains only workflows where `public = true`. The "Private Workflow" and "Disabled Workflow" are absent.

---

### WFLOW-02 — Authenticated non-member sees public + own-group workflows

- **Preconditions:** `testuser` is authenticated. `testuser` is **not** a member of the `internal` group.
- **Steps (API):**
  1. Send with user token:
     ```bash
     curl -s "$BASE/workflows/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 200. "Public Workflow" is present. "Private Workflow" is absent. "Disabled Workflow" is absent.

---

### WFLOW-03 — Group member sees group-restricted workflow

- **Preconditions:** `testuser` is a member of the `internal` group. Add them:
  ```bash
  python manage.py shell -c "
  from django.contrib.auth import get_user_model
  from django.contrib.auth.models import Group
  u = get_user_model().objects.get(username='testuser')
  g = Group.objects.get(name='internal')
  u.groups.add(g)
  print('added')
  "
  ```
- **Steps (API):**
  1. Send with user token:
     ```bash
     curl -s "$BASE/workflows/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 200. Both "Public Workflow" and "Private Workflow" appear. "Disabled Workflow" is still absent.

> **Teardown:** Remove `testuser` from `internal` group after this test if subsequent tests assume they are not a member.

---

### WFLOW-04 — Admin sees all enabled workflows

- **Preconditions:** `adminuser` is authenticated. At least one `public=False` enabled workflow exists.
- **Steps (API):**
  1. Send with admin token:
     ```bash
     curl -s "$BASE/workflows/" \
       -H "Authorization: Token $ADMIN_TOKEN"
     ```
- **Expected result:** HTTP 200. Both "Public Workflow" and "Private Workflow" appear. "Disabled Workflow" does **not** appear (it has `status=disabled`, which is filtered for everyone).

---

### WFLOW-05 — Disabled workflows are hidden from all non-admin users

- **Preconditions:** "Disabled Workflow" exists with `status=disabled, public=True`.
- **Steps (API):**
  1. Send without token:
     ```bash
     curl -s "$BASE/workflows/"
     ```
  2. Send with user token:
     ```bash
     curl -s "$BASE/workflows/" -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** Both responses return HTTP 200. "Disabled Workflow" is absent from both results.

---

## 2. Category Filter

### WFLOW-06 — Filter by category returns matching workflows

- **Preconditions:** At least one workflow with `category.name = "Genomics"` exists.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/workflows/?category=Genomics"
     ```
- **Expected result:** HTTP 200. All returned workflows have `category.name = "Genomics"`. Workflows from other categories are absent.

---

### WFLOW-07 — Filter by non-existent category returns empty list

- **Preconditions:** No workflow has a category named `"Nonexistent"`.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/workflows/?category=Nonexistent"
     ```
- **Expected result:** HTTP 200. Response body is an empty array `[]`.

---

### WFLOW-08 — Categories endpoint returns all categories

- **Preconditions:** At least one `WorkflowCategory` exists (e.g. `Genomics`).
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/categories/"
     ```
- **Expected result:** HTTP 200. Response is a list containing at least `{"id": ..., "name": "Genomics"}`.

---

## 3. Workflow Detail & Submission Form

### WFLOW-09 — Get workflow detail returns parameters list

- **Preconditions:** A workflow with known `<id>` exists (get the ID from WFLOW-01 results).
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/workflows/<id>/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 200. Response includes `id`, `name`, `description`, `version`, `status`, `public`, and a `parameters` array (may be empty if the workflow has no declared inputs).

---

### WFLOW-10 — Workflow detail: access denied for group-restricted workflow

- **Preconditions:** "Private Workflow" exists with `public=False`. `testuser` is **not** in `internal` group.
- **Steps (API):**
  1. Get the ID of "Private Workflow":
     ```bash
     curl -s "$BASE/workflows/" -H "Authorization: Token $ADMIN_TOKEN" \
       | python -c "import sys,json; [print(w['id'], w['name']) for w in json.load(sys.stdin)]"
     ```
  2. Attempt to fetch the private workflow detail as `testuser`:
     ```bash
     curl -s "$BASE/workflows/<private_id>/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 404 (the object is not in the user's queryset).

---

### WFLOW-11 — WorkflowSubmitView renders the dynamic form

- **Preconditions:** At least one enabled workflow exists. `testuser` is logged in via the UI.
- **Steps (UI):**
  1. Navigate to `$APP/` (the home page). Workflow cards should be visible.
  2. Click on the "Public Workflow" card (or navigate to `$APP/run/<id>`).
- **Expected result:**
  - The workflow's name, description, and version are displayed.
  - For each parameter declared in the workflow's `yaml_config`, a corresponding form input is rendered:
    - `text` type → `<input type="text">`
    - `file` type → a file picker input
    - `select` type → `<select>` dropdown
    - `checkbox` type → `<input type="checkbox">`
    - `radio` type → radio buttons
    - `textarea` type → `<textarea>`
    - `terms` type → a checkbox with a link to terms text
  - Required parameters are marked as required.

---

### WFLOW-12 — Workflow submit form: required field validation

- **Preconditions:** A workflow with at least one required parameter exists. `testuser` is on the submit page.
- **Steps (UI):**
  1. Navigate to `$APP/run/<id>`.
  2. Leave a required field blank.
  3. Click **Submit** (or equivalent).
- **Expected result:** The form does not submit. An error message or visual indicator marks the required field(s). The browser does not navigate away from the submit page.

---

### WFLOW-13 — File upload shows progress dialog

- **Preconditions:** A workflow with a `file` type parameter exists. `testuser` is on the submit page.
- **Steps (UI):**
  1. Navigate to `$APP/run/<id>`.
  2. Click the file input for the file parameter and select a local file (any file).
- **Expected result:** A progress dialog or indicator appears while the file uploads. The dialog closes (or progress reaches 100%) after the upload completes. The file name is shown in the form.

---

## 4. Admin Workflow Management

### WFLOW-14 — Admin can list all workflows including disabled

- **Preconditions:** `adminuser` is logged in. Navigate to `$APP/admin/workflows`.
- **Steps (UI):**
  1. Navigate to `$APP/admin/workflows`.
- **Expected result:** A table or list of all workflows is shown, including disabled ones. Each row shows the workflow name, status (enabled/disabled), and visibility (public/private).

---

### WFLOW-15 — Admin can disable an enabled workflow

- **Preconditions:** "Public Workflow" is currently `status=enabled`. `adminuser` is on `$APP/admin/workflows`.
- **Steps (UI):**
  1. Find "Public Workflow" in the list.
  2. Click the **Disable** toggle or button.
- **Expected result:** The workflow's status changes to `disabled` in the UI. The workflow no longer appears in `GET /api/workflows/` for non-admin users (verify with WFLOW-01).

---

### WFLOW-16 — Admin can re-enable a disabled workflow

- **Preconditions:** "Public Workflow" is currently `status=disabled` (from WFLOW-15).
- **Steps (UI):**
  1. On `$APP/admin/workflows`, find "Public Workflow".
  2. Click the **Enable** toggle or button.
- **Expected result:** The workflow's status changes to `enabled`. It reappears in `GET /api/workflows/` for authenticated users.

---

### WFLOW-17 — Admin can assign group access to a workflow

- **Preconditions:** "Private Workflow" exists. The `internal` group exists. `adminuser` is on `$APP/admin/workflows/<private_id>`.
- **Steps (UI):**
  1. Navigate to `$APP/admin/workflows/<private_id>`.
  2. In the group access section, add the `internal` group.
  3. Save.
- **Expected result:** A member of the `internal` group can now see "Private Workflow" in `GET /api/workflows/`.

---

### WFLOW-18 — Non-admin cannot access admin workflow management

- **Preconditions:** `testuser` is logged in (not admin).
- **Steps (UI):**
  1. Navigate directly to `$APP/admin/workflows`.
- **Expected result:** Redirected to `$APP/` or `$APP/login`. Admin workflow view is not displayed.
