import tempfile
from pathlib import Path

import click

from cli.config.constants import AIDLC_WORKFLOWS_REPO_OWNER, AIDLC_WORKFLOWS_REPO_NAME
from cli.config.constants import DOCS_DIR
from cli.exceptions import AidlcError
from cli.services import git_service, github_release_service, platform_service, workspace_config_service


@click.command()
def init():
    """Initialize workspace: select platform, download rules, configure docs repo URL."""
    workspace_root = Path.cwd()
    try:
        config = workspace_config_service.load_config(workspace_root)

        # Platform selection (idempotent — skip if set)
        if not workspace_config_service.get_platform(config):
            platform = _prompt_platform()
            config["platform"] = platform
        else:
            platform = config["platform"]
            click.echo(f"✓ Platform already configured: {platform} (already done)")

        # Docs repo URL (idempotent — skip if set)
        if not workspace_config_service.get_docs_repo_url(config):
            docs_url = click.prompt("Enter your docs repo git URL")
            config["docs_repo_url"] = docs_url
        else:
            docs_url = config["docs_repo_url"]
            click.echo(f"✓ Docs repo already configured (already done)")

        # Clone docs repo (idempotent — skip if present)
        docs_url = workspace_config_service.get_docs_repo_url(config) or docs_url
        docs_repo_name = workspace_config_service.derive_repo_name(docs_url)
        docs_dir = workspace_root / DOCS_DIR
        docs_target = docs_dir / docs_repo_name
        if not docs_target.exists():
            click.echo("Cloning docs repo...")
            docs_dir.mkdir(exist_ok=True)
            git_service.clone_repo(docs_url, docs_target)
            click.echo(f"✓ Docs repo cloned")
        else:
            click.echo(f"✓ Docs repo already cloned (already done)")

        # Rule download (idempotent — skip if rules exist)
        rules_path = workspace_root / platform_service.get_rules_path(platform)
        if not rules_path.exists():
            click.echo("Downloading latest AI-DLC rules...")
            release = github_release_service.get_latest_release_info(
                AIDLC_WORKFLOWS_REPO_OWNER, AIDLC_WORKFLOWS_REPO_NAME
            )
            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                zip_path = tmp_path / "release.zip"
                github_release_service.download_release_zip(release["download_url"], zip_path)
                extracted = github_release_service.extract_rules(zip_path, tmp_path / "extracted")
                platform_service.place_rules(platform, extracted, workspace_root)
            config["rules_version"] = release["tag"]
            click.echo(f"✓ Rules installed ({release['tag']})")
        else:
            click.echo(f"✓ Rules already present (already done)")

        workspace_config_service.save_config(workspace_root, config)
        click.echo("\n✅ Workspace initialized successfully!")
        click.echo("Next: run 'aidlc start' to begin a workflow.")

    except AidlcError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(1)


def _prompt_platform() -> str:
    platforms = platform_service.get_display_names()
    click.echo("Which AI coding assistant do you use?")
    for i, (key, display) in enumerate(platforms, 1):
        click.echo(f"  {i}) {display}")
    choice = click.prompt("Select", type=click.IntRange(1, len(platforms)))
    return platforms[choice - 1][0]
