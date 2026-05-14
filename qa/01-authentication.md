# Authentication Tests

Tests for user registration, account activation, login, logout, password reset, and route access guards.

Assumes `BASE` and `APP` environment variables are set as described in [README.md](README.md).

---

## 1. Registration

### AUTH-01 — Successful registration

- **Preconditions:** Username `newuser` does not exist in the database.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/auth/register/" \
       -H "Content-Type: application/json" \
       -d '{
         "username": "newuser",
         "email": "newuser@example.com",
         "full_name": "New User",
         "password": "Newpass1"
       }'
     ```
- **Expected result:** HTTP 201. Response body contains `user.username = "newuser"` and `user.is_active = false`. The `message` field reads `"Registration successful. Please check your email for activation instructions."` The user exists in the database with `is_active=False` and a non-null `activation_key`.

---

### AUTH-02 — Registration: username too short

- **Preconditions:** None.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/auth/register/" \
       -H "Content-Type: application/json" \
       -d '{"username": "abc", "email": "abc@x.com", "full_name": "Abc", "password": "Testpass1"}'
     ```
- **Expected result:** HTTP 400. Response `message` contains `"The username must contain at least four characters."` No user is created.

---

### AUTH-03 — Registration: non-alphanumeric username

- **Preconditions:** None.
- **Steps (API):**
  1. Send with username `"test user"` (space) or `"test-user"` (hyphen):
     ```bash
     curl -s -X POST "$BASE/auth/register/" \
       -H "Content-Type: application/json" \
       -d '{"username": "test-user", "email": "t@x.com", "full_name": "T", "password": "Testpass1"}'
     ```
- **Expected result:** HTTP 400. Response `message` contains `"Your username is not valid. Only characters A-Z, a-z and digits 0-9 are acceptable."`

---

### AUTH-04 — Registration: password too short

- **Preconditions:** None.
- **Steps (API):**
  1. Send with password `"Ab1"` (only 3 chars):
     ```bash
     curl -s -X POST "$BASE/auth/register/" \
       -H "Content-Type: application/json" \
       -d '{"username": "newuser2", "email": "n2@x.com", "full_name": "N2", "password": "Ab1"}'
     ```
- **Expected result:** HTTP 400. Response `message` contains `"Password must contain at least six characters!"`

---

### AUTH-05 — Registration: password missing digit

- **Preconditions:** None.
- **Steps (API):**
  1. Send with password `"Testpass"` (no digit):
     ```bash
     curl -s -X POST "$BASE/auth/register/" \
       -H "Content-Type: application/json" \
       -d '{"username": "newuser3", "email": "n3@x.com", "full_name": "N3", "password": "Testpass"}'
     ```
- **Expected result:** HTTP 400. Response `message` contains `"Password must contain at least one number (0-9)!"`

---

### AUTH-06 — Registration: password missing uppercase

- **Preconditions:** None.
- **Steps (API):**
  1. Send with password `"testpass1"`:
     ```bash
     curl -s -X POST "$BASE/auth/register/" \
       -H "Content-Type: application/json" \
       -d '{"username": "newuser4", "email": "n4@x.com", "full_name": "N4", "password": "testpass1"}'
     ```
- **Expected result:** HTTP 400. Response `message` contains `"Password must contain at least one uppercase letter (A-Z)!"`

---

### AUTH-07 — Registration: password missing lowercase

- **Preconditions:** None.
- **Steps (API):**
  1. Send with password `"TESTPASS1"`:
     ```bash
     curl -s -X POST "$BASE/auth/register/" \
       -H "Content-Type: application/json" \
       -d '{"username": "newuser5", "email": "n5@x.com", "full_name": "N5", "password": "TESTPASS1"}'
     ```
- **Expected result:** HTTP 400. Response `message` contains `"Password must contain at least one lowercase letter (a-z)!"`

---

### AUTH-08 — Registration: password confirmation mismatch

- **Preconditions:** None.
- **Steps (API):**
  1. Send with `password = "Testpass1"` and `password_confirm = "Different1"`:
     ```bash
     curl -s -X POST "$BASE/auth/register/" \
       -H "Content-Type: application/json" \
       -d '{
         "username": "newuser6",
         "email": "n6@x.com",
         "full_name": "N6",
         "password": "Testpass1",
         "password_confirm": "Different1"
       }'
     ```
- **Expected result:** HTTP 400. Response `message` contains `"Please check your passwords."`

---

### AUTH-09 — Registration: duplicate username

- **Preconditions:** User `testuser` already exists (from seed data).
- **Steps (API):**
  1. Attempt to register with `username = "testuser"`:
     ```bash
     curl -s -X POST "$BASE/auth/register/" \
       -H "Content-Type: application/json" \
       -d '{"username": "testuser", "email": "unique@x.com", "full_name": "T", "password": "Testpass1"}'
     ```
- **Expected result:** HTTP 400. Response `message` indicates the username is already taken.

---

### AUTH-10 — Registration: duplicate email

- **Preconditions:** User with email `testuser@example.com` already exists.
- **Steps (API):**
  1. Attempt to register with `email = "testuser@example.com"` but a different username:
     ```bash
     curl -s -X POST "$BASE/auth/register/" \
       -H "Content-Type: application/json" \
       -d '{"username": "uniqueuser", "email": "testuser@example.com", "full_name": "T", "password": "Testpass1"}'
     ```
- **Expected result:** HTTP 400. Response indicates email is already in use.

---

### AUTH-11 — Registration: missing full_name

- **Preconditions:** None.
- **Steps (API):**
  1. Send without `full_name`:
     ```bash
     curl -s -X POST "$BASE/auth/register/" \
       -H "Content-Type: application/json" \
       -d '{"username": "newuser7", "email": "n7@x.com", "password": "Testpass1"}'
     ```
- **Expected result:** HTTP 400. Response indicates `full_name` is required.

---

### AUTH-12 — Registration UI flow

- **Preconditions:** App is running. Username `uireguser` does not exist.
- **Steps (UI):**
  1. Navigate to `$APP/register`.
  2. Fill in: Username = `uireguser`, Email = `ui@example.com`, Full Name = `UI Reg User`, Password = `Regpass1`.
  3. Click the **Register** button.
- **Expected result:** A success message is shown (e.g. "Registration successful. Please check your email for activation instructions."). The user is not yet logged in.

---

## 2. Account Activation

### AUTH-13 — Valid activation key activates account

- **Preconditions:** A user was registered but not yet activated. Obtain their `activation_key` from the database:
  ```bash
  python manage.py shell -c "
  from django.contrib.auth import get_user_model
  User = get_user_model()
  u = User.objects.get(username='newuser')
  print(u.activation_key)
  "
  ```
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/auth/activate/<activation_key>/"
     ```
- **Expected result:** HTTP 200. Response `message` = `"Account activated successfully"`. In the database, `user.is_active = True` and `user.activation_key = null`.

---

### AUTH-14 — Invalid activation key

- **Preconditions:** None.
- **Steps (API):**
  1. Send with a fabricated key:
     ```bash
     curl -s "$BASE/auth/activate/not-a-real-key-00000000/"
     ```
- **Expected result:** HTTP 400. Response `message` = `"Invalid activation key"`.

---

### AUTH-15 — Already-activated key is rejected

- **Preconditions:** User `testuser` is already active (`is_active = True`, `activation_key = null`).
- **Steps (API):**
  1. Attempt to activate with any key (or the now-nulled key):
     ```bash
     curl -s "$BASE/auth/activate/any-key/"
     ```
- **Expected result:** HTTP 400. Response `message` = `"Invalid activation key"` (no match because key is null).

---

### AUTH-16 — Inactive user cannot log in

- **Preconditions:** A registered but not-yet-activated user exists (e.g. `newuser` from AUTH-01).
- **Steps (API):**
  1. Attempt to log in:
     ```bash
     curl -s -X POST "$BASE/auth/login/" \
       -H "Content-Type: application/json" \
       -d '{"username": "newuser", "password": "Newpass1"}'
     ```
- **Expected result:** HTTP 400. Response `message` = `"User account is disabled."`

---

## 3. Login

### AUTH-17 — Successful login returns token and user object

- **Preconditions:** `testuser` exists and is active.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/auth/login/" \
       -H "Content-Type: application/json" \
       -d '{"username": "testuser", "password": "Testpass1"}'
     ```
- **Expected result:** HTTP 200. Response body contains:
  - `token` — a non-empty string
  - `user.username` = `"testuser"`
  - `user.is_active` = `true`
  - `user.is_admin` = `false`
  - `message` = `"Login successful"`

---

### AUTH-18 — Login: wrong password

- **Preconditions:** `testuser` exists and is active.
- **Steps (API):**
  1. Send with wrong password:
     ```bash
     curl -s -X POST "$BASE/auth/login/" \
       -H "Content-Type: application/json" \
       -d '{"username": "testuser", "password": "Wrongpass9"}'
     ```
- **Expected result:** HTTP 400. Response `message` = `"Invalid username or password."`

---

### AUTH-19 — Login: missing fields

- **Preconditions:** None.
- **Steps (API):**
  1. Send with no password:
     ```bash
     curl -s -X POST "$BASE/auth/login/" \
       -H "Content-Type: application/json" \
       -d '{"username": "testuser"}'
     ```
- **Expected result:** HTTP 400. Response `message` contains `"Must include username and password."`

---

### AUTH-20 — Admin login returns is_admin = true

- **Preconditions:** `adminuser` exists and is a superuser.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/auth/login/" \
       -H "Content-Type: application/json" \
       -d '{"username": "adminuser", "password": "AdminPass1"}'
     ```
- **Expected result:** HTTP 200. Response `user.is_admin = true`.

---

### AUTH-21 — Login UI: token persisted and redirect to /jobs

- **Preconditions:** `testuser` is active. App is running.
- **Steps (UI):**
  1. Navigate to `$APP/login`.
  2. Enter Username = `testuser`, Password = `Testpass1`.
  3. Click **Login**.
- **Expected result:**
  - Browser redirects to `$APP/jobs`.
  - Browser `localStorage` contains an entry for the auth token (open DevTools → Application → Local Storage).
  - The navbar shows the logged-in state (e.g. username or profile link visible).

---

### AUTH-22 — Unauthenticated API request is rejected

- **Preconditions:** None.
- **Steps (API):**
  1. Send a request to a protected endpoint without a token:
     ```bash
     curl -s "$BASE/jobs/"
     ```
- **Expected result:** HTTP 401 or 403. No job data returned.

---

### AUTH-23 — Authenticated API request succeeds

- **Preconditions:** `USER_TOKEN` is set.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/jobs/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 200. Response is a JSON list (possibly empty).

---

## 4. Logout

### AUTH-24 — Logout clears session

- **Preconditions:** `USER_TOKEN` is set (user is logged in).
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/auth/logout/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 200. Response `message` = `"Logout successful"`.

---

### AUTH-25 — Logout without auth is rejected

- **Preconditions:** None.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/auth/logout/"
     ```
- **Expected result:** HTTP 401 or 403. Logout is not processed.

---

### AUTH-26 — Logout UI: navbar returns to logged-out state

- **Preconditions:** `testuser` is logged in via the UI (AUTH-21 completed).
- **Steps (UI):**
  1. With the browser still at `$APP/jobs`, find the user menu or logout button in the navbar.
  2. Click **Logout**.
- **Expected result:**
  - Browser redirects to `$APP/login` (or the homepage).
  - `localStorage` auth token is cleared (verify in DevTools).
  - The navbar shows the logged-out state (Login/Register links visible).

---

### AUTH-27 — Accessing a protected route after logout redirects to /login

- **Preconditions:** User has just logged out (AUTH-26).
- **Steps (UI):**
  1. Manually navigate to `$APP/jobs` in the address bar.
- **Expected result:** Browser is redirected to `$APP/login`. The original destination may be preserved as a `?next=` query parameter.

---

## 5. Password Reset

### AUTH-28 — Password reset: unknown email

- **Preconditions:** Email `nobody@example.com` is not in the database.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/auth/password-reset/" \
       -H "Content-Type: application/json" \
       -d '{"email": "nobody@example.com"}'
     ```
- **Expected result:** HTTP 400. Response `message` contains `"No user found with this email address."`

---

### AUTH-29 — Password reset: valid email queues reset token

- **Preconditions:** `testuser` exists with `email = "testuser@example.com"`.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/auth/password-reset/" \
       -H "Content-Type: application/json" \
       -d '{"email": "testuser@example.com"}'
     ```
- **Expected result:** HTTP 200. Response `message` = `"Password reset email sent"`. In the database, `user.password_reset_token` is a non-null UUID and `user.password_reset_expires` is ~24 hours from now.

---

### AUTH-30 — Password reset confirm: valid token and valid new password

- **Preconditions:** `testuser` has a valid `password_reset_token` (from AUTH-29). Retrieve the token:
  ```bash
  python manage.py shell -c "
  from django.contrib.auth import get_user_model
  u = get_user_model().objects.get(username='testuser')
  print(u.password_reset_token)
  "
  ```
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/auth/password-reset-confirm/<token>/" \
       -H "Content-Type: application/json" \
       -d '{"password": "Newpass99"}'
     ```
- **Expected result:** HTTP 200. Response `message` = `"Password reset successful"`. `user.password_reset_token` and `user.password_reset_expires` are cleared to null.

---

### AUTH-31 — Password reset confirm: old password no longer works

- **Preconditions:** AUTH-30 completed successfully. Old password was `Testpass1`, new is `Newpass99`.
- **Steps (API):**
  1. Attempt login with old password:
     ```bash
     curl -s -X POST "$BASE/auth/login/" \
       -H "Content-Type: application/json" \
       -d '{"username": "testuser", "password": "Testpass1"}'
     ```
  2. Attempt login with new password:
     ```bash
     curl -s -X POST "$BASE/auth/login/" \
       -H "Content-Type: application/json" \
       -d '{"username": "testuser", "password": "Newpass99"}'
     ```
- **Expected result:** Step 1 returns HTTP 400. Step 2 returns HTTP 200 with a token.

> **Note:** Reset `testuser`'s password back to `Testpass1` after this test to keep subsequent tests consistent.

---

### AUTH-32 — Password reset confirm: invalid token

- **Preconditions:** None.
- **Steps (API):**
  1. Send with a fabricated token:
     ```bash
     curl -s -X POST "$BASE/auth/password-reset-confirm/00000000-0000-0000-0000-000000000000/" \
       -H "Content-Type: application/json" \
       -d '{"password": "Newpass99"}'
     ```
- **Expected result:** HTTP 400. Response `message` = `"Invalid or expired reset link."`

---

### AUTH-33 — Password reset confirm: expired token

- **Preconditions:** `testuser` has a `password_reset_token`. Manually expire it:
  ```bash
  python manage.py shell -c "
  from django.contrib.auth import get_user_model
  from django.utils import timezone
  import datetime
  u = get_user_model().objects.get(username='testuser')
  u.password_reset_expires = timezone.now() - datetime.timedelta(hours=25)
  u.save()
  print('expired:', u.password_reset_token)
  "
  ```
- **Steps (API):**
  1. Send with the now-expired token and a valid new password:
     ```bash
     curl -s -X POST "$BASE/auth/password-reset-confirm/<token>/" \
       -H "Content-Type: application/json" \
       -d '{"password": "Newpass99"}'
     ```
- **Expected result:** HTTP 400. Response `message` = `"This reset link has expired."`

---

### AUTH-34 — Password reset confirm: weak new password rejected

- **Preconditions:** `testuser` has a valid (non-expired) `password_reset_token`.
- **Steps (API):**
  1. Send with password `"weak"` (too short, missing uppercase and digit):
     ```bash
     curl -s -X POST "$BASE/auth/password-reset-confirm/<token>/" \
       -H "Content-Type: application/json" \
       -d '{"password": "weak"}'
     ```
- **Expected result:** HTTP 400. Response `message` contains a password validation error (e.g. `"Password must contain at least six characters!"`).

---

### AUTH-35 — Password reset UI flow

- **Preconditions:** `testuser` exists and is active. App is running. Email backend is configured (or check DB for token).
- **Steps (UI):**
  1. Navigate to `$APP/reset-password`.
  2. Enter email `testuser@example.com` and submit.
  3. Retrieve the reset token from the database.
  4. Navigate to `$APP/recover/<token>`.
  5. Enter a new password `Newreset9` (and confirm if the form requires it), then submit.
- **Expected result:**
  - Step 2: A success message appears (e.g. "Password reset email sent").
  - Step 5: A success message appears and the form is cleared. The user can now log in with `Newreset9`.

---

## 6. Route Guards

### AUTH-36 — Unauthenticated access to /profile redirects to /login

- **Preconditions:** No user is logged in (clear localStorage or use a private browser window).
- **Steps (UI):**
  1. Navigate directly to `$APP/profile`.
- **Expected result:** Browser redirects to `$APP/login`. The URL may include `?next=%2Fprofile`.

---

### AUTH-37 — Unauthenticated access to /jobs redirects to /login

- **Preconditions:** No user is logged in.
- **Steps (UI):**
  1. Navigate directly to `$APP/jobs`.
- **Expected result:** Browser redirects to `$APP/login`.

---

### AUTH-38 — Unauthenticated access to /run/:id redirects to /login

- **Preconditions:** No user is logged in.
- **Steps (UI):**
  1. Navigate directly to `$APP/run/1` (any workflow ID).
- **Expected result:** Browser redirects to `$APP/login`.

---

### AUTH-39 — Non-admin access to /admin/* redirects away

- **Preconditions:** `testuser` (non-admin) is logged in.
- **Steps (UI):**
  1. Navigate directly to `$APP/admin`.
- **Expected result:** Browser redirects to `$APP/` (homepage) or another non-admin route. The admin dashboard is not shown.

---

### AUTH-40 — Admin access to /admin/* is allowed

- **Preconditions:** `adminuser` is logged in.
- **Steps (UI):**
  1. Navigate to `$APP/admin`.
- **Expected result:** The Admin Dashboard view is displayed. No redirect occurs.

---

### AUTH-41 — 401 response from API triggers logout and redirect

- **Preconditions:** `testuser` is logged in via the UI. Their token is in `localStorage`.
- **Steps (UI):**
  1. Manually delete or corrupt the auth token in `localStorage` (DevTools → Application → Local Storage → delete the token value).
  2. In the browser, trigger any API-backed action (e.g. navigate to `$APP/jobs` or click Refresh).
- **Expected result:** The app detects the 401 response from the API, clears the auth state, and redirects to `$APP/login`.
