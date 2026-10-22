---
name: tests
description: Run the unit (Django + vitest) and Playwright E2E test suites
---

Run this repo's tests. "$1" may name a suite (`unit`, `e2e`, `all`), an
app/module, or a test name; otherwise pick the smallest suite that covers
the change, then widen.

## Entry point

`scripts/test.sh` runs everything, using `./venv/bin/python`:

```sh
scripts/test.sh unit             # check + makemigrations --check + manage.py test + vitest (SQLite)
scripts/test.sh unit --postgres  # same, Django tests against $TEST_DATABASE_URL
scripts/test.sh e2e [pytest args]
scripts/test.sh all              # unit, then e2e (default)
```

`--postgres` needs a running server; default URL is
`postgres://cloudgene:cloudgene@127.0.0.1:5432/cloudgene`. Nothing starts it.

## Narrower runs

Django (unittest; apps `accounts`, `admin_panel`, `core`, `jobs`, `workflows`):

```sh
venv/bin/python manage.py test jobs
venv/bin/python manage.py test jobs.tests.<module>.<Class>.<test_method>
```

Frontend (vitest):

```sh
cd frontend
npx vitest run [path-or-pattern]
```

E2E (Playwright via pytest; each run boots its own stack under
`e2e/.artifacts/`, so it never touches the dev DB or `home/`):

```sh
venv/bin/python -m pytest e2e -k deep_links          # subset
venv/bin/python -m pytest e2e -n 4 -m "not serial"   # parallel
venv/bin/python -m pytest e2e -m serial              # global-state tests, never with -n
E2E_SKIP_BUILD=1 venv/bin/python -m pytest e2e ...   # reuse existing SPA bundle
```

## Rules

- **Never** `pip install -r e2e/requirements.txt` or `playwright install`.
  `playwright==1.56.0` is pinned to match the installed Chromium; drifting
  breaks browser launch.
- Nextflow must be on `PATH` for E2E (or set `E2E_NEXTFLOW`).
- After changing an API view or serializer, regenerate the schema or the
  staleness test fails:
  `venv/bin/python manage.py spectacular --file schema.yaml --validate`.
- After model changes, `makemigrations --check` fails until migrations are
  created.
- After editing Python, run `/home/cameron/.local/envs/claude/bin/flake8`
  on the changed files.

## When E2E fails

Start with `e2e/.artifacts/summary.txt` (one line per test, first error,
trace path). Then:

- Traces: `e2e/.artifacts/playwright/<test-id>/trace.zip`
  (`venv/bin/python -m playwright show-trace <zip>`).
- Server/worker/build logs: `e2e/.artifacts/stack-<worker>/logs/`.
- Stack home, mail outbox, DB: `e2e/.artifacts/stack-<worker>/`.

More detail in `e2e/README.md`. Report failures with the actual output;
don't mark xfail or skip tests to get green without asking.
