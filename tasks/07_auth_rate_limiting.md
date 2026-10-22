# 07 — Rate-limit the anonymous auth endpoints

## Overview

Cloudgene's anonymous endpoints (log in, register, request a password reset, activate, confirm
a reset) have no rate limiting at any layer. DRF has no throttle classes configured, and the
nginx configuration has no `limit_req`. The only protection is the per-account login lockout
(BE-AUTH-006), which does nothing against:

- **password spraying**: trying one common password against many usernames, so no single
  account reaches the lockout threshold;
- **mail flooding**: repeated `auth_register_create` or `auth_password_reset_create` calls
  that make the server send unlimited e-mail, to one victim address or to many. This costs
  mail-provider reputation and can get the sender blocklisted.

There is a second, quieter problem. Behind nginx, every request reaches Django from the proxy,
and DRF's `NUM_PROXIES` is unset. A per-address throttle added naively would therefore key
every client on the same address and throttle everyone together.

This task adds DRF throttles to those five operations, keyed on the real client address and,
for the mail-sending operations, on the target e-mail address. It backs them with a cache shared
by all gunicorn workers. It also adds an nginx `limit_req` outer limit for the same paths and
for `/django-admin/login/`, which DRF does not cover.

Source: spec/ISSUES.md SEC-04 (BE-AUTH-026, BE-AUTH-027, BE-ACCT-013, DEP-SEC-026, major).
SEC-09 (account lockout enables username enumeration and lockout-DoS) is related but needs a
decision on the lockout contract, so it stays in `tasks/todo.md`.

## Relevant spec

Read before starting:

- spec/constitution.md
- spec/backend/authentication.md — login and lockout (BE-AUTH-001..012), Throttling
  (BE-AUTH-026, -027), Known gaps.
- spec/backend/accounts.md — register, activate, reset (BE-ACCT-008..016; BE-ACCT-013 same
  answer for any e-mail).
- spec/backend/api-contract.md — error envelope; `429 throttled` and the `Retry-After` header
  rows.
- spec/deployment/api-contract.md — proxy headers (DEP-API-023: the one permitted use of
  `X-Forwarded-For`).
- spec/deployment/security-hardening.md — DEP-SEC-026 (nginx interim limit).
- spec/deployment/reverse-proxy.md — where nginx directives are specified.
- spec/deployment/environment-config.md — inventory of env variables (any new variable is added
  there and to `deploy/cloudgene.env.example`).
- spec/frontend/auth-views.md — how login/register/reset views show errors.
- spec/backend/tests.md, spec/frontend/tests.md, spec/deployment/tests.md.

Depends on task 04 only loosely. Once gunicorn listens only on a socket that steps cannot
reach, a workflow step can no longer bypass nginx to forge `X-Forwarded-For`. This task does not
need 04 to land first.

## Design

### Throttles

DRF scoped throttles on POST only, on the five operations. The rates below are defaults; see
"Configuration":

| Operation | Key | Default rate | Why |
|---|---|---|---|
| `auth_login_create` | client address | `10/min` and `100/hour` | Spraying; lockout still covers the single-account case |
| `auth_register_create` | client address | `5/hour` | Each call sends mail when activation is on |
| `auth_password_reset_create` | client address | `5/hour` | Sends mail |
| `auth_password_reset_create` | target e-mail (normalised, hashed in the key) | `3/hour` | Stops flooding one victim from many addresses |
| `auth_activate_create` | client address | `30/hour` | Keys are unguessable; this only bounds noise |
| `auth_password_reset_confirm` | client address | `30/hour` | Same |

Rules:

- A throttled request gets **429**, code `throttled`, header `Retry-After: <seconds>`, and a
  readable message, e.g. `Too many requests. Try again in N minute(s).` (rounded up). It must
  not be DRF's default `Request was throttled. Expected available in 42 seconds.` Check that
  `core/exceptions.py` keeps the `Retry-After` header that DRF's `Throttled` sets.
- The per-e-mail reset throttle MUST NOT reveal whether the address is registered
  (BE-ACCT-013). It applies to every submitted address, registered or not, and its 429 is the
  same as the per-address 429. Throttling a reset for an unknown address is fine.
- Successful and failed attempts both count. A throttle counts requests, not failures.
- Login lockout (BE-AUTH-006..009) is unchanged and independent. When both apply, the
  throttle is checked first (DRF checks throttles before the view runs), so a throttled
  request does not count towards the account's `login_attempts`. State this in BE-AUTH-026.
- Authenticated endpoints are not throttled in this task.

### Client address (BE-AUTH-027)

- `REST_FRAMEWORK['NUM_PROXIES']` from a new env variable `DJANGO_NUM_PROXIES`, default `0`
  (development: use `REMOTE_ADDR`). The Ansible env template and `deploy/cloudgene.env.example`
  set it to `1`. With `1`, DRF uses the right-most `X-Forwarded-For` entry, which nginx's
  `$proxy_add_x_forwarded_for` sets to the real `$remote_addr`. A client-supplied
  `X-Forwarded-For` therefore cannot change the key.
- A `check --deploy` warning when `DEBUG` is off and `DJANGO_NUM_PROXIES` is `0` (next free
  `cloudgene.W0xx`). Behind a proxy that setting throttles everyone together.
- The `DJANGO_` prefix is already covered by task 03's step-environment strip.

### Shared cache

DRF throttles store their history in Django's cache. There is no `CACHES` setting today, so each
gunicorn worker has its own `LocMemCache`. Limits would multiply by the worker count and reset on
every worker recycle (`max_requests`). Configure a shared cache:

- Default: `DatabaseCache` (table `cloudgene_cache`). It works for SQLite and PostgreSQL and
  across hosts. Create the table from a migration (a `RunPython` that calls
  `createcachetable`), so no new deploy step is needed and the test runner gets it
  automatically.
- Use it as the `default` cache unless something else already relies on `default` being local
  (grep for `cache.` usage first). If it does, use a named `throttle` cache and point the
  throttle classes at it.
- The cache is not atomic under concurrency. A burst can slightly exceed a limit. That is
  acceptable; say so in the spec.

### Configuration

Rates live in Django settings (`DEFAULT_THROTTLE_RATES`), each overridable by an env variable
`DJANGO_THROTTLE_<SCOPE>` (e.g. `DJANGO_THROTTLE_LOGIN=10/min`). The value `off` disables that
scope. Settings errors in these values name the variable (do not repeat DEP-13's unnamed
`ValueError`). Not in `settings.yaml`. Rates are operator settings, not admin-UI settings. See
Open questions.

The e2e harness logs in many times per run. Its stack env MUST set every scope to a high rate
or `off` (`e2e/stack.py`), except where a test deliberately exercises throttling.

### nginx outer limit (DEP-SEC-026)

In `deploy/nginx.conf.example` and the Ansible template
(`deploy/ansible/roles/nginx/templates/cloudgene.conf.j2`): a `limit_req_zone` keyed on
`$binary_remote_addr`, applied with a modest burst to the auth paths listed in DEP-SEC-026 and
`/django-admin/login/`, `limit_req_status 429`. It is looser than the DRF limits, for example
`30r/m burst=20 nodelay`, so DRF's envelope is what users normally see. nginx's own 429 page is
HTML (API-17). Accept that for the outer limit.

### Frontend

The login, register and both reset views already show the envelope message. Check that a 429
`throttled` displays the message and does not leave the submit button disabled or spinning.
Fix it if it does.

### Interfaces

- No new operation. `throttled` (429) becomes a documented error on the five operations
  (Notable errors, marked as taken from code per Article 5.3). `schema.yaml` errors are
  `default: Error`, so the schema is unchanged. Confirm with
  `python manage.py spectacular --file schema.yaml --validate`.
- New env variables `DJANGO_NUM_PROXIES`, `DJANGO_THROTTLE_*`; new cache table; nginx zone.

## Steps

1. **Settings**: `CACHES`, `NUM_PROXIES`, `DEFAULT_THROTTLE_RATES` with env overrides.
2. **Cache table migration** (in `core` or `accounts`).
3. **Throttle classes** (e.g. `accounts/throttles.py`): per-address scoped throttles, the
   per-e-mail reset throttle, the custom message. Attach them to the five views in
   `accounts/views.py`.
4. **Deploy check** for `NUM_PROXIES` behind a proxy.
5. **e2e harness env**: disable or raise rates in `e2e/stack.py`.
6. **nginx**: example config and Ansible template. Env example and Ansible env template:
   `DJANGO_NUM_PROXIES=1`.
7. **Backend unit tests**, at the planned names in spec/backend/authentication.md:
   - `accounts/tests.py::ThrottleTest::test_login_throttled_per_address`: the 11th login in a
     minute from one address gets 429 `throttled` with `Retry-After`; another address is not
     affected.
   - `accounts/tests.py::ThrottleTest::test_throttle_keys_on_rightmost_forwarded_address`: with
     `NUM_PROXIES=1`, changing the left part of `X-Forwarded-For` does not reset the count, and a
     different right-most entry is a different key. With `NUM_PROXIES=0`, `REMOTE_ADDR` is used.
   - Register and reset-request throttles per address. The per-e-mail reset throttle trips from
     several addresses for one e-mail, and gives an identical 429 for registered and unknown
     addresses.
   - Activate and reset-confirm throttles.
   - A throttled login does not increment `login_attempts`.
   - `DJANGO_THROTTLE_LOGIN=off` disables that scope; a malformed value fails start-up with a
     message naming the variable.
   - The throttle survives across two separate client instances, i.e. it uses the shared cache
     and not per-process memory. Assert the backend is `DatabaseCache`.
   - `core/tests/test_deploy.py`: the new `NUM_PROXIES` deploy warning.
   - Contract: the 429 body validates as the error envelope (existing contract test module for
     auth, `accounts/test_contracts.py`).
8. **Frontend unit tests** (vitest): the login view shows the `throttled` message and re-enables
   submit. Same for the reset-request view.
9. **E2E** (Article 7.3): if the harness can boot a stack with custom env for one test, add a
   serial test in `e2e/tests/test_auth.py` with `DJANGO_THROTTLE_LOGIN=3/min`. It fails to log in
   4 times, then checks that the UI shows the throttle message. If the harness cannot do that
   yet, list the test as `(planned)` with a Known gap (Article 6.2) and add a `tasks/todo.md`
   item for the harness capability.
10. **Config tests**: in `core/tests/test_deploy_files.py` (planned home), `NginxExampleTest`
    asserts the `limit_req` zone covers the DEP-SEC-026 paths. `EnvContractTest`, if present,
    picks up the new variables.
11. **Spec updates** (same change set):
    - spec/backend/authentication.md: BE-AUTH-026 (now MUST, rates, keys, order relative to
      lockout, custom message) and BE-AUTH-027 lose `(planned)`. Remove Known gaps. Add
      Acceptance tests rows.
    - spec/backend/accounts.md: the per-e-mail reset throttle and its BE-ACCT-013 constraint.
    - spec/backend/api-contract.md: `429 throttled` on the five operations; the `throttled` row
      no longer says "no throttles are configured today"; `Retry-After` row covers `throttled`.
    - spec/deployment/environment-config.md: new variables. spec/deployment/security-hardening.md
      and reverse-proxy.md: DEP-SEC-026 met; directives. spec/deployment/api-contract.md:
      DEP-API-023 now has a user.
    - spec/frontend/auth-views.md: 429 display.
    - Each section's tests.md: traceability rows and counts.
    - spec/ISSUES.md: drop SEC-04.
12. **User docs**: `docs/DEPLOYMENT.md` (env variables, nginx zone, the createcachetable
    migration); `docs/ADMIN_GUIDE.md` if it describes the lockout.
13. Run the unit and e2e suites (`/tests` skill) and flake8. Ask the user before deploying.

## Acceptance criteria

- [ ] The five anonymous auth operations answer 429 `throttled` with `Retry-After` and a
      readable message once their per-address rate is exceeded.
- [ ] Password-reset requests are also limited per target e-mail, without revealing whether
      the address is registered.
- [ ] Behind nginx, throttles key on the real client address. A forged `X-Forwarded-For` prefix
      does not change the key, and `check --deploy` warns if `NUM_PROXIES` is unset in
      production.
- [ ] Throttle state is shared by all gunicorn workers (database cache).
- [ ] nginx applies an outer `limit_req` to the auth paths and `/django-admin/login/`.
- [ ] Rates are configurable and can be disabled per scope via env; the e2e harness is not
      throttled.
- [ ] `schema.yaml` is unchanged.
- [ ] Backend, frontend and config tests cover the above; e2e covered or planned with a gap;
      suites pass; flake8 is clean.
- [ ] Spec and docs updated as in steps 11–12.

## Open questions

Implement the stated default and copy the question into the relevant spec's Open questions.

- **Rates in `settings.yaml`?** Default: no, they are env/operator settings. Moving them to
  `settings.yaml` would make them admin-editable without a restart.
- **Authenticated endpoints.** Should job submission or the API generally get a per-user
  throttle? Default: no; the queue limit (`max_queue_size`) already bounds submissions.
- **Lockout contract (SEC-09).** With per-address throttling in place, should the per-account
  lockout be keyed on account + address, or replaced, so that it cannot be used to lock out a
  known user? This is a separate task, tracked in `tasks/todo.md`.
