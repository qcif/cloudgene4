---
name: execute
description: Execute a task from the ./tasks directory
---

Read ./tasks/$1_*.md and carry out the specified task.

**Before starting**
- Prompt the user if `git status` shows a lot of uncommitted
  changes - they should probably be committed before starting.
- Consider whether the task has unmet preconditions, or whether it should be
  deferred until another task is complete.
- Check tasks/todo.md for any items relating to the task, and flag them for
  inclusion in the brief if they are not already represented there.
- Create a git worktree to do the work, so you don't clobber other agents
  working in parallel.
- Write the task ID to tasks/active.md (main branch) so that `main` has a record
  of this open branch.

**When executing the task**
- If anything is unclear, stop and ask for clarification in the task.
- Deviations from the task brief require approval from the user before
  proceeding.
- As the task progresses, write any outcomes to the bottom of the task file in
  an "Outcomes" section, especially any deviations from the task definition, or
  any new information that comes to light.
- Code comments should be written only when they add useful context to otherwise
  obscure code. Docstrings, task briefs, spec or docs are usually the right
  place for narrative material.

**Task completion**
- When the task is complete, ensure that any checklists in the task file are
  checked off, and move the task file to ./tasks/completed/.
- Ensure that any markdown links to the task file are updated to point to the
  new location in ./tasks/completed/.
- If task execution resulted in new tasks being created, write them to
  ./tasks/todo.md.
- If writing spec, do not create markdown links to task files, just say
  "task nn_task_name". This prevents broken links when tasks are moved or
  renamed.
- Report all spec changes in your final summary to the user.
- Commit your changes to the worktree and prompt the user to merge into main.
- When it's merged, remove your entry from tasks/active.md
