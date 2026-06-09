from pathlib import Path

import click

from cli.config.constants import CODE_DIR, DOCS_DIR, RE_SKILLS_SUBDIR
from cli.exceptions import AidlcError, ConfigNotFoundError
from cli.services import git_service, workspace_config_service


@click.command("re")
@click.argument("repo_name", required=False)
def re_skills(repo_name: str | None):
    """Pull latest code and prompt to refresh RE skills for a repo."""
    workspace_root = Path.cwd()
    try:
        config = workspace_config_service.load_config(workspace_root)
        if not config:
            raise ConfigNotFoundError("Run 'aidlc init' first")

        repos = workspace_config_service.get_code_repos(config)
        if not repos:
            raise ConfigNotFoundError("No code repos registered. Run 'aidlc start' first.")

        docs_url = workspace_config_service.get_docs_repo_url(config)
        docs_repo_name = workspace_config_service.derive_repo_name(docs_url)

        # Resolve repo_name
        if not repo_name:
            if len(repos) == 1:
                repo_name = repos[0]["name"]
            else:
                click.echo("\n📋 Registered repos:\n")
                for i, r in enumerate(repos, 1):
                    click.echo(f"    {i}) {r['name']}")
                idx = click.prompt("\nWhich repo?", type=click.IntRange(1, len(repos))) - 1
                repo_name = repos[idx]["name"]

        code_repo_dir = workspace_root / CODE_DIR / repo_name
        if not code_repo_dir.exists():
            raise ConfigNotFoundError(f"Code repo not found at code/{repo_name}. Run 'aidlc start' first.")

        # Pull latest from default branch
        click.echo(f"Pulling latest code for {repo_name}...")
        git_service.pull_repo(code_repo_dir)
        click.echo(f"✓ code/{repo_name} is up to date")

        # Show RE prompt
        docs_re_path = f"docs/{docs_repo_name}/re-skills/{repo_name}/"
        click.echo("\n  Open your AI chat and paste the following prompt:")
        click.echo("")
        click.echo("┌──────────────────────────────────────────────────────────────┐")
        click.echo(f"│  Using AI-DLC, reverse engineer the codebase at              │")
        click.echo(f"│  code/{repo_name + '/':<54}│")
        click.echo(f"│  and generate the skills/knowledge base files.               │")
        click.echo(f"│  Store the output in {docs_re_path:<41}│")
        click.echo("└──────────────────────────────────────────────────────────────┘")

    except AidlcError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(1)
