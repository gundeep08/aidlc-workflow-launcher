from pathlib import Path

import click

from cli.config.constants import CODE_DIR, DOCS_DIR, RE_SKILLS_SUBDIR, AIDLC_WORKFLOWS_REPO_OWNER, AIDLC_WORKFLOWS_REPO_NAME
from cli.exceptions import AidlcError, ConfigNotFoundError
from cli.services import workspace_config_service, staleness_service, github_release_service, git_service


@click.command()
@click.pass_context
def status(ctx):
    """Show workspace health: rules version, docs sync, and RE skills freshness."""
    workspace_root = Path.cwd()
    try:
        config = workspace_config_service.load_config(workspace_root)
        if not config:
            raise ConfigNotFoundError("Run 'aidlc init' first")

        repos = workspace_config_service.get_code_repos(config)
        if not repos:
            click.echo("No repos registered. Run 'aidlc start' to get started.")
            return

        code_dir = workspace_root / CODE_DIR
        docs_dir = workspace_root / DOCS_DIR

        # Find docs repo subdirectory
        docs_repo_path = None
        if docs_dir.exists():
            subdirs = [p for p in docs_dir.iterdir() if p.is_dir()]
            if subdirs:
                docs_repo_path = subdirs[0]

        re_dir = docs_repo_path / RE_SKILLS_SUBDIR if docs_repo_path else None

        click.echo(f"\n{'Component':<25} {'Status':<40}")
        click.echo("─" * 65)

        # Rules version
        rules_stale = False
        local_version = config.get("rules_version", None)
        if local_version:
            try:
                latest = github_release_service.get_latest_release_info(
                    AIDLC_WORKFLOWS_REPO_OWNER, AIDLC_WORKFLOWS_REPO_NAME
                )
                if latest["tag"] != local_version:
                    click.echo(f"{'AI-DLC Rules':<25} {'⚠ Outdated: ' + local_version + ' → ' + latest['tag']:<40}")
                    rules_stale = True
                else:
                    click.echo(f"{'AI-DLC Rules':<25} {'✓ Up to date (' + local_version + ')':<40}")
            except Exception:
                click.echo(f"{'AI-DLC Rules':<25} {local_version + ' (could not check remote)':<40}")
        else:
            click.echo(f"{'AI-DLC Rules':<25} {'⚠ Not installed':<40}")
            rules_stale = True

        # Docs repo
        docs_stale = False
        if docs_repo_path:
            behind = git_service.commits_behind_remote(docs_repo_path)
            if behind is None:
                docs_status = "Could not check remote"
            elif behind > 0:
                docs_status = f"⚠ {behind} commit(s) behind remote"
                docs_stale = True
            else:
                docs_status = "✓ Up to date"
            click.echo(f"{'Docs: ' + docs_repo_path.name:<25} {docs_status:<40}")

        click.echo("─" * 65)

        # Code repos - RE skills status
        click.echo(f"{'Repo':<25} {'RE Skills':<40}")
        click.echo("─" * 65)

        stale_repos = []
        for repo in repos:
            name = repo["name"]
            if re_dir is None:
                re_status = "⚠ Docs repo not found"
                stale_repos.append(name)
            else:
                staleness = staleness_service.check_staleness(name, re_dir, code_dir / name)
                if staleness["reason"] == "no_re":
                    re_status = "⚠ No RE skills"
                    stale_repos.append(name)
                elif staleness["stale"]:
                    re_status = f"⚠ Stale ({staleness['commits_since']} commits since last RE)"
                    stale_repos.append(name)
                else:
                    re_status = "✓ Fresh"

            click.echo(f"{name:<25} {re_status:<40}")

        click.echo("")

        # Interactive prompts for remediation
        if rules_stale:
            if click.confirm("Update rules now?", default=True):
                ctx.invoke(_get_update_rules_cmd())

        if docs_stale:
            if click.confirm("Pull latest docs now?", default=True):
                ctx.invoke(_get_update_docs_cmd())

        if stale_repos:
            click.echo(f"⚠  RE skills need attention for: {', '.join(stale_repos)}")
            if click.confirm("Refresh RE skills now?", default=True):
                if len(stale_repos) == 1:
                    repo_name = stale_repos[0]
                else:
                    click.echo("")
                    for i, name in enumerate(stale_repos, 1):
                        click.echo(f"    {i}) {name}")
                    idx = click.prompt("\nWhich repo?", type=click.IntRange(1, len(stale_repos))) - 1
                    repo_name = stale_repos[idx]
                ctx.invoke(_get_re_cmd(), repo_name=repo_name)

    except AidlcError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(1)


def _get_update_rules_cmd():
    from cli.commands.update_rules import update_rules
    return update_rules


def _get_update_docs_cmd():
    from cli.commands.update_docs import update_docs
    return update_docs


def _get_re_cmd():
    from cli.commands.re import re_skills
    return re_skills
