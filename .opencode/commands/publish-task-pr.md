---
description: Commit, push, create a task PR, and optionally watch checks
agent: task-publisher
subtask: true
---

Publish a task pull request using `scripts/publish-task-pr.py`.

User arguments: `$ARGUMENTS`

Rules:

- Run from the task-manager repository root.
- Use the script as the source of truth; do not manually duplicate its git/gh flow unless the script fails and the failure is diagnosed.
- If no `--repo-dir` is provided, let the script auto-select the current task checkout or the only dirty checkout under `tasks/`; if selection is ambiguous, ask for `--repo-dir`.
- Never publish from a branch with the same name as the PR base branch; the script will reject this before committing.
- If `$ARGUMENTS` contains neither `--yes` nor `--dry-run`, run the script first with `--dry-run` appended and summarize the planned side effects.
- If the user has explicitly asked to publish, or `$ARGUMENTS` includes `--yes`, run the script with `--yes`.
- If the target repository has changes and no `-m` or `--message` is provided, generate a concise imperative commit message from the task diff/context and pass it to the script; ask only if the target repository or intended changes are ambiguous.
- Prefer passing `--repo-dir tasks/<task-slug>/<repo-name>` when the current directory is not the target task repository.
- Include `--watch-checks` when the user asks to wait for CI results.

Common example:

```sh
scripts/publish-task-pr.py \
  --repo-dir tasks/45-run-ci-build-in-pr-before-merging/Vocavista \
  --all \
  -m "Add PR CI build workflow" \
  --summary "Add a CI Build workflow for PRs targeting main." \
  --verification "./mvnw --batch-mode verify" \
  --watch-checks \
  --yes
```
