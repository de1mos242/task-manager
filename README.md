# Task Manager

Manages issue-based task worktrees for one or more supported GitHub repositories.

## Quick Start

```sh
scripts/create-task.py https://github.com/org/repo/issues/123
scripts/create-task.py https://github.com/org/repo/issues/123 Vocavista OtherRepo
scripts/publish-task-pr.py --repo-dir tasks/123-task-title/Vocavista --all -m "Implement task" --yes
```

## How It Works

1. Add supported repositories to `ORIGINS.md` (name, HTTPS URL, short README description).
2. Run `scripts/create-task.py` with a GitHub issue URL.
3. The script clones the repo(s) under `tasks/<issue-number>-<title-slug>/<repo-name>/`.
4. A new branch `<issue-number>-<title-slug>` is created and checked out.
5. Each task root gets a `progress.md` for tracking work.

## Publishing Task Pull Requests

Use `scripts/publish-task-pr.py` to commit, push, and create a PR for a task repository.

Start with a dry run:

```sh
scripts/publish-task-pr.py --repo-dir tasks/123-task-title/Vocavista --all -m "Implement task" --dry-run
```

Publish after reviewing the plan:

```sh
scripts/publish-task-pr.py --repo-dir tasks/123-task-title/Vocavista --all -m "Implement task" --watch-checks --yes
```

The script infers the issue number from task branches such as `123-task-title`, adds `Fixes #123` to the PR body by default, pushes the branch, creates or reuses an open PR, and updates the task `progress.md` when possible.

## Structure

```
task-manager/
├── ORIGINS.md              # Supported repositories registry
├── AGENTS.md               # Instructions for agents working with tasks
├── .gitignore              # Ignores tasks/ (each has its own git state)
├── scripts/
│   ├── create-task.py      # Task bootstrap script
│   └── publish-task-pr.py  # Commit, push, and PR publishing script
├── .opencode/
│   ├── agent/
│   │   └── task-publisher.md
│   ├── commands/
│   │   └── publish-task-pr.md
│   └── skills/
│       └── task-creation/  # Project-local opencode skill
│           └── SKILL.md
└── tasks/                  # Created task worktrees (git ignored)
    └── 123-add-google-auth/
        ├── Vocavista/      # Cloned repository
        └── progress.md     # Task progress log
```

## Adding Repositories

Edit `ORIGINS.md` with a new table row:

| Name | URL | Description |
| --- | --- | --- |
| MyRepo | https://github.com/org/MyRepo.git | Short description from README. |

## OpenCode Skill

Place this repository anywhere and open it with opencode. The project-local skill at `.opencode/skills/task-creation/SKILL.md` activates automatically when you ask to start a task from a GitHub issue URL.

## OpenCode Command

The project-local command `/publish-task-pr` uses the `task-publisher` subagent to wrap `scripts/publish-task-pr.py` for task PR publishing. Restart opencode after changing command or agent files so the command and agent registry reload.
