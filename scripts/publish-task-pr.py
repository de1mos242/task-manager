#!/usr/bin/env python3
"""Commit, push, and open a pull request for a task repository."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def die(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def require_command(name: str) -> None:
    if not shutil.which(name):
        die(f"required command not found: {name}")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def run(
    args: list[str],
    cwd: Path,
    *,
    dry_run: bool = False,
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    printable = " ".join(args)
    if dry_run and not capture:
        print(f"DRY RUN: ({cwd}) {printable}")
        return subprocess.CompletedProcess(args, 0, "", "")

    return subprocess.run(
        args,
        cwd=cwd,
        text=True,
        capture_output=capture,
        check=check,
    )


def output(args: list[str], cwd: Path, *, check: bool = True) -> str:
    result = run(args, cwd, capture=True, check=check)
    return result.stdout.strip()


def ensure_git_repo(repo_dir: Path) -> None:
    result = run(["git", "rev-parse", "--is-inside-work-tree"], repo_dir, capture=True, check=False)
    if result.returncode != 0 or result.stdout.strip() != "true":
        die(f"not a git repository: {repo_dir}")


def current_branch(repo_dir: Path) -> str:
    branch = output(["git", "branch", "--show-current"], repo_dir)
    if not branch:
        die("repository is in detached HEAD state")
    return branch


def status_lines(repo_dir: Path) -> list[str]:
    status = output(["git", "status", "--porcelain=v1"], repo_dir)
    return [line for line in status.splitlines() if line]


def print_preflight(repo_dir: Path, base: str) -> None:
    print("== Branch ==", flush=True)
    run(["git", "status", "--short", "--branch"], repo_dir)
    print()

    print("== Recent commits ==", flush=True)
    run(["git", "log", "--oneline", "-10"], repo_dir)
    print()

    print(f"== Diff from {base} ==", flush=True)
    run(["git", "diff", "--stat", f"{base}...HEAD"], repo_dir, check=False)
    print()


def stage_changes(repo_dir: Path, paths: list[str], stage_all: bool, dry_run: bool) -> None:
    if stage_all and paths:
        die("use either --all or --path, not both")
    if stage_all:
        run(["git", "add", "--all"], repo_dir, dry_run=dry_run)
        return
    if paths:
        run(["git", "add", "--", *paths], repo_dir, dry_run=dry_run)


def has_staged_changes(repo_dir: Path) -> bool:
    result = run(["git", "diff", "--cached", "--quiet"], repo_dir, check=False)
    return result.returncode != 0


def commit_if_needed(repo_dir: Path, message: str | None, dry_run: bool) -> bool:
    if not message:
        return False
    if not has_staged_changes(repo_dir):
        print("No staged changes to commit.")
        return False

    print("== Staged diff ==")
    run(["git", "diff", "--cached", "--stat"], repo_dir)
    run(["git", "diff", "--cached"], repo_dir)
    print()

    run(["git", "commit", "-m", message], repo_dir, dry_run=dry_run)
    return True


def default_title(repo_dir: Path, provided_title: str | None, message: str | None) -> str:
    if provided_title:
        return provided_title
    if message:
        return message
    title = output(["git", "log", "-1", "--pretty=%s"], repo_dir)
    if not title:
        die("could not infer PR title; pass --title")
    return title


def infer_issue(branch: str, provided_issue: str | None) -> str | None:
    if provided_issue:
        return provided_issue.lstrip("#")
    match = re.match(r"^(\d+)(?:-|$)", branch)
    if match:
        return match.group(1)
    return None


def build_body(args: argparse.Namespace, title: str, issue: str | None) -> str:
    if args.body_file:
        return Path(args.body_file).read_text()
    if args.body:
        body = args.body
    else:
        summary = args.summary or [title]
        lines = ["## Summary", *[f"- {item}" for item in summary]]
        if args.verification:
            lines.extend(["", "## Verification", *[f"- {item}" for item in args.verification]])
        body = "\n".join(lines)

    if issue and not args.no_fixes and f"#{issue}" not in body:
        body = f"{body.rstrip()}\n\nFixes #{issue}"
    return body


def branch_has_upstream(repo_dir: Path) -> bool:
    result = run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        repo_dir,
        capture=True,
        check=False,
    )
    return result.returncode == 0


def push_branch(repo_dir: Path, branch: str, dry_run: bool) -> None:
    if branch_has_upstream(repo_dir):
        run(["git", "push"], repo_dir, dry_run=dry_run)
    else:
        run(["git", "push", "-u", "origin", branch], repo_dir, dry_run=dry_run)


def existing_pr_url(repo_dir: Path, branch: str, base: str) -> str | None:
    result = run(
        ["gh", "pr", "view", branch, "--json", "baseRefName,state,url"],
        repo_dir,
        capture=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    pr = json.loads(result.stdout or "{}")
    if pr.get("baseRefName") == base and pr.get("state") == "OPEN":
        return pr.get("url")
    return None


def create_pr(repo_dir: Path, base: str, branch: str, title: str, body: str, dry_run: bool) -> str:
    existing = existing_pr_url(repo_dir, branch, base)
    if existing:
        print(f"Existing PR found: {existing}")
        return existing

    if dry_run:
        print("DRY RUN: would create PR with body:")
        print(body)
        return ""

    result = run(
        ["gh", "pr", "create", "--base", base, "--head", branch, "--title", title, "--body", body],
        repo_dir,
        capture=True,
        check=True,
    )
    url = result.stdout.strip()
    if not url:
        die("gh pr create did not return a PR URL")
    print(url)
    return url


def task_progress_file(repo_dir: Path) -> Path | None:
    root = repo_root().resolve()
    try:
        relative = repo_dir.resolve().relative_to(root / "tasks")
    except ValueError:
        return None
    parts = relative.parts
    if len(parts) < 2:
        return None
    progress = root / "tasks" / parts[0] / "progress.md"
    return progress if progress.exists() else None


def add_bullet_under_heading(content: str, heading: str, bullet: str) -> str:
    lines = content.splitlines()
    target = f"## {heading}"
    try:
        start = lines.index(target)
    except ValueError:
        suffix = "" if content.endswith("\n") else "\n"
        return f"{content}{suffix}\n{target}\n\n- {bullet}\n"

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break

    block = lines[start:end]
    if f"- {bullet}" in block:
        return content if content.endswith("\n") else f"{content}\n"

    insert_at = end
    while insert_at > start + 1 and lines[insert_at - 1] == "":
        insert_at -= 1
    lines.insert(insert_at, f"- {bullet}")
    return "\n".join(lines) + "\n"


def update_progress(repo_dir: Path, pr_url: str, checks_passed: bool | None) -> None:
    progress = task_progress_file(repo_dir)
    if not progress:
        return

    content = progress.read_text()
    content = add_bullet_under_heading(content, "Current State", f"Published PR: {pr_url}.")
    if checks_passed is True:
        content = add_bullet_under_heading(content, "Verification", f"GitHub PR checks passed for {pr_url}.")
    elif checks_passed is False:
        content = add_bullet_under_heading(content, "Verification", f"GitHub PR checks failed for {pr_url}.")
    progress.write_text(content)
    print(f"Updated progress: {progress}")


def comment_on_issue(repo_dir: Path, issue: str | None, pr_url: str, checks_passed: bool | None, skip: bool) -> None:
    if skip or not issue or not pr_url:
        return
    message = f"PR opened: {pr_url}"
    if checks_passed is True:
        message = f"PR opened and checks passed: {pr_url}"
    elif checks_passed is False:
        message = f"PR opened, but checks failed: {pr_url}"
    run(["gh", "issue", "comment", issue, "--body", message], repo_dir)


def watch_checks(repo_dir: Path, pr_url: str, dry_run: bool) -> bool | None:
    if not pr_url:
        return None
    if dry_run:
        print(f"DRY RUN: would watch checks for {pr_url}")
        return None
    result = run(["gh", "pr", "checks", pr_url, "--watch", "--interval", "10"], repo_dir, check=False)
    return result.returncode == 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Commit, push, and create a GitHub PR for a task repository.",
        epilog="Use --dry-run to inspect the planned publish flow, or --yes to perform side effects.",
    )
    parser.add_argument("--repo-dir", default=".", help="Task repository directory (default: current directory).")
    parser.add_argument("--base", default="main", help="Base branch for the PR (default: main).")
    parser.add_argument("-m", "--message", help="Commit message. If omitted, no commit is created.")
    parser.add_argument("--title", help="PR title. Defaults to commit message or HEAD subject.")
    parser.add_argument("--body", help="Full PR body. If omitted, a body is generated.")
    parser.add_argument("--body-file", help="Path to a file containing the full PR body.")
    parser.add_argument("--summary", action="append", default=[], help="Summary bullet for generated PR body; repeatable.")
    parser.add_argument("--verification", action="append", default=[], help="Verification bullet for generated PR body; repeatable.")
    parser.add_argument("--issue", help="GitHub issue number. Defaults to a leading branch number.")
    parser.add_argument("--no-fixes", action="store_true", help="Do not add a Fixes #issue line to the PR body.")
    parser.add_argument("--all", action="store_true", help="Stage all changed files before committing.")
    parser.add_argument("--path", action="append", default=[], help="Path to stage before committing; repeatable.")
    parser.add_argument("--watch-checks", action="store_true", help="Wait for PR checks to finish.")
    parser.add_argument("--skip-progress", action="store_true", help="Do not update task progress.md.")
    parser.add_argument("--skip-issue-comment", action="store_true", help="Do not comment on the linked GitHub issue.")
    parser.add_argument("--dry-run", action="store_true", help="Print the planned side effects without performing them.")
    parser.add_argument("--yes", action="store_true", help="Perform commit, push, and PR creation side effects.")
    args = parser.parse_args()

    if args.yes == args.dry_run:
        die("pass exactly one of --dry-run or --yes")
    if args.body and args.body_file:
        die("use either --body or --body-file, not both")
    return args


def main() -> None:
    args = parse_args()
    require_command("git")
    require_command("gh")

    repo_dir = Path(args.repo_dir).expanduser().resolve()
    ensure_git_repo(repo_dir)
    branch = current_branch(repo_dir)
    issue = infer_issue(branch, args.issue)

    dirty = bool(status_lines(repo_dir))
    if dirty and not args.message:
        die("working tree has changes; pass --message to commit them")
    if dirty and not args.all and not args.path:
        die("working tree has changes; pass --all or one or more --path values to stage intended files")

    print_preflight(repo_dir, args.base)
    stage_changes(repo_dir, args.path, args.all, args.dry_run)
    committed = commit_if_needed(repo_dir, args.message, args.dry_run)
    if committed:
        print("Commit step completed.")

    title = default_title(repo_dir, args.title, args.message)
    body = build_body(args, title, issue)

    push_branch(repo_dir, branch, args.dry_run)
    pr_url = create_pr(repo_dir, args.base, branch, title, body, args.dry_run)
    checks_passed = watch_checks(repo_dir, pr_url, args.dry_run) if args.watch_checks else None

    if pr_url and not args.skip_progress and not args.dry_run:
        update_progress(repo_dir, pr_url, checks_passed)
    if pr_url and not args.dry_run:
        comment_on_issue(repo_dir, issue, pr_url, checks_passed, args.skip_issue_comment)

    if pr_url:
        print(f"PR: {pr_url}")
    if checks_passed is True:
        print("Checks: passed")
    elif checks_passed is False:
        print("Checks: failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
