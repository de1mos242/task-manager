#!/usr/bin/env python3
"""Create a task worktree from a GitHub issue URL."""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def die(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def require_command(name: str) -> None:
    if not _find_executable(name):
        die(f"required command not found: {name}")


def _find_executable(name: str) -> bool:
    return any(
        os.access(os.path.join(p, name), os.X_OK)
        for p in os.environ.get("PATH", "").split(os.pathsep)
    )


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def slugify(text: str) -> str:
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    slug = re.sub(r"-+", "-", slug)
    return slug or "task"


def normalize_repo_url(value: str) -> str:
    if not value.startswith("https://github.com/"):
        raise ValueError(f"unsupported repository URL: {value}")
    if " " in value or value.startswith("git@"):
        raise ValueError(f"unsupported repository URL: {value}")
    value = value.removesuffix(".git")
    return f"{value}.git"


def repo_name_from_url(url: str) -> str:
    name = url.rsplit("/", 1)[-1]
    return name.removesuffix(".git")


def load_origins(origins_file: Path) -> list[dict[str, str]]:
    if not origins_file.is_file():
        die(f"ORIGINS.md not found at {origins_file}")

    origins = []
    for line in origins_file.read_text().splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        line = line.strip("|")
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            continue
        name, url = parts[0], parts[1]
        if not name or not url:
            continue
        if name.lower() in ("name", "---"):
            continue
        if not url.startswith("https://github.com/"):
            continue
        try:
            url = normalize_repo_url(url)
        except ValueError:
            continue
        origins.append({"name": name, "url": url})
    return origins


def resolve_repo(requested: str, origins: list[dict[str, str]]) -> str:
    if requested.startswith("https://github.com/"):
        normalized = normalize_repo_url(requested)
        for origin in origins:
            if origin["url"] == normalized:
                return normalized
    else:
        for origin in origins:
            if repo_name_from_url(origin["url"]) == requested:
                return origin["url"]
    die(f"repository is not listed in ORIGINS.md: {requested}")


def gh_issue_view(issue_number: str, repo: str) -> dict:
    result = subprocess.run(
        ["gh", "issue", "view", issue_number, "--repo", repo, "--json", "title"],
        capture_output=True,
        text=True,
        check=True,
    )
    import json
    data = json.loads(result.stdout)
    return {"title": data.get("title", "")}


def append_progress(progress_file: Path, message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(progress_file, "a") as f:
        f.write(f"\n## {timestamp}\n\n- {message}\n")


def run_git(args: list[str], cwd: Path | None = None) -> None:
    subprocess.run(["git", *args], check=True, cwd=cwd)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a task worktree from a GitHub issue URL.",
        epilog="Only HTTPS GitHub repositories listed in ORIGINS.md are supported.",
    )
    parser.add_argument("issue_url", help="GitHub issue URL")
    parser.add_argument(
        "repos",
        nargs="*",
        help="Optional repo names or HTTPS URLs (defaults to issue repo)",
    )
    args = parser.parse_args()

    require_command("gh")
    require_command("git")

    issue_url = args.issue_url
    match = re.match(
        r"^https://github\.com/([^/]+)/([^/]+)/issues/([0-9]+)([/?#].*)?$", issue_url
    )
    if not match:
        die(f"expected a GitHub issue URL: {issue_url}")

    issue_repo_owner = match.group(1)
    issue_repo_name = match.group(2)
    issue_number = match.group(3)

    root = repo_root()
    origins_file = root / "ORIGINS.md"
    origins = load_origins(origins_file)
    if not origins:
        die("no HTTPS GitHub repositories found in ORIGINS.md")

    issue_data = gh_issue_view(issue_number, f"{issue_repo_owner}/{issue_repo_name}")
    issue_title = issue_data["title"]
    if not issue_title:
        die("could not read issue title")

    title_slug = slugify(issue_title)
    task_slug = f"{issue_number}-{title_slug}"
    branch_name = task_slug
    task_root = root / "tasks" / task_slug
    progress_file = task_root / "progress.md"

    requested_repos = args.repos
    if not requested_repos:
        requested_repos = [f"https://github.com/{issue_repo_owner}/{issue_repo_name}.git"]

    resolved_repos = []
    for requested in requested_repos:
        resolved_repos.append(resolve_repo(requested, origins))

    for repo_url in resolved_repos:
        repo_name = repo_name_from_url(repo_url)
        repo_dir = task_root / repo_name
        if repo_dir.exists():
            die(f"repository already exists for this task: {repo_dir}")

    task_root.mkdir(parents=True, exist_ok=True)
    if not progress_file.exists():
        progress_file.write_text(
            f"# {task_slug}\n\n"
            f"- Issue: {issue_url}\n"
            f"- Branch: {branch_name}\n\n"
        )

    for repo_url in resolved_repos:
        repo_name = repo_name_from_url(repo_url)
        repo_dir = task_root / repo_name
        run_git(["clone", repo_url, str(repo_dir)])
        run_git(["switch", "-c", branch_name], cwd=repo_dir)
        append_progress(progress_file, f"Cloned {repo_name} and created branch {branch_name}.")

    print(f"Task created: {task_root}")
    print(f"Progress file: {progress_file}")


if __name__ == "__main__":
    main()
