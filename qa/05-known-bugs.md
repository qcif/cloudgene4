# Known Bugs — Reproduction Steps & Root Causes

This document describes confirmed bugs in the current build, with precise reproduction steps, observed behaviour, expected behaviour, and the root cause (for the development team). These bugs were identified through manual UI testing.

QA engineers should verify each bug is present before a fix is applied (to confirm the reproduction case), then re-test after the fix to confirm resolution.

---

## BUG-01 — Workflow submission form shows only the Job Name field

### Severity: Critical (blocks core user flow)

### Observed behaviour
When a user navigates to `/run/<workflow-id>` for a workflow that has configured input parameters, only the **Job Name** field is displayed. None of the workflow's declared inputs (text fields, file uploads, dropdowns, etc.) appear.

### Steps to reproduce
1. Log in as any authenticated user.
2. Ensure at least one workflow exists with one or more configured input parameters.
3. Navigate to `/run/<workflow-id>`.
4. Observe the form.

**Actual:** The form contains only the "Job name" `<input>` field. The `DynamicForm` component renders nothing.

**Expected:** One input control is rendered per workflow parameter, matching the parameter's type (text, file, select, checkbox, radio, textarea, terms).

### Root cause

**Field name mismatch between the API serializer and the Vue component.**

`WorkflowParameterSerializer` ([workflows/serializers.py:14](../workflows/serializers.py#L14)) serializes the parameter type and ID as:
```python
fields = ['parameter_id', 'parameter_type', ...]
```

`DynamicForm.vue` ([frontend/src/components/workflows/form/DynamicForm.vue:50](../frontend/src/components/workflows/form/DynamicForm.vue#L50)) reads these as:
```js
param.type   // → undefined (field is named 'parameter_type')
param.id     // → undefined (field is named 'parameter_id')
```

Because `param.type` is always `undefined`, no `v-else-if` branch in the template ever matches, so the entire body of the `v-for` renders nothing. The `values` reactive object is also keyed on `undefined` for every parameter.

Also, `WorkflowSubmitView.vue` ([frontend/src/views/public/WorkflowSubmitView.vue:31](../frontend/src/views/public/WorkflowSubmitView.vue#L31)) filters parameters using `p.direction`, which is also not a field the serializer returns:
```js
const inputParams = () =>
  (workflow.value?.parameters ?? []).filter((p) => p.direction === 'input' || !p.direction)
```
`p.direction` is always `undefined`, so `!p.direction` is always `true` and the filter passes everything — this part is not the bug, but the field name is wrong regardless.

### Fix required (development team)
Either:
- **Option A:** Rename the serializer fields to `id` and `type` (adjust the model field references accordingly).
- **Option B:** Update `DynamicForm.vue` and `WorkflowSubmitView.vue` to use `param.parameter_type` and `param.parameter_id` everywhere.

### Verification after fix
1. Navigate to `/run/<workflow-id>` for a workflow with at least one input parameter.
2. Confirm each declared parameter renders the correct input component.
3. Complete and submit the form — confirm the job is created.

---

## BUG-02 — Login fails with 403 when a browser session cookie is present

### Severity: Critical (intermittent — blocks login for returning users)

### Observed behaviour
Logging in with a valid username and password sometimes returns a 403 Forbidden error, displayed to the user as "Request failed. Please try again." or "Invalid username or password." The Django server log shows:

```
Forbidden: /api/auth/login/
"POST /api/auth/login/ HTTP/1.1" 403 108
```

### Steps to reproduce
1. Log in successfully once via the UI. This creates a Django session cookie in the browser.
2. Log out (which clears the localStorage token but does **not** clear the session cookie).
3. Attempt to log in again with valid credentials.

**Actual:** Login returns 403.

**Expected:** Login returns 200 with a token and user object.

### When it does NOT reproduce
In a fresh private/incognito browser window (no session cookie present), login succeeds correctly.

### Root cause

**Django `SessionAuthentication` enforcing CSRF on POST requests when a session cookie is present.**

`settings.py` ([cloudgene_django/settings.py:144](../cloudgene_django/settings.py#L144)) lists `SessionAuthentication` first:
```python
'DEFAULT_AUTHENTICATION_CLASSES': [
    'rest_framework.authentication.SessionAuthentication',
    'rest_framework.authentication.TokenAuthentication',
],
```

When a session cookie exists in the browser, DRF's `SessionAuthentication.authenticate()` succeeds (it finds the session) and then calls `enforce_csrf()`. The Axios API client ([frontend/src/api/client.js](../frontend/src/api/client.js)) never attaches a CSRF token to requests, so the check fails and Django returns 403.

This is also the reason visiting `/admin/` (Django's built-in admin) and then navigating back to the SPA breaks login — the Django admin sets a session cookie.

### Fix required (development team)
The SPA is a token-based client and does not use Django sessions. Remove `SessionAuthentication` from `DEFAULT_AUTHENTICATION_CLASSES`, keeping only `TokenAuthentication`:
```python
'DEFAULT_AUTHENTICATION_CLASSES': [
    'rest_framework.authentication.TokenAuthentication',
],
```

### Verification after fix
1. Log in and out several times in the same browser session.
2. Open the Django admin in the same browser, then return to the SPA and log in.
3. Confirm login succeeds in all cases without 403 errors.

---

## BUG-03 — Password reset request returns 403 Forbidden

### Severity: High (blocks password recovery)

### Observed behaviour
Submitting the password reset form at `/reset-password` shows the error "Request failed. Please try again." The Django server log shows:

```
Forbidden: /api/auth/password-reset/
"POST /api/auth/password-reset/ HTTP/1.1" 403 108
```

### Steps to reproduce
1. In a browser that has previously visited the app (session cookie present).
2. Navigate to `/reset-password`.
3. Enter a valid registered email address and submit.

**Actual:** 403 Forbidden. No reset email is sent.

**Expected:** 200. "Password reset email sent."

### Root cause

Same root cause as BUG-02. `SessionAuthentication` is first in `DEFAULT_AUTHENTICATION_CLASSES` and enforces CSRF on all POST requests where a session cookie is present. The `PasswordResetView` uses `permission_classes = [AllowAny]` but that does not bypass CSRF enforcement — CSRF is enforced at the authentication layer, not the permission layer.

### Fix required (development team)
Same fix as BUG-02 — remove `SessionAuthentication` from `DEFAULT_AUTHENTICATION_CLASSES`.

### Verification after fix
1. Ensure a session cookie is present (log in and out, or visit `/admin/`).
2. Navigate to `/reset-password` and submit a valid email.
3. Confirm HTTP 200 is returned and no 403 error appears.
4. Confirm the reset token is created in the database (or email is written to the email file).

---

## BUG-04 — Logout redirects to /login instead of the home page

### Severity: Low (UX issue)

### Observed behaviour
Clicking **Logout** redirects the user to `/login` instead of the home page (`/`).

### Steps to reproduce
1. Log in as any user.
2. Open the user dropdown in the navbar.
3. Click **Logout**.

**Actual:** Browser navigates to `/login`.

**Expected:** Browser navigates to `/` (home page).

### Root cause

`AppNavbar.vue` ([frontend/src/components/layout/AppNavbar.vue:16](../frontend/src/components/layout/AppNavbar.vue#L16)):
```js
async function logout() {
  await auth.logout()
  router.push('/login')   // ← should be router.push('/')
}
```

### Fix required (development team)
Change `router.push('/login')` to `router.push('/')`.

### Verification after fix
1. Log in, then click Logout.
2. Confirm the browser lands on the home page (`/`), not `/login`.
3. Confirm the navbar shows the logged-out state (Login / Sign up links visible).
