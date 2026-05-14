# End-to-End UI Flow Tests (Selenium / Browser)

This document covers the complete user experience from a browser perspective. Tests follow full user journeys rather than individual endpoints, and are designed to catch regressions that curl-based API tests cannot — including SPA routing, state persistence, real-time updates, form rendering, and visual feedback.

Each test is written as step-by-step browser instructions. They can be executed manually or used as the basis for automated Selenium scripts.

---

## Environment Setup

### Requirements
- Google Chrome (latest stable) or Firefox
- ChromeDriver matching Chrome version, added to `$PATH`
- Both servers running:
  - Django backend: `http://localhost:8000`
  - Vite dev server: `http://localhost:5173` (or use production build at `http://localhost:8000`)
- Test users created per [README.md](README.md)

### Before each test session
- Clear browser cookies and localStorage (or use a fresh incognito/private window) to avoid session contamination.
- To clear manually: DevTools → Application → Storage → Clear site data.

### Notation
- `APP` = `http://localhost:5173` (adjust if using production build)
- **Bold** text = UI element to interact with
- `monospace` = value to type or URL to navigate to
- ✅ = expected pass condition

---

## Flow 1 — New User Registration & Activation

**Covers:** Registration form validation, activation link, first login.

### UI-01 — Complete registration flow

**Preconditions:** Username `flowuser` does not exist.

1. Navigate to `APP/register`.
2. ✅ The registration form is displayed with fields: Username, Email, Full Name, Password.
3. Enter: Username = `flowuser`, Email = `flow@example.com`, Full Name = `Flow User`, Password = `Flowpass1`.
4. Click **Register** (or **Sign up**).
5. ✅ A success message appears on the page. The text includes "check your email" or similar. The user is NOT automatically logged in (no username in navbar).
6. Activate the account via the Django shell (bypassing email in dev):
   ```bash
   python manage.py shell -c "
   from django.contrib.auth import get_user_model
   u = get_user_model().objects.get(username='flowuser')
   u.is_active = True
   u.activation_key = None
   u.save()
   "
   ```
7. Navigate to `APP/login`.
8. Enter Username = `flowuser`, Password = `Flowpass1`. Click **Sign in**.
9. ✅ Browser navigates to `APP/` or `APP/jobs`. The navbar shows `flowuser` (or a user icon/dropdown with their username).

---

### UI-02 — Registration form validation (client-side and server-side)

**Preconditions:** App is open at `APP/register`.

1. Submit the form with all fields blank.
2. ✅ Browser-native or Vue validation prevents submission and marks required fields.
3. Enter Username = `ab` (too short), fill remaining fields with valid data. Click **Register**.
4. ✅ An error message appears: "The username must contain at least four characters."
5. Change Username to `test user` (contains a space), keep other fields valid. Click **Register**.
6. ✅ An error message appears indicating only alphanumeric characters are allowed.
7. Change Username to `flowuser2`, set Password = `weak` (no uppercase, no digit). Click **Register**.
8. ✅ An error message appears indicating the password is too short or missing required character types.

---

## Flow 2 — Login, Session, and Logout

**Covers:** Login, token persistence, logout redirect, and CSRF resilience.

### UI-03 — Successful login and token storage

**Preconditions:** `testuser` / `Testpass1` is active.

1. Open a fresh incognito window. Navigate to `APP/login`.
2. Enter Username = `testuser`, Password = `Testpass1`. Click **Sign in**.
3. ✅ Browser navigates away from `/login` (to `/` or `/jobs`).
4. Open DevTools → Application → Local Storage → `http://localhost:5173`.
5. ✅ A key named `cg_token` exists with a non-empty string value.
6. ✅ A key named `cg_user` exists and contains a JSON object with `username: "testuser"`.
7. ✅ The navbar shows `testuser` in the user dropdown (not Login/Sign up links).

---

### UI-04 — Login fails gracefully with wrong password

**Preconditions:** `testuser` is active.

1. Navigate to `APP/login`.
2. Enter Username = `testuser`, Password = `WrongPass99`. Click **Sign in**.
3. ✅ The page does NOT navigate away. An error message is shown (e.g. "Invalid username or password.").
4. ✅ No `cg_token` entry is created in localStorage.

---

### UI-05 — Login succeeds after previous login/logout cycle (CSRF resilience)

This test specifically validates BUG-02 is fixed.

**Preconditions:** `testuser` is active.

1. Log in as `testuser` (UI-03).
2. Log out (click user dropdown → **Logout**).
3. ✅ Browser navigates to `/` (home page) — **not** `/login`. (This also validates BUG-04 is fixed.)
4. Navigate to `APP/login`.
5. Enter credentials again: `testuser` / `Testpass1`. Click **Sign in**.
6. ✅ Login succeeds. Browser navigates away. `cg_token` is set in localStorage.
7. Repeat steps 2–6 three more times without clearing browser data.
8. ✅ Login succeeds every time.

---

### UI-06 — Logout redirects to home page

This test specifically validates BUG-04 is fixed.

**Preconditions:** `testuser` is logged in.

1. Click the user dropdown in the navbar. Click **Logout**.
2. ✅ Browser navigates to `APP/` (the home page, path = `/`).
3. ✅ The URL is NOT `/login`.
4. ✅ The navbar shows Login and Sign up links (logged-out state).
5. ✅ `cg_token` is removed from localStorage.

---

### UI-07 — Protected route redirects unauthenticated user to login

**Preconditions:** User is logged out (fresh incognito window or after UI-06).

1. Navigate directly to `APP/jobs`.
2. ✅ Browser is immediately redirected to `APP/login`.
3. ✅ The URL contains `?next=%2Fjobs` (or similar) preserving the destination.
4. Log in as `testuser`.
5. ✅ Browser navigates to `APP/jobs` (the original destination is restored).

---

### UI-08 — Expired/missing token triggers automatic logout

**Preconditions:** `testuser` is logged in. `cg_token` is in localStorage.

1. Open DevTools → Application → Local Storage.
2. Edit the `cg_token` value to `invalidtoken12345`.
3. Navigate to `APP/jobs` (or click any nav item that triggers an API call).
4. ✅ The app detects the 401 response, clears `cg_token` and `cg_user` from localStorage, and redirects to `APP/login`.

---

## Flow 3 — Password Reset

**Covers:** Reset request, email token, new password, and CSRF resilience.

### UI-09 — Password reset request succeeds (BUG-03 fix validation)

This test specifically validates BUG-03 is fixed.

**Preconditions:** `testuser` exists. Browser may have session cookies from previous logins.

1. Log in and log out once (to ensure a session cookie may be present).
2. Navigate to `APP/reset-password`.
3. Enter email `testuser@example.com`. Click **Send reset link** (or equivalent button).
4. ✅ A success message is shown: "Password reset email sent" or similar.
5. ✅ No 403 error appears.
6. Check that the reset token was created in the database:
   ```bash
   python manage.py shell -c "
   from django.contrib.auth import get_user_model
   u = get_user_model().objects.get(username='testuser')
   print('Token:', u.password_reset_token)
   print('Expires:', u.password_reset_expires)
   "
   ```
7. ✅ `password_reset_token` is a UUID (non-null). `password_reset_expires` is ~24 hours from now.

---

### UI-10 — Complete password reset end-to-end

**Preconditions:** `testuser` has a valid `password_reset_token` (from UI-09 or manually set).

1. Retrieve the token:
   ```bash
   python manage.py shell -c "
   from django.contrib.auth import get_user_model
   u = get_user_model().objects.get(username='testuser')
   print(u.password_reset_token)
   "
   ```
2. Navigate to `APP/recover/<token>`.
3. ✅ A password reset form is displayed (not a 404 or error page).
4. Enter new password `Resetpass9` (and confirm if the form requires it). Submit.
5. ✅ A success message appears (e.g. "Password reset successful").
6. Navigate to `APP/login`. Log in with `testuser` / `Resetpass9`.
7. ✅ Login succeeds. Browser navigates away from `/login`.
8. Try logging in again with the old password `Testpass1`.
9. ✅ Login fails with "Invalid username or password."

> **Teardown:** Reset `testuser`'s password back to `Testpass1` via the shell so subsequent tests can use it.

---

### UI-11 — Password reset form: unknown email shows error

**Preconditions:** Email `nobody@nowhere.com` is not registered.

1. Navigate to `APP/reset-password`.
2. Enter `nobody@nowhere.com`. Submit.
3. ✅ An error message appears (e.g. "No user found with this email address.").
4. ✅ The page does NOT navigate away. No success message is shown.

---

## Flow 4 — Workflow Submission Form

**Covers:** Dynamic form rendering, input types, file upload, submission. Validates BUG-01 fix.

### UI-12 — Workflow form renders all input types (BUG-01 fix validation)

This test specifically validates BUG-01 is fixed.

**Preconditions:** A workflow with at least one input parameter of each type exists. `testuser` is logged in.

1. Navigate to `APP/run/<workflow-id>`.
2. ✅ The form renders a form control for **every** input parameter declared in the workflow. Specifically:
   - A `text` or `string` parameter → renders an `<input type="text">` with the parameter's label.
   - A `local_file` parameter → renders a file picker input.
   - A `list` parameter → renders a `<select>` dropdown with the declared options.
   - A `checkbox` parameter → renders a `<input type="checkbox">`.
   - A `radio` parameter → renders radio buttons.
   - A `textarea` parameter → renders a `<textarea>`.
   - A `terms_checkbox` parameter → renders a checkbox with a link to the terms text.
3. ✅ The **Job Name** field is pre-filled with the workflow's name (editable).
4. ✅ Required parameters are visually indicated as required (asterisk or similar).

---

### UI-13 — Workflow form: hello-cloudgene inputs are visible

This is the specific reproduction of the originally reported bug.

**Preconditions:** The `hello-cloudgene` workflow exists with its configured input parameters.

1. Log in as `testuser`.
2. Navigate to `APP/run/hello-cloudgene`.
3. ✅ The form contains MORE than just the Job Name field.
4. ✅ All input parameters declared in the workflow's configuration are visible.
5. ✅ No JavaScript errors appear in the browser console (DevTools → Console).

---

### UI-14 — Workflow form: required field prevents submission

**Preconditions:** A workflow with at least one required input exists. `testuser` is on the submit page.

1. Navigate to `APP/run/<workflow-id>`.
2. Clear (or do not fill in) a required input field.
3. Click **Submit Job**.
4. ✅ The form does not submit. The required field is highlighted or an error message appears.
5. ✅ The browser does not navigate away from the submit page.
6. ✅ No job appears in `APP/jobs` for `testuser`.

---

### UI-15 — Workflow form: file upload shows progress

**Preconditions:** A workflow with a `local_file` type input exists. `testuser` is on the submit page.

1. Navigate to `APP/run/<workflow-id>`.
2. Click the file input and select any local file (e.g. a small text file).
3. ✅ While the file uploads, a progress indicator (dialog, bar, or percentage) is displayed.
4. ✅ After upload completes, the file name is shown in or next to the file input.
5. ✅ The progress indicator is dismissed or resets to 0% after upload.

---

### UI-16 — Workflow form: successful job submission and redirect

**Preconditions:** A runnable workflow exists. All required inputs have valid values. `testuser` is on the submit page.

1. Navigate to `APP/run/<workflow-id>`.
2. Fill in all required fields with valid values.
3. Click **Submit Job**.
4. ✅ The button shows a loading spinner while submitting.
5. ✅ After submission, browser navigates to `APP/jobs/<new-job-id>`.
6. ✅ The job detail page shows the job name, the workflow name, and status **Pending**.

---

## Flow 5 — Job Monitoring

**Covers:** Job list, job detail tabs, real-time WebSocket updates.

### UI-17 — Job list shows only current user's jobs

**Preconditions:** `testuser` is logged in and has at least one submitted job. `otheruser` has also submitted a job.

1. Navigate to `APP/jobs`.
2. ✅ The page lists `testuser`'s jobs.
3. ✅ `otheruser`'s jobs do NOT appear in the list.
4. ✅ Each row shows at minimum: job name, workflow name, status badge, and submitted date.

---

### UI-18 — Job detail page: Logs tab

**Preconditions:** A completed or running job exists. `testuser` is logged in.

1. Navigate to `APP/jobs`.
2. Click on a completed job.
3. ✅ The job detail page loads. Tabs are visible (Logs, Steps, Results — or similar).
4. Click the **Logs** tab.
5. ✅ Raw text log output is displayed. The content is not blank if the job produced output.
6. ✅ The log content scrolls vertically if it is long.

---

### UI-19 — Job detail page: Steps tab

**Preconditions:** A job with multiple steps exists (at least one completed).

1. Navigate to the job detail page (`APP/jobs/<job-id>`).
2. Click the **Steps** tab.
3. ✅ A list or accordion of workflow steps is shown.
4. ✅ Each step shows its name and a status indicator (e.g. coloured badge or icon).
5. Click on a step to expand it.
6. ✅ Step-level details (e.g. output, duration) are shown inside the expanded accordion item.

---

### UI-20 — Job detail page: Results tab and downloads

**Preconditions:** A completed job with at least one downloadable result file exists.

1. Navigate to the job detail page.
2. Click the **Results** tab.
3. ✅ One or more downloadable files are listed. Each file shows a name and file size.
4. Click the download link/button for a file.
5. ✅ The browser initiates a file download. The downloaded file is valid (not empty, not an HTML error page).

---

### UI-21 — Real-time job status via WebSocket

**Preconditions:** The Celery worker and Redis are running. A newly submitted job is in `pending` or `running` state.

1. Navigate to `APP/jobs/<job-id>` while the job is still running.
2. Do NOT refresh the page.
3. Watch the status badge and Steps tab.
4. ✅ The status badge updates automatically (e.g. from **Running** to **Completed**) without a manual page refresh.
5. ✅ Step statuses update in real-time as each step completes.
6. Open browser DevTools → Network → WS (WebSocket tab). Confirm a WebSocket connection is established to `ws://localhost:8000/ws/jobs/<job-id>/`.
7. ✅ The WebSocket connection closes cleanly when navigating away from the page (no lingering connections).

---

### UI-22 — Cancel a running job from the UI

**Preconditions:** `testuser` has a job in `pending` or `running` state.

1. Navigate to `APP/jobs/<job-id>`.
2. Locate the **Cancel** button (may be on the job detail page or in a dropdown).
3. Click **Cancel**. Confirm in any confirmation dialog.
4. ✅ The job status badge changes to **Cancelled**.
5. ✅ The Cancel button is no longer active (or is hidden) after cancellation.
6. Navigate to `APP/jobs` (the list view).
7. ✅ The job shows status **Cancelled** in the list.

---

## Flow 6 — Admin Panel

**Covers:** Admin-only views, user management, settings.

### UI-23 — Admin dashboard loads with statistics

**Preconditions:** `adminuser` is logged in.

1. Navigate to `APP/admin`.
2. ✅ The Admin Dashboard is displayed (not redirected).
3. ✅ Statistics cards show numeric values for total jobs, users, and workflows.
4. ✅ A chart (jobs over time) is rendered — not blank, no console errors.
5. ✅ A table of recent jobs is shown.
6. ✅ Recent system log entries are listed.

---

### UI-24 — Admin sidebar navigation

**Preconditions:** `adminuser` is logged in and on any `/admin` page.

1. ✅ A sidebar is visible with links to: Dashboard, Jobs, Users, Workflows, Settings (General, Nextflow, Mail, Templates, Logs).
2. Click each link in turn.
3. ✅ Each link navigates to the correct view without a full page reload (SPA navigation).
4. ✅ The active sidebar item is visually highlighted.

---

### UI-25 — Admin users page: list, create, delete

**Preconditions:** `adminuser` is logged in. Navigate to `APP/admin/users`.

1. ✅ A paginated list of all users is shown. `testuser`, `otheruser`, and `adminuser` all appear.
2. Find `otheruser` in the list. Click **Delete** (or a trash icon).
3. ✅ A confirmation dialog appears asking "Are you sure?".
4. Confirm the deletion.
5. ✅ `otheruser` is removed from the list without a page reload.
6. Verify via API: `GET /api/users/` (as admin) should not include `otheruser`.

> **Teardown:** Recreate `otheruser` after this test if needed for subsequent tests.

---

### UI-26 — Non-admin is blocked from admin panel

**Preconditions:** `testuser` (non-admin) is logged in.

1. Navigate directly to `APP/admin`.
2. ✅ The browser is redirected away (to `APP/` or `APP/login`). The admin dashboard is NOT displayed.
3. Navigate directly to `APP/admin/users`.
4. ✅ Same redirect. No user list is shown.

---

### UI-27 — Template editor: update and verify

**Preconditions:** `adminuser` is logged in. At least one template exists.

1. Navigate to `APP/admin/settings/templates`.
2. ✅ A list of available templates is shown.
3. Select any template.
4. ✅ The template's current content is displayed in an editable area.
5. Change the content text slightly (e.g. add a comment or extra space).
6. Click **Save**.
7. ✅ A success message or visual confirmation appears.
8. Reload the page. Select the same template again.
9. ✅ The edited content is still present (it was persisted).

---

### UI-28 — System logs page: display and filter

**Preconditions:** `adminuser` is logged in. At least some system log entries exist.

1. Navigate to `APP/admin/settings/logs`.
2. ✅ Log entries are displayed in reverse chronological order.
3. If a filter control is present (e.g. "Level" dropdown), select **error**.
4. ✅ Only log entries with level `error` are shown. Other levels are hidden.

---

## Flow 7 — Profile Page

### UI-29 — View and edit profile

**Preconditions:** `testuser` is logged in.

1. Navigate to `APP/profile`.
2. ✅ The profile page loads showing `testuser`'s current username, email, and full name.
3. Edit the Full Name to `Updated Test User`. Click **Save** (or equivalent).
4. ✅ A success message appears.
5. Navigate away (e.g. to `APP/jobs`), then return to `APP/profile`.
6. ✅ The full name shows `Updated Test User` (the change was persisted).

---

### UI-30 — API token is visible and copyable

**Preconditions:** `testuser` is logged in and on `APP/profile`.

1. Locate the API token section.
2. ✅ A token value is displayed (may be masked, e.g. `••••••abc123`).
3. Click **Copy** (or reveal + copy).
4. ✅ The clipboard contains the full token string.
5. Verify the token matches by logging in via API and comparing:
   ```bash
   curl -s -X POST "http://localhost:8000/api/auth/login/" \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "password": "Testpass1"}' \
     | python -c "import sys,json; print(json.load(sys.stdin)['token'])"
   ```

---

## Flow 8 — Navbar & Layout

### UI-31 — Navbar items rendered from API

**Preconditions:** At least one `NavbarItem` exists. No user is logged in.

1. Navigate to `APP/`.
2. ✅ The top navbar is visible with the **Cloudgene** brand link.
3. ✅ Any configured navbar items (from `GET /api/admin/navbar-items/`) appear as links.
4. ✅ The Login and Sign up links are visible (user is not logged in).
5. Log in as `adminuser`.
6. ✅ Admin-only navbar items (where `admin_only = true`) are now visible. They were hidden when logged out.

---

### UI-32 — Responsive layout on mobile viewport

**Preconditions:** Any page is open.

1. In DevTools, enable the device toolbar. Set viewport to iPhone 12 (390×844).
2. Navigate to `APP/login`, `APP/jobs`, and `APP/admin` (as admin).
3. ✅ On each page, content is readable without horizontal scrolling.
4. ✅ The navbar collapses into a hamburger menu at mobile width.
5. Click the hamburger. ✅ The nav menu expands with all links accessible.

---

## Regression Checklist

After each bug fix, run the following quick smoke tests to confirm no regressions:

| Check | Expected |
|-------|----------|
| Navigate to `APP/login`, log in with valid credentials | Succeeds every time, including after a previous login/logout |
| Navigate to `APP/reset-password`, enter a valid email | Success message; no 403 error |
| Navigate to `APP/run/<workflow-id>` for any workflow with inputs | All input fields are visible |
| Log out from the user dropdown | Redirected to `APP/` (home page, not `/login`) |
| Navigate to `APP/admin` while logged in as non-admin | Redirected away |
| Navigate to `APP/jobs` without being logged in | Redirected to `APP/login` |
