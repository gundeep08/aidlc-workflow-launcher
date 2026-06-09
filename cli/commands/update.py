from pathlib import Path

import click

from cli.config.constants import CODE_DIR, DOCS_DIR, AIDLC_WORKFLOWS_REPO_OWNER, AIDLC_WORKFLOWS_REPO_NAME
from cli.exceptions import AidlcError, ConfigNotFoundError, PlatformNotConfiguredError
from cli.services import git_service, workspace_config_service, github_release_service, platform_service


@click.command()
def update():
    """Update rules, docs repo, and/or code repos."""
    workspace_root = Path.cwd()
    try:
        config = workspace_config_service.load_config(workspace_root)
        if not config:
            raise ConfigNotFoundError("Run 'aidlc init' first")

        repos = workspace_config_service.get_code_repos(config)
        docs_url = workspace_config_service.get_docs_repo_url(config)

        click.echo("\n📋 What would you like to update?\n")
        click.echo("    1) AI-DLC Rules")
        click.echo("    2) Docs repo")
        click.echo("    3) Code repo(s)")
        click.echo("    A) All of the above")
        choice = click.prompt("\nSelect", default="A").strip().upper()

        if choice in ("1", "A"):
            _update_rules(workspace_root, config)

        if choice in ("2", "A"):
            _update_docs(workspace_root, docs_url)

        if choice in ("3", "A"):
            _update_code(workspace_root, repos)

        click.echo("\n✅ Update complete.")

    except AidlcError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(1)


def _update_rules(workspace_root: Path, config: dict) -> None:
    import tempfile

    platform = workspace_config_service.get_platform(config)
    if not platform:
        platform = platform_service.detect_current_platform(workspace_root)
    if not platform:
        click.echo("  ⚠ No platform configured — skipping rules update")
        return

    old_version = config.get("rules_version", "unknown")
    click.echo("\n  Fetching latest AI-DLC rules...")
    try:
        release = github_release_service.get_latest_release_info(
            AIDLC_WORKFLOWS_REPO_OWNER, AIDLC_WORKFLOWS_REPO_NAME
        )
        if release["tag"] == old_version:
            click.echo(f"  ✓ Rules already up to date ({old_version})")
            return

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            zip_path = tmp_path / "release.zip"
            github_release_service.download_release_zip(release["download_url"], zip_path)
            extracted = github_release_service.extract_rules(zip_path, tmp_path / "extracted")
            platform_service.place_rules(platform, extracted, workspace_root)

        config["rules_version"] = release["tag"]
        workspace_config_service.save_config(workspace_root, config)
        click.echo(f"  ✓ Rules updated: {old_version} → {release['tag']}")
    except Exception as e:
        click.echo(f"  ⚠ Could not update rules: {e}")


def _update_docs(workspace_root: Path, docs_url: str | None) -> None:
    if not docs_url:
        click.echo("\n  ⚠ No docs repo configured — skipping")
        return

    docs_repo_name = workspace_config_service.derive_repo_name(docs_url)
    docs_repo_dir = workspace_root / DOCS_DIR / docs_repo_name

    if not docs_repo_dir.exists():
        click.echo(f"\n  ⚠ Docs repo not found at docs/{docs_repo_name} — skipping")
        return

    click.echo(f"\n  Pulling docs repo ({docs_repo_name})...")
    try:
        git_service.pull_repo(docs_repo_dir)
        click.echo(f"  ✓ Docs repo up to date")
    except Exception as e:
        click.echo(f"  ⚠ Could not pull docs repo: {e}")


def _update_code(workspace_root: Path, repos: list[dict]) -> None:
    if not repos:
        click.echo("\n  ⚠ No code repos registered — skipping")
        return

    # Check which repos have remote changes
    stale = []
    for repo in repos:
        name = repo["name"]
        code_repo_dir = workspace_root / CODE_DIR / name
        if not code_repo_dir.exists():
            continue
        behind = git_service.commits_behind_remote(code_repo_dir)
        if behind is not None and behind > 0:
            stale.append((name, behind))

    if not stale:
        click.echo("\n  ✓ All code repos up to date")
        return

    click.echo("\n  Code repos behind remote:\n")
    for i, (name, behind) in enumerate(stale, 1):
        click.echo(f"    {i}) {name} ({behind} commit(s) behind)")
    click.echo(f"    A) All of the above")
    choice = click.prompt("\n  Which repo(s) to pull? (e.g. 1,2 or A for all)", default="A").strip()

    if choice.upper() == "A":
        to_pull = [name for name, _ in stale]
    else:
        indices = [int(c.strip()) - 1 for c in choice.split(",")]
        to_pull = [stale[i][0] for i in indices]

    for name in to_pull:
        code_repo_dir = workspace_root / CODE_DIR / name
        try:
            git_service.pull_repo(code_repo_dir)
            click.echo(f"  ✓ {name} — updated")
        except Exception as e:
            click.echo(f"  ⚠ {name} — could not pull: {e}")
