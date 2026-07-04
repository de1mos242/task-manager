---
description: Create a task checkout from a GitHub issue URL
subtask: true
---

Create a task checkout using `scripts/create-task.py`.

User arguments: `$ARGUMENTS`

Rules:

- Run from the task-manager repository root.
- Require the first argument to be a GitHub issue URL.
- If the user explicitly names target repositories after the issue URL, pass them through as repo names or HTTPS GitHub clone URLs.
- If the user does not name repositories, do not add repo arguments; the script will use the issue repository by default.
- Use `scripts/create-task.py` as the source of truth for cloning, branch creation, `TASKS.md`, and initial `progress.md` updates.
- Do not manually clone repositories or edit `TASKS.md` unless the script fails and the failure has been diagnosed.
- After the script finishes, report the created task path and progress file path from the script output.

Common examples:

```sh
scripts/create-task.py https://github.com/org/repo/issues/123
scripts/create-task.py https://github.com/org/repo/issues/123 Vocavista OtherRepo
scripts/create-task.py https://github.com/org/repo/issues/123 https://github.com/org/OtherRepo.git
```
