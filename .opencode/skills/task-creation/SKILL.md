---
name: task-creation
description: Use when starting or creating a task from a GitHub issue URL in this task-manager repository, including optional target repositories.
---

# Task Creation

Use this skill when the user asks to start, create, or set up a task from a GitHub issue URL.

## Workflow

1. Confirm the current project is the task-manager repository.
2. Use `scripts/create-task.py` with the GitHub issue URL.
3. If the user explicitly names target repositories, pass them after the issue URL.
4. If the user does not name repositories, do not add repo arguments; the script will use the issue repository by default.
5. After the script finishes, update the task root `progress.md` with a concise setup entry if the script did not already capture the important context.

## Repository Rules

- Supported repositories must be listed in `ORIGINS.md` with name, HTTPS URL, and short README-based description.
- Only HTTPS GitHub clone URLs are supported.
- Task repositories are cloned under `tasks/<issue-number>-<issue-title-slug>/<repo-name>/`.
- Existing task repository directories must not be overwritten.
- `tasks/` is git ignored because cloned repositories manage their own git state.

## Progress Rule

Keep `tasks/<task-slug>/progress.md` up to date after any significant implementation change, decision, blocker, or verification result.

## Examples

```sh
scripts/create-task.py https://github.com/org/repo/issues/123
scripts/create-task.py https://github.com/org/repo/issues/123 Vocavista OtherRepo
scripts/create-task.py https://github.com/org/repo/issues/123 https://github.com/org/OtherRepo.git
```
