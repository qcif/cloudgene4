# Admin Panel Tests

Tests for the admin dashboard, user management, server settings, template editor, navbar items, system logs, and the user profile page.

Assumes `BASE`, `APP`, `USER_TOKEN`, and `ADMIN_TOKEN` are set as described in [README.md](README.md).

---

## 1. Access Control

### ADMIN-01 — Non-admin is blocked from all admin API endpoints

- **Preconditions:** `testuser` is authenticated (non-admin).
- **Steps (API):**
  1. Attempt each admin endpoint:
     ```bash
     curl -s "$BASE/admin/dashboard/"       -H "Authorization: Token $USER_TOKEN"
     curl -s "$BASE/admin/server-settings/" -H "Authorization: Token $USER_TOKEN"
     curl -s "$BASE/admin/system-logs/"     -H "Authorization: Token $USER_TOKEN"
     curl -s "$BASE/admin/counters/"        -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** All four requests return HTTP 403. No data is returned.

---

### ADMIN-02 — Non-admin templates and navbar-items endpoints are read-only

- **Preconditions:** `testuser` is authenticated (non-admin).
- **Steps (API):**
  1. Read templates (should succeed):
     ```bash
     curl -s "$BASE/admin/templates/" -H "Authorization: Token $USER_TOKEN"
     ```
  2. Attempt to update a template (should fail):
     ```bash
     TEMPLATE_ID=$(curl -s "$BASE/admin/templates/" | python -c "import sys,json; items=json.load(sys.stdin); print(items[0]['id']) if items else print('')")
     curl -s -X PATCH "$BASE/admin/templates/$TEMPLATE_ID/" \
       -H "Authorization: Token $USER_TOKEN" \
       -H "Content-Type: application/json" \
       -d '{"content": "<p>hacked</p>"}'
     ```
  3. Read navbar items (should succeed):
     ```bash
     curl -s "$BASE/admin/navbar-items/" -H "Authorization: Token $USER_TOKEN"
     ```
  4. Attempt to create a navbar item (should fail):
     ```bash
     curl -s -X POST "$BASE/admin/navbar-items/" \
       -H "Authorization: Token $USER_TOKEN" \
       -H "Content-Type: application/json" \
       -d '{"label": "Hacked", "url": "/hacked"}'
     ```
- **Expected result:** Steps 1 and 3 return HTTP 200. Steps 2 and 4 return HTTP 403.

---

### ADMIN-03 — Non-admin UI access to /admin/* is redirected

- **Preconditions:** `testuser` (non-admin) is logged in via the UI.
- **Steps (UI):**
  1. Navigate directly to `$APP/admin`.
  2. Navigate directly to `$APP/admin/users`.
  3. Navigate directly to `$APP/admin/settings/general`.
- **Expected result:** All three navigations redirect the user to `$APP/` (homepage) or `$APP/login`. No admin UI content is displayed.

---

### ADMIN-04 — Unauthenticated access to /admin/* is redirected to /login

- **Preconditions:** No user is logged in.
- **Steps (UI):**
  1. Navigate directly to `$APP/admin`.
- **Expected result:** Browser redirects to `$APP/login`.

---

## 2. Dashboard

### ADMIN-05 — Dashboard API returns statistics and recent data

- **Preconditions:** At least one job, user, and workflow exist.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/admin/dashboard/" \
       -H "Authorization: Token $ADMIN_TOKEN" \
       | python -m json.tool
     ```
- **Expected result:** HTTP 200. Response contains:
  - `statistics.jobs` — object with keys: `total`, `pending`, `running`, `completed`, `failed`, `cancelled` (all integers ≥ 0)
  - `statistics.users` — object with keys: `total`, `active`, `staff`
  - `statistics.workflows` — object with keys: `total`, `enabled`, `disabled`
  - `recent_jobs` — array of up to 10 recent job objects
  - `recent_logs` — array of up to 10 recent log entries

---

### ADMIN-06 — Dashboard statistics are accurate

- **Preconditions:** You know the exact counts in the database (query them):
  ```bash
  python manage.py shell -c "
  from jobs.models import Job
  from django.contrib.auth import get_user_model
  from workflows.models import Workflow
  print('Jobs total:', Job.objects.count())
  print('Users total:', get_user_model().objects.count())
  print('Workflows enabled:', Workflow.objects.filter(status='enabled').count())
  "
  ```
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/admin/dashboard/" -H "Authorization: Token $ADMIN_TOKEN"
     ```
- **Expected result:** The `statistics.jobs.total`, `statistics.users.total`, and `statistics.workflows.enabled` values match the database counts exactly.

---

### ADMIN-07 — Dashboard UI displays stats cards and recent activity

- **Preconditions:** `adminuser` is logged in via the UI.
- **Steps (UI):**
  1. Navigate to `$APP/admin`.
- **Expected result:**
  - Stats cards are visible showing total/active counts for jobs, users, and workflows.
  - A chart (e.g. jobs-over-time area chart) is rendered.
  - A table or list of recent jobs is shown.
  - A list of recent system log entries is shown.

---

## 3. User Management

### ADMIN-08 — Admin can list all users

- **Preconditions:** At least `testuser`, `otheruser`, and `adminuser` exist.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/users/" -H "Authorization: Token $ADMIN_TOKEN"
     ```
- **Expected result:** HTTP 200. Response is a list containing all users. Each user object includes `id`, `username`, `email`, `full_name`, `is_active`, `is_admin`, `groups`.

---

### ADMIN-09 — Regular user can only see their own profile

- **Preconditions:** `testuser` is authenticated.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/users/" -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 200. Response contains only `testuser`'s own user object (list of one).

---

### ADMIN-10 — Admin can create a new user via API

- **Preconditions:** `adminuser` is authenticated. Username `newadminuser` does not exist.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/users/" \
       -H "Authorization: Token $ADMIN_TOKEN" \
       -H "Content-Type: application/json" \
       -d '{
         "username": "newadminuser",
         "email": "newadmin@x.com",
         "full_name": "New Admin User",
         "password": "Adminpass1"
       }'
     ```
- **Expected result:** HTTP 201. The new user exists in the database.

---

### ADMIN-11 — Admin can change a user's group membership

- **Preconditions:** `testuser` exists. An `internal` group exists.
- **Steps (UI):**
  1. Navigate to `$APP/admin/users`.
  2. Find `testuser` in the list.
  3. Add the `internal` group to `testuser`.
  4. Save.
- **Expected result:** `testuser.groups` now includes `internal`. Verify via:
  ```bash
  curl -s "$BASE/users/" -H "Authorization: Token $ADMIN_TOKEN" \
    | python -c "import sys,json; users=json.load(sys.stdin); [print(u['groups']) for u in users if u['username']=='testuser']"
  ```

---

### ADMIN-12 — Admin can delete a user

- **Preconditions:** A disposable user (e.g. `newadminuser` from ADMIN-10) exists.
- **Steps (UI):**
  1. Navigate to `$APP/admin/users`.
  2. Find `newadminuser`.
  3. Click **Delete** and confirm.
- **Expected result:** The user no longer appears in the user list. `GET /api/users/` (as admin) does not include `newadminuser`.

---

### ADMIN-13 — Admin users management: non-admin is blocked

- **Preconditions:** `testuser` is authenticated (non-admin).
- **Steps (API):**
  1. Attempt to delete a user:
     ```bash
     USER_ID=$(curl -s "$BASE/users/" -H "Authorization: Token $ADMIN_TOKEN" \
       | python -c "import sys,json; u=[x for x in json.load(sys.stdin) if x['username']=='otheruser']; print(u[0]['id'] if u else '')")
     curl -s -X DELETE "$BASE/users/$USER_ID/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 403. `otheruser` still exists in the database.

---

## 4. Server Settings

### ADMIN-14 — Admin can retrieve server settings

- **Preconditions:** `adminuser` is authenticated. At least one `ServerSettings` record exists.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/admin/server-settings/" \
       -H "Authorization: Token $ADMIN_TOKEN"
     ```
- **Expected result:** HTTP 200. Response is a list of settings objects.

---

### ADMIN-15 — Admin can update server settings

- **Preconditions:** A `ServerSettings` record exists with a known `id`.
- **Steps (API):**
  1. Get the settings ID:
     ```bash
     SETTINGS_ID=$(curl -s "$BASE/admin/server-settings/" \
       -H "Authorization: Token $ADMIN_TOKEN" \
       | python -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")
     ```
  2. Update a setting:
     ```bash
     curl -s -X PATCH "$BASE/admin/server-settings/$SETTINGS_ID/" \
       -H "Authorization: Token $ADMIN_TOKEN" \
       -H "Content-Type: application/json" \
       -d '{"server_name": "Cloudgene QA Test"}'
     ```
- **Expected result:** HTTP 200. The updated field is reflected in the response and in the database.

---

### ADMIN-16 — Non-admin cannot read or update server settings

- **Preconditions:** `testuser` is authenticated.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/admin/server-settings/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 403.

---

### ADMIN-17 — General settings UI is accessible to admins

- **Preconditions:** `adminuser` is logged in.
- **Steps (UI):**
  1. Navigate to `$APP/admin/settings/general`.
- **Expected result:** A settings form is displayed showing current server configuration. Fields are editable and saving works.

---

### ADMIN-18 — Nextflow and Mail settings pages load

- **Preconditions:** `adminuser` is logged in.
- **Steps (UI):**
  1. Navigate to `$APP/admin/settings/nextflow`.
  2. Navigate to `$APP/admin/settings/mail`.
- **Expected result:** Both pages load without errors and show relevant configuration forms.

---

## 5. Template Editor

### ADMIN-19 — Anyone can read templates

- **Preconditions:** At least one `Template` exists.
- **Steps (API):**
  1. Without auth:
     ```bash
     curl -s "$BASE/admin/templates/"
     ```
  2. With user token:
     ```bash
     curl -s "$BASE/admin/templates/" -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** Both return HTTP 200 with a list of template objects.

---

### ADMIN-20 — Admin can update a template

- **Preconditions:** A `Template` exists with known `id`. `adminuser` is authenticated.
- **Steps (API):**
  1. Get a template ID:
     ```bash
     TMPL_ID=$(curl -s "$BASE/admin/templates/" \
       | python -c "import sys,json; items=json.load(sys.stdin); print(items[0]['id']) if items else print('')")
     ```
  2. Update its content:
     ```bash
     curl -s -X PATCH "$BASE/admin/templates/$TMPL_ID/" \
       -H "Authorization: Token $ADMIN_TOKEN" \
       -H "Content-Type: application/json" \
       -d '{"content": "<p>Updated content</p>"}'
     ```
- **Expected result:** HTTP 200. `content` in the response equals `"<p>Updated content</p>"`.

---

### ADMIN-21 — Template editor UI is accessible to admin

- **Preconditions:** `adminuser` is logged in.
- **Steps (UI):**
  1. Navigate to `$APP/admin/settings/templates`.
- **Expected result:** A list of templates is shown. Selecting a template displays its content in an editor. Saving updates the template content.

---

### ADMIN-22 — Non-admin cannot update templates

- **Preconditions:** `testuser` is authenticated. A template ID is known.
- **Steps (API):**
  1. Attempt to update:
     ```bash
     curl -s -X PATCH "$BASE/admin/templates/$TMPL_ID/" \
       -H "Authorization: Token $USER_TOKEN" \
       -H "Content-Type: application/json" \
       -d '{"content": "evil content"}'
     ```
- **Expected result:** HTTP 403.

---

## 6. Navbar Items

### ADMIN-23 — Anyone can read navbar items

- **Preconditions:** At least one `NavbarItem` exists.
- **Steps (API):**
  1. Without auth:
     ```bash
     curl -s "$BASE/admin/navbar-items/"
     ```
- **Expected result:** HTTP 200. Response is a list of navbar item objects.

---

### ADMIN-24 — Navbar renders items from API on page load

- **Preconditions:** At least one navbar item exists. `testuser` is logged in.
- **Steps (UI):**
  1. Navigate to any public page (e.g. `$APP/jobs`).
- **Expected result:** The top navigation bar displays the items returned by `GET /api/admin/navbar-items/`. Admin-only items are visible only when logged in as an admin.

---

### ADMIN-25 — Admin can create a navbar item

- **Preconditions:** `adminuser` is authenticated.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/admin/navbar-items/" \
       -H "Authorization: Token $ADMIN_TOKEN" \
       -H "Content-Type: application/json" \
       -d '{"label": "Docs", "url": "/pages/docs", "order": 99}'
     ```
- **Expected result:** HTTP 201. The new navbar item appears in subsequent `GET /api/admin/navbar-items/` responses.

---

### ADMIN-26 — Non-admin cannot create or update navbar items

- **Preconditions:** `testuser` is authenticated.
- **Steps (API):**
  1. Attempt to create a navbar item:
     ```bash
     curl -s -X POST "$BASE/admin/navbar-items/" \
       -H "Authorization: Token $USER_TOKEN" \
       -H "Content-Type: application/json" \
       -d '{"label": "Hacked", "url": "/hacked"}'
     ```
- **Expected result:** HTTP 403.

---

## 7. System Logs

### ADMIN-27 — Admin can read system logs

- **Preconditions:** At least one `SystemLog` entry exists.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/admin/system-logs/" \
       -H "Authorization: Token $ADMIN_TOKEN"
     ```
- **Expected result:** HTTP 200. Response is a list of log entries ordered by `timestamp` descending. Each entry has at minimum: `id`, `level`, `component`, `message`, `timestamp`.

---

### ADMIN-28 — System logs can be filtered by level

- **Preconditions:** Log entries of multiple levels exist.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/admin/system-logs/?level=error" \
       -H "Authorization: Token $ADMIN_TOKEN"
     ```
- **Expected result:** HTTP 200. All returned log entries have `level = "error"`. Entries of other levels are absent.

---

### ADMIN-29 — System logs can be filtered by component

- **Preconditions:** Log entries from multiple components exist.
- **Steps (API):**
  1. Send with a known component name (e.g. `auth`):
     ```bash
     curl -s "$BASE/admin/system-logs/?component=auth" \
       -H "Authorization: Token $ADMIN_TOKEN"
     ```
- **Expected result:** HTTP 200. All returned entries have `component = "auth"`.

---

### ADMIN-30 — Non-admin cannot read system logs

- **Preconditions:** `testuser` is authenticated.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/admin/system-logs/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 403.

---

### ADMIN-31 — Logs viewer UI is accessible to admin

- **Preconditions:** `adminuser` is logged in.
- **Steps (UI):**
  1. Navigate to `$APP/admin/settings/logs`.
- **Expected result:** A log viewer is displayed. Entries are shown in reverse chronological order. Filtering controls (by level and/or component) are present and functional.

---

## 8. Profile Page

### ADMIN-32 — Authenticated user can view their profile

- **Preconditions:** `testuser` is logged in.
- **Steps (UI):**
  1. Navigate to `$APP/profile`.
- **Expected result:** The profile page is displayed showing `testuser`'s username, email, and full name.

---

### ADMIN-33 — User can edit their full_name and email

- **Preconditions:** `testuser` is logged in. API endpoint: `PATCH /api/users/<user_id>/`.
- **Steps (UI):**
  1. Navigate to `$APP/profile`.
  2. Edit the Full Name field to `"Updated Name"`.
  3. Save.
- **Expected result:** The change is persisted. The profile page reflects `"Updated Name"`. A GET of `$BASE/users/<user_id>/` (as admin) confirms `full_name = "Updated Name"`.

---

### ADMIN-34 — Profile page shows (or allows copying) the API token

- **Preconditions:** `testuser` is logged in.
- **Steps (UI):**
  1. Navigate to `$APP/profile`.
  2. Locate the API token section.
  3. Click **Copy** (or equivalent) to copy the token to the clipboard.
- **Expected result:** The token field displays a masked or full token value. The copy action succeeds (clipboard contains the token). The token matches the value returned by the login API (`POST /api/auth/login/`).

---

### ADMIN-35 — Unauthenticated access to /profile is redirected

- **Preconditions:** No user is logged in.
- **Steps (UI):**
  1. Navigate to `$APP/profile`.
- **Expected result:** Browser redirects to `$APP/login`.

---

## 9. Static Content Pages

### ADMIN-36 — Static page renders content from templates API

- **Preconditions:** A `Template` of type `page` with a known slug exists (e.g. slug = `home`).
- **Steps (UI):**
  1. Navigate to `$APP/pages/<slug>`.
- **Expected result:** The page renders the HTML content stored in the template. The content matches what is stored in `GET /api/admin/templates/` for that slug.

---

### ADMIN-37 — Home page renders template content

- **Preconditions:** A `Template` for the home page exists.
- **Steps (UI):**
  1. Navigate to `$APP/`.
- **Expected result:** The home page renders dynamic HTML from the templates API. The page is not blank.
