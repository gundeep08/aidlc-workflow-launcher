from pathlib import Path

import click

from cli.config.constants import CODE_DIR
from cli.exceptions import AidlcError, ConfigNotFoundError
from cli.services import git_service, workspace_config_service


@click.command()
@click.argument("repo_urls", nargs=-1, required=True)
def clone(repo_urls: tuple[str, ...]):
    """Clone one or more code repos into code/ directory."""
    workspace_root = Path.cwd()
    try:
        config = workspace_config_service.load_config(workspace_root)
        if not config:
            raise ConfigNotFoundError("Run 'aidlc init' first")

        code_dir = workspace_root / CODE_DIR
        code_dir.mkdir(exist_ok=True)
        cloned, skipped = 0, 0

        for url in repo_urls:
            repo_name = workspace_config_service.derive_repo_name(url)
            target = code_dir / repo_name
            if target.exists():
                click.echo(f"✓ {repo_name} already exists (already done)")
                skipped += 1
            else:
                click.echo(f"Cloning {repo_name}...")
                git_service.clone_repo(url, target)
                click.echo(f"✓ Cloned {repo_name}")
                cloned += 1
            config = workspace_config_service.add_code_repo(config, repo_name, url, f"{CODE_DIR}/{repo_name}")

        workspace_config_service.save_config(workspace_root, config)
        click.echo(f"\n✅ Done — cloned: {cloned}, skipped: {skipped}")

    except AidlcError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(1)
