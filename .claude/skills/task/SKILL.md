---
name: task
description: Create a new task
---

- Write a new task markdown file for "$1" in ./tasks/
- Ensure that the task adheres to spec/constitution.md
- Open the task with an "Overview" section that describes the problem and
  intent in plain language, that would be understandable to a graduate-level
  developer.
- Ensure that you draw from the relevant specifications in ./spec/ so that the
  task is coherent with project objectives and constraints.
- Before writing the task, check tasks/todo.md for any related items that should
  be included.
- Don't write code in the task - pseudocode or examples only
- If the task involves frontend or backend code, ensure that unit test coverage
  is included as part of the task description.
- If the task involves multiple large steps, break it down into multiple task
  files e.g."build backend" "build frontend".
- If the task should be completed before an existing task, renumber them to
  suggest the preferred order of completion.
- If writing spec, never create markdown links to task files, just say
  "task nn_task_name.md". This prevents broken links when tasks are moved or
  renamed. Do not use line anchors in any link as they also go stale quickly.
- Do not write markdown links to local files, especially task or spec files.
  Don't use relative paths - they will break later. Just reference files by
  plain text path, relative to the project root.
- When making updates to application code, consider whether an update to the
  ansible playbook should be included to make that feature deployable (e.g.
  config update)
