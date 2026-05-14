# Job Tests

Tests for job submission, status monitoring, cancellation, restart, log viewing, result downloads, and queue management.

Assumes `BASE`, `APP`, `USER_TOKEN`, `ADMIN_TOKEN`, and at least one enabled workflow exist as described in [README.md](README.md) and [02-workflows.md](02-workflows.md).

Job IDs are UUIDs. Replace `<job_id>` throughout with an actual job ID obtained from submission or listing responses.

---

## Test Data Setup

Obtain the ID of the public workflow to use for submission:

```bash
WORKFLOW_ID=$(curl -s "$BASE/workflows/" \
  -H "Authorization: Token $USER_TOKEN" \
  | python -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")
echo "Workflow ID: $WORKFLOW_ID"
```

---

## 1. Job Submission

### JOB-01 — Submit a job with valid parameters

- **Preconditions:** `testuser` is authenticated. A workflow with ID `$WORKFLOW_ID` is enabled and accessible to `testuser`.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/jobs/" \
       -H "Authorization: Token $USER_TOKEN" \
       -H "Content-Type: application/json" \
       -d "{\"workflow\": $WORKFLOW_ID, \"name\": \"Test Job 1\", \"parameters\": {}}"
     ```
     *(Adjust `parameters` to match the workflow's input definitions.)*
- **Expected result:** HTTP 201. Response includes:
  - `id` — a UUID
  - `status` = `"pending"`
  - `workflow` = `$WORKFLOW_ID`
  - `user` matches `testuser`
  - `submitted_at` is set

---

### JOB-02 — Submit a job: missing required parameter

- **Preconditions:** A workflow with at least one required input parameter exists.
- **Steps (API):**
  1. Submit the job omitting a required parameter value:
     ```bash
     curl -s -X POST "$BASE/jobs/" \
       -H "Authorization: Token $USER_TOKEN" \
       -H "Content-Type: application/json" \
       -d "{\"workflow\": $WORKFLOW_ID, \"parameters\": {}}"
     ```
- **Expected result:** HTTP 400. Response indicates which parameter is missing or invalid.

---

### JOB-03 — Submit a job from the UI

- **Preconditions:** `testuser` is logged in via the UI. `$APP/run/<workflow_id>` is accessible.
- **Steps (UI):**
  1. Navigate to `$APP/run/<workflow_id>`.
  2. Fill in all required parameters in the dynamic form.
  3. For any `file` type parameter, select a local file.
  4. Click **Submit** (or **Run**).
- **Expected result:**
  - If a file parameter exists, a file upload progress dialog appears during upload.
  - After submission, the browser navigates to the job detail page `$APP/jobs/<new_job_id>`.
  - The job status badge shows **Pending**.

---

### JOB-04 — Unauthenticated job submission is rejected

- **Preconditions:** None.
- **Steps (API):**
  1. Send without a token:
     ```bash
     curl -s -X POST "$BASE/jobs/" \
       -H "Content-Type: application/json" \
       -d "{\"workflow\": 1, \"parameters\": {}}"
     ```
- **Expected result:** HTTP 401 or 403. No job is created.

---

## 2. Job Status Lifecycle

### JOB-05 — Job status transitions: pending → running → completed

- **Preconditions:** A job was just submitted (JOB-01) and is in `status=pending`.
- **Steps (API):**
  1. Poll the job endpoint until the status changes:
     ```bash
     watch -n 2 "curl -s \"$BASE/jobs/<job_id>/\" \
       -H \"Authorization: Token $USER_TOKEN\" \
       | python -c \"import sys,json; d=json.load(sys.stdin); print(d.get('status'), d.get('started_at'), d.get('completed_at'))\""
     ```
- **Expected result:**
  - Status starts as `"pending"`, transitions to `"running"` once the job engine picks it up, then to `"completed"` after the workflow finishes.
  - `started_at` is set when status becomes `"running"`.
  - `completed_at` is set when status becomes `"completed"`.

---

### JOB-06 — Job detail view updates in real-time (WebSocket)

- **Preconditions:** A job is in progress (`status=running`). `testuser` is logged in via the UI.
- **Steps (UI):**
  1. Navigate to `$APP/jobs/<job_id>`.
  2. Observe the **Steps** tab while the job runs.
- **Expected result:**
  - The step progress accordion updates without a page refresh.
  - The status badge changes from **Running** to **Completed** (or **Failed**) automatically.
  - No manual polling or page reload is required.

---

## 3. Job List

### JOB-07 — User sees only their own jobs

- **Preconditions:** `testuser` has submitted at least one job. `otheruser` has also submitted at least one job. Both tokens are available.
- **Steps (API):**
  1. List jobs as `testuser`:
     ```bash
     curl -s "$BASE/jobs/" -H "Authorization: Token $USER_TOKEN"
     ```
  2. List jobs as `otheruser`:
     ```bash
     OTHER_TOKEN=$(curl -s -X POST "$BASE/auth/login/" \
       -H "Content-Type: application/json" \
       -d '{"username": "otheruser", "password": "Otherpass1"}' \
       | python -c "import sys,json; print(json.load(sys.stdin)['token'])")
     curl -s "$BASE/jobs/" -H "Authorization: Token $OTHER_TOKEN"
     ```
- **Expected result:** Each user's response contains only their own jobs. `testuser`'s jobs do not appear in `otheruser`'s list and vice versa.

---

### JOB-08 — Admin sees all users' jobs

- **Preconditions:** Both `testuser` and `otheruser` have submitted jobs.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/jobs/" -H "Authorization: Token $ADMIN_TOKEN"
     ```
- **Expected result:** HTTP 200. The response includes jobs from multiple users (both `testuser`'s and `otheruser`'s jobs appear).

---

### JOB-09 — Job list UI shows only the current user's jobs

- **Preconditions:** `testuser` is logged in. `testuser` has at least one job submitted.
- **Steps (UI):**
  1. Navigate to `$APP/jobs`.
- **Expected result:** A table or list of `testuser`'s jobs is shown. Each row shows at minimum: job name, workflow, status, and submission date.

---

### JOB-10 — Job list pagination

- **Preconditions:** `testuser` has more jobs than the page size (typically 10–20). Submit enough jobs to exceed one page.
- **Steps (UI):**
  1. Navigate to `$APP/jobs`.
  2. If a second page exists, click the **Next** pagination control.
- **Expected result:** The next page of jobs is loaded. The page indicator updates. Navigation between pages works without a full page reload.

---

## 4. Job Detail Tabs

### JOB-11 — Logs tab shows raw job output

- **Preconditions:** A completed (or running) job exists. `testuser` is logged in.
- **Steps (UI):**
  1. Navigate to `$APP/jobs/<job_id>`.
  2. Click the **Logs** tab.
- **Expected result:** The raw text log output of the job is displayed. If the job is still running, logs may update in real-time.

---

### JOB-12 — Logs available via API

- **Preconditions:** A job with ID `<job_id>` exists and belongs to `testuser`.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/jobs/<job_id>/logs/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 200. Response contains the job's log output (plain text or JSON).

---

### JOB-13 — Steps tab shows step progress accordion

- **Preconditions:** A job with multiple steps exists. `testuser` is logged in.
- **Steps (UI):**
  1. Navigate to `$APP/jobs/<job_id>`.
  2. Click the **Steps** tab.
- **Expected result:** Each step is shown as a collapsible accordion item. Each item shows the step name and status (pending / running / completed / failed). Clicking a step expands it to show step-level details or output.

---

### JOB-14 — Results tab shows download links

- **Preconditions:** A completed job with downloadable result files exists.
- **Steps (UI):**
  1. Navigate to `$APP/jobs/<job_id>`.
  2. Click the **Results** tab.
- **Expected result:** A list of downloadable files is shown. Each file has a name, size, and a download link or button.

---

## 5. Cancel Job

### JOB-15 — Owner can cancel a pending job

- **Preconditions:** `testuser` has a job in `status=pending`. The job ID is `<job_id>`.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/jobs/<job_id>/cancel/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 200. The job's `status` changes to `"cancelled"`. Subsequent `GET /api/jobs/<job_id>/` confirms `status = "cancelled"`.

---

### JOB-16 — Owner can cancel a running job

- **Preconditions:** `testuser` has a job in `status=running`.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/jobs/<job_id>/cancel/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 200. Job `status` becomes `"cancelled"`.

---

### JOB-17 — Non-owner cannot cancel another user's job

- **Preconditions:** `testuser` has a job in `status=pending` or `running`. `otheruser` token is available.
- **Steps (API):**
  1. Attempt to cancel `testuser`'s job as `otheruser`:
     ```bash
     curl -s -X POST "$BASE/jobs/<testuser_job_id>/cancel/" \
       -H "Authorization: Token $OTHER_TOKEN"
     ```
- **Expected result:** HTTP 403 or 404. The job status is unchanged.

---

### JOB-18 — Completed job cannot be cancelled

- **Preconditions:** `testuser` has a job in `status=completed`.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/jobs/<job_id>/cancel/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 400 (or similar error). Response indicates the job cannot be cancelled in its current state.

---

### JOB-19 — Admin can cancel any user's job

- **Preconditions:** `otheruser` has a job in `status=pending` or `running`.
- **Steps (API):**
  1. Send using admin token:
     ```bash
     curl -s -X POST "$BASE/jobs/<otheruser_job_id>/cancel/" \
       -H "Authorization: Token $ADMIN_TOKEN"
     ```
- **Expected result:** HTTP 200. Job `status` becomes `"cancelled"`.

---

## 6. Restart Job

### JOB-20 — Owner can restart a failed job

- **Preconditions:** `testuser` has a job in `status=failed`. Manually set one if needed:
  ```bash
  python manage.py shell -c "
  from jobs.models import Job
  j = Job.objects.filter(user__username='testuser').first()
  j.status = 'failed'
  j.save()
  print(j.id)
  "
  ```
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/jobs/<job_id>/restart/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 200. A new job is created (or the existing one is requeued) with `status=pending`.

---

### JOB-21 — Owner can restart a cancelled job

- **Preconditions:** `testuser` has a job in `status=cancelled`.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/jobs/<job_id>/restart/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 200. The job is restarted.

---

### JOB-22 — Pending job cannot be restarted

- **Preconditions:** `testuser` has a job in `status=pending`.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/jobs/<job_id>/restart/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 400. Response indicates the job cannot be restarted while it is pending or running.

---

## 7. Downloads

### JOB-23 — List downloadable result files

- **Preconditions:** A completed job with associated `JobDownload` records exists.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/jobs/<job_id>/download/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 200. Response is a list of download objects, each with at minimum: `filename`, `file_size`, and a URL or ID for downloading.

---

### JOB-24 — Download a specific result file

- **Preconditions:** A job download exists with ID `<download_id>`.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -O -J "$BASE/jobs/<job_id>/download/<download_id>/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 200. The file is returned as a binary download with the correct `Content-Disposition` header. The file content is valid.

---

### JOB-25 — Non-owner cannot download another user's results

- **Preconditions:** `testuser` has a completed job with downloads. `otheruser` token is available.
- **Steps (API):**
  1. Attempt to download as `otheruser`:
     ```bash
     curl -s "$BASE/jobs/<testuser_job_id>/download/" \
       -H "Authorization: Token $OTHER_TOKEN"
     ```
- **Expected result:** HTTP 403 or 404. No file data is returned.

---

### JOB-26 — Admin can download any user's results

- **Preconditions:** `testuser` has a completed job with downloads.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/jobs/<testuser_job_id>/download/" \
       -H "Authorization: Token $ADMIN_TOKEN"
     ```
- **Expected result:** HTTP 200. The download list is returned.

---

### JOB-27 — Expired download link is rejected

- **Preconditions:** A `JobDownload` exists. Manually expire it:
  ```bash
  python manage.py shell -c "
  from jobs.models import JobDownload
  from django.utils import timezone
  import datetime
  d = JobDownload.objects.first()
  d.expires_at = timezone.now() - datetime.timedelta(days=1)
  d.save()
  print(d.id)
  "
  ```
- **Steps (API):**
  1. Attempt to download the expired file:
     ```bash
     curl -s "$BASE/jobs/<job_id>/download/<download_id>/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 400 or 410 (Gone). Response indicates the download link has expired.

---

## 8. Queue Management (Admin)

### JOB-28 — Get queue status

- **Preconditions:** `adminuser` is authenticated.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/jobs/queue_status/" \
       -H "Authorization: Token $ADMIN_TOKEN"
     ```
- **Expected result:** HTTP 200. Response contains job counts (e.g. `pending`, `running`, `total`).

---

### JOB-29 — Non-admin cannot access queue status

- **Preconditions:** `testuser` is authenticated (non-admin).
- **Steps (API):**
  1. Send:
     ```bash
     curl -s "$BASE/jobs/queue_status/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** HTTP 403. Queue status is not returned.

---

### JOB-30 — Admin can pause the job queue

- **Preconditions:** The queue is currently running.
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/jobs/pause_queue/" \
       -H "Authorization: Token $ADMIN_TOKEN"
     ```
  2. Submit a new job (JOB-01). Wait a few seconds.
  3. Check the new job's status:
     ```bash
     curl -s "$BASE/jobs/<new_job_id>/" -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** Step 1 returns HTTP 200. Step 3 shows the new job remains in `status=pending` (the queue engine does not pick it up while paused).

---

### JOB-31 — Admin can resume the job queue

- **Preconditions:** The queue is paused (JOB-30 completed).
- **Steps (API):**
  1. Send:
     ```bash
     curl -s -X POST "$BASE/jobs/resume_queue/" \
       -H "Authorization: Token $ADMIN_TOKEN"
     ```
  2. Wait a few seconds and check the pending job's status.
- **Expected result:** Step 1 returns HTTP 200. The previously-pending job transitions to `status=running` (queue resumes normal operation).

---

### JOB-32 — Non-admin cannot pause or resume the queue

- **Preconditions:** `testuser` is authenticated (non-admin).
- **Steps (API):**
  1. Attempt to pause:
     ```bash
     curl -s -X POST "$BASE/jobs/pause_queue/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
  2. Attempt to resume:
     ```bash
     curl -s -X POST "$BASE/jobs/resume_queue/" \
       -H "Authorization: Token $USER_TOKEN"
     ```
- **Expected result:** Both requests return HTTP 403.
