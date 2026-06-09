from pathlib import Path

import click

from cli.config.constants import DOCS_DIR
from cli.exceptions import AidlcError, ConfigNotFoundError
from cli.services import git_service, workspace_config_service


@click.command("update-docs")
def update_docs():
    """Pull latest changes for the docs repo."""
    workspace_root = Path.cwd()
    try:
        config = workspace_config_service.load_config(workspace_root)
        if not config:
            raise ConfigNotFoundError("Run 'aidlc init' first")

        docs_url = workspace_config_service.get_docs_repo_url(config)
        if not docs_url:
            raise ConfigNotFoundError("No docs repo configured. Run 'aidlc init' first.")

        docs_repo_name = workspace_config_service.derive_repo_name(docs_url)
        docs_repo_dir = workspace_root / DOCS_DIR / docs_repo_name

        if not docs_repo_dir.exists():
            raise ConfigNotFoundError(f"Docs repo not found at docs/{docs_repo_name}. Run 'aidlc init' first.")

        click.echo(f"Pulling docs repo ({docs_repo_name})...")
        git_service.pull_repo(docs_repo_dir)
        click.echo(f"✓ Docs repo up to date")

    except AidlcError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(1)
