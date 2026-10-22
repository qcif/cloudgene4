# 05 — Live job progress: make status changes visible to the poller

## Overview

While a job runs, the job detail page polls `jobs_status_retrieve` (`getJobStatus`). The poller
backs off when nothing changes: 2 s, then ×1.5 per unchanged tick, capped at 10 s. It resets to
2 s on a change (FE-JDET-008). The view decides "changed" by comparing only `updated_at`
(`refreshStatus()` in `frontend/src/views/public/JobDetailView.vue`).

The worker, however, records most progress without touching `Job.updated_at`:

- `current_step` is set with `QuerySet.update()`, which bypasses `auto_now`;
- step `processes` are saved on the `JobStep` row (`update_fields=['processes']`);
- step state changes are saved on `JobStep` rows;
- messages are inserted with `bulk_create` on `JobMessage`.

`updated_at` changes only on claim and finish. During a run, every tick looks unchanged, so the
delay climbs to 10 s and stays there. Users see progress (task counts, step changes, new
messages) up to 10 s late instead of 2 s. A waiting job's `queue_position` also changes
without any write to the job row, so the same lag applies in the queue.

This task fixes both halves, as the spec already requires. The backend keeps `updated_at` truthful
(BE-QUEUE-028), and the frontend detects any change in what it displays rather than relying on one
field (FE-JDET-010). Either half alone would mostly hide the problem. Both are needed because
`updated_at` is part of the public contract, and because `queue_position` is derived, so no
row write can track it.

Source: spec/ISSUES.md JOB-01 (BE-QUEUE-028, FE-JDET-010, major).

## Relevant spec

Read before starting:

- spec/constitution.md
- spec/backend/job-queue-worker.md — BE-QUEUE-028 and the worker's progress writes; Known gaps.
- spec/backend/job-progress-outputs.md — what progress/messages the worker records and when.
- spec/backend/jobs-api.md — `jobs_status_retrieve` payload (`JobStatus`).
- spec/backend/api-contract.md — `JobStatus` fields as quoted from `schema.yaml`.
- spec/frontend/job-detail.md — polling (FE-JDET-007..013), the delay state diagram, Known gaps.
- spec/frontend/api-contract.md — `getJobStatus`.
- spec/backend/tests.md, spec/frontend/tests.md — test homes and traceability.

## Design

### Backend: keep `updated_at` truthful (BE-QUEUE-028)

Every worker write that changes the `jobs_status_retrieve` payload MUST also set
`Job.updated_at = now` in the same transaction or immediately after. A single helper keeps it
in one place, e.g. `_touch(job_id, now)` performing
`Job.objects.filter(pk=job_id).update(updated_at=now)`, or `updated_at=now` added to the
existing `update()` calls.

| Write | Where (today) | Change |
|---|---|---|
| `current_step` on step start | `jobs/worker.py` `_start_step` | add `updated_at=now` to the `update()` |
| Step state/timestamps (start, finish, cancel) | `JobStep.save(update_fields=...)` | touch the job |
| Step `processes` | `_save_processes` (only when `tracker.changed`) | touch the job |
| New messages | `add_messages` (`bulk_create`) | touch the job when the list is non-empty |
| Any other `JobStep`/`JobMessage` write found while auditing `jobs/worker.py` and `jobs/services.py` | — | touch the job |

Constraints:

- Do not touch on ticks where nothing changed. The tracker already guards `processes`; keep that
  guard, so an idle running job does not write every tick.
- Batch where cheap: one poll cycle that adds messages *and* updates processes can touch once.
  This is an optimisation, not a requirement.
- `updated_at` remains `auto_now`; nothing in the jobs list or admin ordering depends on it
  changing less often (check `jobs/views.py`, `admin_panel/` orderings before merging).

### Frontend: compare what is displayed (FE-JDET-010)

`refreshStatus()` returns "changed" when a fingerprint of the displayed status fields differs
from the previous tick, not when `updated_at` differs. The fingerprint covers every field the
view renders from the status payload: `state`, `queue_position`, `current_step`, each step's
`state` and `processes`, the message count and the last message id, and `updated_at`. Use the
field names exactly as `schema.yaml` `JobStatus` defines them. A stable `JSON.stringify` of a
picked object is enough; do not deep-compare the whole response.

Keep the fingerprint function small and exported (or co-located in `usePolling`'s neighbour
module) so it can be unit-tested without mounting the view.

### Interfaces

No shape change. `schema.yaml` is unchanged: `updated_at` already exists on `JobStatus`; this
task makes its value correct. Confirm with
`python manage.py spectacular --file schema.yaml --validate`.

## Steps

1. **Backend touch** in `jobs/worker.py` (and `jobs/services.py` if the audit finds status-visible
   writes there that don't already set `updated_at`).
2. **Frontend fingerprint** in `JobDetailView.vue` (`refreshStatus`), extracted as a helper.
3. **Backend unit tests**, in `jobs/tests/test_worker.py`:
   - For a running job (use the existing `WorkerTestBase` fake runner): `updated_at` advances when
     the next step starts, when `processes` change, and when a message is added.
   - `updated_at` does **not** advance on a tick with no progress (no extra writes).
   - The existing success-path test still passes, with `updated_at` monotonic over the run.
4. **Frontend unit tests** (vitest):
   - The fingerprint helper: changes for each listed field; unchanged for an identical payload
     with a different object identity.
   - `frontend/src/test/views/job-detail.test.js` › "progress change resets the poll delay" (the
     planned name in spec/frontend/job-detail.md). Mount the view with mocked `getJob`/
     `getJobStatus` and fake timers. Two status responses with the same `updated_at` but different
     `processes` reset the delay to 2 s. Identical responses back off. This is the first view
     test under `src/test/views/`; follow the layout the frontend tests spec names.
5. **E2E** (Article 7.3), in the existing jobs e2e module (`e2e/tests/test_jobs.py`): run a
   multi-step workflow whose steps sleep a few seconds. Check that the job page shows step 2 as
   running within ~4 s of it starting, using the worker's own timestamps, not a fixed sleep. If
   the timing is too flaky for CI, assert instead that `updated_at` from the status API changes
   between steps.
6. **Spec updates** (same change set):
   - spec/backend/job-queue-worker.md: BE-QUEUE-028 loses `(planned)`; remove the Known gap; add
     Acceptance tests rows.
   - spec/frontend/job-detail.md: FE-JDET-010 states the fingerprint fields; remove the Known
     gap; update the Acceptance tests row from planned to existing.
   - spec/backend/tests.md, spec/frontend/tests.md: traceability rows and counts.
   - spec/ISSUES.md: drop JOB-01.
7. Run the unit and e2e suites (`/tests` skill) and flake8.

## Acceptance criteria

- [ ] During a run, `Job.updated_at` changes whenever the status payload changes (step start
      and finish, process counts, messages) and not on idle ticks.
- [ ] The job page treats any change in displayed status fields, including `queue_position`, as
      a change and keeps polling at 2 s while progress is happening.
- [ ] `schema.yaml` is unchanged.
- [ ] Backend and frontend unit tests and one e2e test cover the above; suites pass; flake8 is
      clean.
- [ ] Spec files updated as in step 6.

## Open questions

Implement the stated default and copy the question into the relevant spec's Open questions.

- **Job list page.** `JobListView` also polls (FE-JLIST-011). Does it use `updated_at` for
  change detection too? If so, apply the same fingerprint approach there in this task. It is
  small and it is the same bug.
- **Incremental messages.** Each status poll returns all messages (JOB-06). The fingerprint uses
  the count and last id, so it does not depend on that changing. `?after=` is a separate task.
