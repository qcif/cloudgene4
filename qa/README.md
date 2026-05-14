# Cloudgene4 — QA Testing Guide

This directory contains the manual QA test plan for Cloudgene4. Tests cover both the REST API (via `curl`) and the Vue.js SPA (via browser/Selenium steps).

---

## Test Environment

### Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.10+ | Use the project venv (see below) |
| Node.js | 18+ | For the Vite dev server |
| Google Chrome | Latest stable | Selenium UI tests |
| ChromeDriver | Must match Chrome | Add to `$PATH` |
| Selenium (Python) | 4.x | `pip install selenium` inside venv |
| `curl` | Any | For API tests |

### Starting the servers

**Backend (Django):**
```bash
cd /path/to/cloudgene4
source venv/bin/activate
python manage.py runserver
# Listening at http://localhost:8000
```

**Frontend (Vite dev server):**
```bash
cd frontend/
npm install
npm run dev
# Listening at http://localhost:5173
```

For production-mode testing (frontend served by Django):
```bash
cd frontend/ && npm run build
# Django then serves frontend/dist/ at http://localhost:8000
```

---

## Base URLs

| Layer | URL |
|-------|-----|
| API base | `http://localhost:8000/api` |
| SPA (dev) | `http://localhost:5173` |
| SPA (prod) | `http://localhost:8000` |

All `curl` examples in this guide use `BASE=http://localhost:8000/api`. Set this in your shell:

```bash
export BASE=http://localhost:8000/api
export APP=http://localhost:5173
```

---

## Seed Data Setup

Run these steps once before testing to create the required test fixtures.

### 1. Create a regular user

```bash
curl -s -X POST "$BASE/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "testuser@example.com",
    "full_name": "Test User",
    "password": "Testpass1"
  }'
```

Then activate via the Django shell (bypasses email):
```bash
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.get(username='testuser')
u.is_active = True
u.activation_key = None
u.save()
print('activated')
"
```

### 2. Create an admin user

```bash
python manage.py createsuperuser \
  --username adminuser \
  --email admin@example.com
# Enter password: AdminPass1
```

### 3. Create a second regular user (for access-control tests)

```bash
curl -s -X POST "$BASE/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "otheruser",
    "email": "otheruser@example.com",
    "full_name": "Other User",
    "password": "Otherpass1"
  }'
# Activate same way as testuser
```

### 4. Obtain auth tokens (save for later tests)

```bash
# Regular user token
USER_TOKEN=$(curl -s -X POST "$BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "Testpass1"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Admin user token
ADMIN_TOKEN=$(curl -s -X POST "$BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "adminuser", "password": "AdminPass1"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['token'])")

echo "User:  $USER_TOKEN"
echo "Admin: $ADMIN_TOKEN"
```

---

## Test User Reference

| Username | Password | Role | Notes |
|----------|----------|------|-------|
| `testuser` | `Testpass1` | Regular user | Primary test account |
| `otheruser` | `Otherpass1` | Regular user | Used for ownership/access tests |
| `adminuser` | `AdminPass1` | Superuser/Admin | Full admin privileges |

---

## Conventions

### Test ID format
Each test case has a unique ID in the format `<MODULE>-<NN>`:

| Module | Prefix |
|--------|--------|
| Authentication | `AUTH` |
| Workflows | `WFLOW` |
| Jobs | `JOB` |
| Admin | `ADMIN` |

### Test case structure

Each test case follows this format:

> **TEST-ID — Title**
> - **Preconditions:** what must be true before the test
> - **Steps:** numbered actions to perform
> - **Expected result:** what success looks like

### API tests vs UI tests

Most features are covered by both an API test (using `curl`) and a UI test (step-by-step browser instructions). The API tests are lower-level and faster; the UI tests verify the full user experience including redirects, error messages in the interface, and state management.

### Pass/Fail notation

- ✅ **PASS** — actual result matches expected result
- ❌ **FAIL** — record the actual result, HTTP status, and any console errors

---

## File Index

| File | Scope |
|------|-------|
| [01-authentication.md](01-authentication.md) | Registration, activation, login, logout, password reset, route guards |
| [02-workflows.md](02-workflows.md) | Workflow listing, access control, category filter, submission form |
| [03-jobs.md](03-jobs.md) | Job submission, monitoring, cancellation, restart, downloads, queue |
| [04-admin.md](04-admin.md) | Dashboard, user management, settings, templates, logs |
