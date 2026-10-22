---
name: fix-ci
description: Diagnose and fix failing GitHub Actions workflows for this repo
---

Diagnose and fix failing GitHub Actions runs. "$1" may name a workflow or
run ID; otherwise find out what is red.

## Facts (verified; re-check if something fails)

- Workflows: TBC (None yet)

## Procedure

1. **Triage.** `gh run list --limit 10`, then `gh run view <id>` to find
   the failing job and step. Note any skipped jobs.
2. **Get the error.** `gh run view <id> --log-failed`. This has returned
   empty output before. If so, reproduce locally: extract the step's
   inline Python heredoc from `workflow.yml` into the scratchpad and run it
   with `$CLAUDE_VENV/bin/python`, e.g.

   ```
   sed -n "/<step name>/,/^          EOF/p" .github/workflows/workflow.yml \
     | sed -n '/<<.EOF./,/^          EOF/p' | sed '1d;$d' \
     | sed 's/^          //' > $SCRATCH/check.py
   ```

3. **Fix** using the catalogue below.
4. **Verify locally** by running every step of the failing job, plus any
   jobs it gates (`needs:`).
5. **Push and confirm.** Only commit/push when the user approves, then
   `gh run watch` the new run until every job is green (including ones
   that were previously skipped).
6. **Extend the catalogue** below when you fix a new class of failure.

## Failure catalogue

(None yet)
