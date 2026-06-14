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

## Pull Requests

- When creating a pull request for task work, link the PR to the corresponding GitHub issue in the PR body.
- Use a closing keyword such as `Fixes #123` or `Closes #123` when the PR is expected to complete the issue.
- If the PR is partial follow-up work, include the issue URL and describe what remains instead of using a closing keyword.
- When creating or editing GitHub issue/PR bodies with `gh`, ensure Markdown contains real line breaks. Do not pass literal `\n` sequences inside ordinary quoted `--body` strings; use a body file or shell quoting that produces actual newlines, and verify the body after editing.

## Progress Tracking

- Every task root must contain `progress.md`, for example `tasks/123-add-google-auth/progress.md`.
- Keep `progress.md` up to date after meaningful implementation changes, important findings, decisions, blockers, or verification results.
- Maintain `progress.md` as a concise current-state summary of what changed, important findings, completed steps, open blockers, and verification results; do not use dated entries or keep a chronological diary of every action.
- Update `progress.md` before pausing work or handing the task back to the user.

## Verification

- Run full relevant test/build commands directly when feasible; do not avoid full verification only because console output may be large.
- For large-output commands, keep token usage low by reading only the last relevant lines, for example `set -o pipefail; mvn clean install | tail -30`, or delegate the command to a subagent that runs it, analyzes the result, and returns only a concise success/failure summary with key errors.
- Do not paste or read full console output unless the bounded tail or subagent summary is insufficient to diagnose the problem.

## Production Safety

- Never run commands against production environments or live deployments unless the user explicitly asks for that exact command to be executed.
- For production commands such as deploys, migrations, scaling, secret changes, or live infrastructure operations, print the command for the user to run instead of executing it.

## Spring Development

- When working on Spring Boot or Spring Framework code, check the relevant sources in the local Maven repository when applicable so implementations use current APIs and available latest features.
- For projects using Spring Boot 4, verify approaches against current documentation and avoid outdated Spring Boot 2/3 patterns. The local Maven repository (`~/.m2/repository`) includes both jars and source artifacts, so inspect those sources when confirming available APIs or behavior.
