import subprocess
from pathlib import Path

from cli.exceptions import GitCloneError, GitNotInstalledError


def is_git_installed() -> bool:
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def clone_repo(url: str, target_dir: Path) -> None:
    if not is_git_installed():
        raise GitNotInstalledError("git is not installed or not on PATH")
    result = subprocess.run(
        ["git", "clone", url, str(target_dir)],
        text=True,
    )
    if result.returncode != 0:
        raise GitCloneError(f"git clone failed")


def pull_repo(repo_dir: Path) -> None:
    subprocess.run(
        ["git", "-C", str(repo_dir), "pull"],
        capture_output=True,
        text=True,
        check=True,
    )


def get_latest_commit_hash(repo_dir: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_dir), "log", "-1", "--format=%H"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_commit_count_since(repo_dir: Path, since_date: str) -> int:
    result = subprocess.run(
        ["git", "-C", str(repo_dir), "rev-list", "--count", f"--since={since_date}", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return int(result.stdout.strip())


def get_latest_commit_date(repo_dir: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_dir), "log", "-1", "--format=%aI"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def checkout_branch(repo_dir: Path, branch_name: str) -> None:
    """Create and checkout branch, or just checkout if it already exists."""
    # Check if branch exists locally
    result = subprocess.run(
        ["git", "-C", str(repo_dir), "rev-parse", "--verify", branch_name],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        subprocess.run(
            ["git", "-C", str(repo_dir), "checkout", branch_name],
            capture_output=True,
            text=True,
            check=True,
        )
    else:
        subprocess.run(
            ["git", "-C", str(repo_dir), "checkout", "-b", branch_name],
            capture_output=True,
            text=True,
            check=True,
        )


def commits_behind_remote(repo_dir: Path) -> int | None:
    """Return number of commits the local default branch is behind remote."""
    # Fetch latest without merging
    result = subprocess.run(
        ["git", "-C", str(repo_dir), "fetch"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    # Try common default branch names
    for default_branch in ("main", "master"):
        result = subprocess.run(
            ["git", "-C", str(repo_dir), "rev-list", "--count", f"{default_branch}..origin/{default_branch}"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return int(result.stdout.strip())
    return None
