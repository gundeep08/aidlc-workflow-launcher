from datetime import datetime, timezone
from pathlib import Path

import yaml

from cli.services import git_service


def get_re_timestamp(re_skills_dir: Path, repo_name: str) -> str | None:
    """Get RE timestamp from metadata.yml, or fall back to latest file mtime."""
    repo_re_dir = re_skills_dir / repo_name
    metadata_path = repo_re_dir / "metadata.yml"
    if metadata_path.exists():
        with open(metadata_path) as f:
            data = yaml.safe_load(f) or {}
        value = data.get("last_updated")
        if value is not None:
            return value.isoformat() if hasattr(value, 'isoformat') else str(value)

    # Fallback: use most recent .md file modification time
    if not repo_re_dir.exists():
        return None
    md_files = list(repo_re_dir.glob("*.md"))
    if not md_files:
        return None
    latest_mtime = max(f.stat().st_mtime for f in md_files)
    return datetime.fromtimestamp(latest_mtime, tz=timezone.utc).isoformat()


def has_re_skills(re_skills_dir: Path, repo_name: str) -> bool:
    """Check if RE skills exist (any .md files other than README in the directory)."""
    repo_re_dir = re_skills_dir / repo_name
    if not repo_re_dir.exists():
        return False
    return any(f for f in repo_re_dir.glob("*.md") if f.name.lower() != "readme.md")


def check_staleness(repo_name: str, re_skills_dir: Path, code_repo_dir: Path) -> dict:
    if not has_re_skills(re_skills_dir, repo_name):
        return {"repo_name": repo_name, "stale": True, "commits_since": 0, "last_re": None, "reason": "no_re"}
    re_timestamp = get_re_timestamp(re_skills_dir, repo_name)
    if re_timestamp is None:
        return {"repo_name": repo_name, "stale": True, "commits_since": 0, "last_re": None, "reason": "no_re"}
    timestamp_str = str(re_timestamp)
    commits_since = git_service.get_commit_count_since(code_repo_dir, timestamp_str)
    stale = commits_since > 0
    reason = "stale" if stale else "fresh"
    return {
        "repo_name": repo_name,
        "stale": stale,
        "commits_since": commits_since,
        "last_re": timestamp_str,
        "reason": reason,
    }


def get_all_staleness(re_skills_dir: Path, code_dir: Path) -> list[dict]:
    results = []
    if not re_skills_dir.exists():
        return results
    for repo_dir in re_skills_dir.iterdir():
        if not repo_dir.is_dir():
            continue
        repo_name = repo_dir.name
        code_repo_dir = code_dir / repo_name
        if not code_repo_dir.exists():
            continue
        results.append(check_staleness(repo_name, re_skills_dir, code_repo_dir))
    return results
