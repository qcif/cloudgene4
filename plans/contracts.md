# Contract Testing Implementation Plan

## Context

The Django + Vue 3 app has integration bugs caused by the API and web client being developed independently. The goal is to implement contracts as both a **design strategy** (OpenAPI schema as single source of truth) and a **testing strategy** (both sides validate against it), targeting 100% coverage of the client-API interface.

The approach follows CONTRACTS.md layers 1–3:
- Layer 1: OpenAPI schema via `drf_spectacular` (source of truth)
- Layer 2: Django `APITestCase` contract tests (backend validates correct request/response shapes)
- Layer 3: Vitest + AJV schema validation (frontend validates payload shape before sending)

Pact (layer 4) is deferred — layers 1–3 already catch the class of bug that caused the 400 error.

Two bugs already identified that the contracts will formally encode and prevent regressing:
1. `WorkflowSubmitView.inputParams()` uses `workflow.value?.parameters` (includes outputs) instead of `workflow.value?.inputs` (inputs only)
2. `WorkflowSubmitView` error handler reads `e.response?.data?.message` but backend returns `data.error` or `data.<fieldname>` — user always sees "Job submission failed." regardless of actual error

---

## Files to Create / Modify

**New files:**
- `accounts/contract_tests.py`
- `workflows/contract_tests.py`
- `jobs/contract_tests.py`
- `admin_panel/contract_tests.py`
- `frontend/vitest.config.js`
- `frontend/src/api/__tests__/auth.spec.js`
- `frontend/src/api/__tests__/jobs.spec.js`
- `frontend/src/api/__tests__/users.spec.js`
- `frontend/src/api/__tests__/admin.spec.js`
- `frontend/src/components/workflows/form/__tests__/DynamicForm.spec.js`
- `schema.yaml` (generated, committed as source of truth)

**Modified files:**
- `requirements.txt` — add `drf-spectacular`
- `cloudgene_django/settings.py` — configure `drf_spectacular`, set `DEFAULT_SCHEMA_CLASS`
- `cloudgene_django/urls.py` — add schema download endpoints
- `frontend/package.json` — add `vitest`, `@vitest/ui`, `ajv`, `ajv-formats`, `@vue/test-utils`, add `"test"` script
- `frontend/src/views/public/WorkflowSubmitView.vue` — fix `inputParams()` and error display

---

## Step-by-Step Implementation

### Step 1 — OpenAPI Schema (drf_spectacular)

Add to `requirements.txt`:
```
drf-spectacular==0.27.2
```

Add to `settings.py`:
```python
INSTALLED_APPS += ['drf_spectacular']
REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'drf_spectacular.openapi.AutoSchema'
SPECTACULAR_SETTINGS = {
    'TITLE': 'Cloudgene API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
```

Add to `cloudgene_django/urls.py` (before the SPA catch-all):
```python
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(), name='swagger-ui'),
```

Generate and commit the schema:
```bash
venv/bin/python manage.py spectacular --file schema.yaml
```

The `schema.yaml` is committed and becomes the source of truth that both the Django tests and Vue tests validate against.

---

### Step 2 — Django Contract Tests

Each app gets a `contract_tests.py` with `APITestCase` classes. They follow this pattern (per CONTRACTS.md): assert on **field names in errors**, not just status codes.

Run with: `venv/bin/python manage.py test accounts.contract_tests workflows.contract_tests jobs.contract_tests admin_panel.contract_tests`

#### `accounts/contract_tests.py`

**AuthContractTest** — `POST /api/auth/login/`
- valid credentials → 200, response has `token` and `user` keys
- missing `username` → 400, `username` in error
- missing `password` → 400, `password` in error
- wrong credentials → 400

**RegistrationContractTest** — `POST /api/auth/register/`
- valid payload → 201, response has `token`
- missing `username` → 400, `username` in error
- missing `email` → 400, `email` in error
- missing `password` → 400, `password` in error
- invalid username (too short, non-alphanumeric) → 400, `username` in error
- invalid email format → 400, `email` in error
- weak password → 400, `password` in error
- duplicate username → 400, `username` in error

**PasswordResetContractTest** — `POST /api/auth/password-reset/`
- valid email → 200
- missing email → 400, `email` in error
- unknown email → 400

**UserUpdateContractTest** — `PATCH /api/users/{id}/`
- valid partial update → 200
- user cannot update another user's record → 403
- admin can update any user → 200

**GroupContractTest** — `POST /api/groups/`
- valid `{name}` → 201, response has `id` and `name`
- missing `name` → 400, `name` in error
- non-admin → 403

#### `workflows/contract_tests.py`

**WorkflowListContractTest** — `GET /api/workflows/`
- response is paginated with `results` list
- each item has `id`, `name`, `status`, `parameters`, `inputs`, `outputs`
- non-public workflow hidden from unauthenticated user
- non-public workflow visible to admin

**WorkflowDetailContractTest** — `GET /api/workflows/{id}/`
- response has `id`, `name`, `description`, `version`, `parameters`, `inputs`, `outputs`
- `inputs` only contains params with `is_input=True`
- `outputs` only contains params with `is_output=True`
- non-accessible workflow → 404 for non-member user

**WorkflowSettingsContractTest** — `PATCH /api/admin/workflows/{id}/settings/`
- valid update → 200
- non-admin → 403
- `allowed_group_names` updates group access correctly

#### `jobs/contract_tests.py`

**JobSubmissionJSONContractTest** — `POST /api/jobs/` with JSON
- valid JSON payload → 201, response has `id`, `status`, `parameters`
- missing `workflow_id` → 400, `workflow_id` in error
- unknown `workflow_id` → 400, `workflow_id` in error
- inaccessible workflow → 400, `workflow_id` in error
- missing required parameter → 400, `parameters` in error (with param name in message)
- unauthenticated → 401

**JobSubmissionFormDataContractTest** — `POST /api/jobs/` with multipart
- valid FormData → 201
- `workflow_id` and `job_name` extracted correctly
- workflow params become `parameters` dict
- missing required param in FormData → 400, `parameters` in error

**JobActionContractTest** — cancel/restart
- `POST /api/jobs/{id}/cancel/` on pending job → 200
- cancel already-completed job → 400
- other user's job → 403

**JobResponseShapeTest**
- `GET /api/jobs/{id}/` response has all required fields: `id`, `name`, `status`, `parameters`, `steps`, `messages`, `downloads`, `can_cancel`, `can_restart`

#### `admin_panel/contract_tests.py`

**ServerSettingsContractTest** — `POST /api/admin/server-settings/`
- valid setting → 201
- missing `name` → 400, `name` in error
- missing `setting_type` → 400, `setting_type` in error
- non-admin → 403

**TemplateContractTest** — `PATCH /api/admin/templates/{id}/`
- valid content update → 200
- non-admin → 403

---

### Step 3 — Vue Contract Tests (Vitest + AJV)

#### Setup

Add to `frontend/package.json` devDependencies:
```json
"vitest": "^2.0.0",
"@vitest/ui": "^2.0.0",
"@vue/test-utils": "^2.4.0",
"ajv": "^8.17.1",
"ajv-formats": "^3.0.1",
"js-yaml": "^4.1.0"
```

Add script: `"test": "vitest run"`, `"test:ui": "vitest --ui"`

Create `frontend/vitest.config.js`:
```javascript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
```

Each test file mocks `@/api/client` using `vi.mock`, then calls the API function and asserts the mock was called with the correct method, URL, and payload shape. Schema component validation via AJV is applied for endpoints with complex payloads.

#### `frontend/src/api/__tests__/auth.spec.js`

- `login()` calls `POST /auth/login/` with `{username, password}` — validate shape against schema `LoginRequest`
- `register()` calls `POST /auth/register/` with full registration fields — validate against `UserRegistration` schema
- `requestPasswordReset()` calls `POST /auth/password-reset/` with `{email}`
- `confirmPasswordReset()` calls `POST /auth/password-reset-confirm/{token}/` with `{password}`

#### `frontend/src/api/__tests__/jobs.spec.js`

- `submitJob(formData)` calls `POST /jobs/` — asserts data is FormData instance (not JSON)
- Content-type detection: FormData triggers deletion of Content-Type header (verified via interceptor behaviour)

#### `frontend/src/api/__tests__/users.spec.js`

- `updateUser(id, data)` calls `PATCH /users/{id}/` with data object — validate shape
- `createGroup(data)` calls `POST /groups/` with `{name}` — validate shape

#### `frontend/src/api/__tests__/admin.spec.js`

- `updateWorkflowSettings(workflowId, data)` calls `PATCH /admin/workflows/{id}/settings/` — validate shape
- `updateTemplate(id, data)` calls `PATCH /admin/templates/{id}/` — validate shape

#### `frontend/src/components/workflows/form/__tests__/DynamicForm.spec.js`

This is the most important Vue test — it validates that `DynamicForm.onSubmit` correctly builds FormData for all parameter types.

Test cases (using `@vue/test-utils` mount):
- text param with value → FormData contains `param.id=value`
- number param with value → FormData contains the value as string
- checkbox param when false → FormData **still includes** `param.id=false` (non-empty, always submitted)
- checkbox param when true → FormData contains `param.id=true`
- file param with no File selected → FormData does **not** include the field (empty string filtered)
- file param with File object → FormData contains the File
- list param → FormData contains selected value
- `job_name` always present in FormData

---

### Step 4 — Fix the Two Identified Bugs

**Bug 1** — `WorkflowSubmitView.vue:32` — `inputParams()` filter:

Current (broken — `!p.direction` is always true, shows outputs too):
```javascript
const inputParams = () =>
  (workflow.value?.parameters ?? []).filter((p) => p.is_input || p.direction === 'input' || !p.direction)
```

Fix (use the dedicated `inputs` field the serializer already provides):
```javascript
const inputParams = () => workflow.value?.inputs ?? []
```

**Bug 2** — `WorkflowSubmitView.vue:43` — error display:

Current (looks for `data.message`, never set by backend):
```javascript
error.value = e.response?.data?.message || 'Job submission failed.'
```

Fix (handle both DRF field errors and the custom `error` key):
```javascript
const data = e.response?.data
if (data?.error) {
  error.value = data.error
} else if (data && typeof data === 'object') {
  const firstKey = Object.keys(data)[0]
  error.value = firstKey ? `${firstKey}: ${data[firstKey]}` : 'Job submission failed.'
} else {
  error.value = 'Job submission failed.'
}
```

---

## Verification

```bash
# Django contract tests
venv/bin/python manage.py test accounts.contract_tests workflows.contract_tests jobs.contract_tests admin_panel.contract_tests --verbosity=2

# All Django tests (regression check)
venv/bin/python manage.py test --verbosity=2

# Vue contract tests
cd frontend && npm test

# Regenerate schema (run after serializer changes)
venv/bin/python manage.py spectacular --file schema.yaml
```

The schema.yaml must be committed alongside serializer changes — it is the contract. CI should fail if the schema is stale (i.e., `spectacular --file /tmp/schema.yaml && diff schema.yaml /tmp/schema.yaml`).
