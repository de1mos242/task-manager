# Task Manager Instructions

This repository manages issue-based task worktrees for one or more supported GitHub repositories.

## Task Creation

- Supported repositories are listed in `ORIGINS.md` with name, HTTPS GitHub clone URL, and short README-based description.
- Task checkouts must be created under `tasks/<issue-number>-<issue-title-slug>/<repo-name>/`.
- The `tasks/` directory is ignored because each cloned repository manages its own git state.
- Use `scripts/create-task.py` to create task directories and branches instead of cloning manually.

## Task Registry

After creating a new task, update `TASKS.md` in the repository root with the new entry.

`TASKS.md` must contain a table of all created tasks with:
- Creation time
- Issue number
- Issue URL
- Issue title
- Repositories used

Append new tasks to the bottom of the table. Do not remove or modify existing entries.

## Progress Tracking

- Every task root must contain `progress.md`, for example `tasks/123-add-google-auth/progress.md`.
- Keep `progress.md` up to date after any significant implementation change, decision, blocker, or verification result.
- Use concise dated entries that explain what changed and why.
- Update `progress.md` before pausing work or handing the task back to the user.
