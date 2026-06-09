from pathlib import Path

import click

from cli.config.constants import DOCS_DIR
from cli.exceptions import AidlcError, ConfigNotFoundError, StateNotFoundError, NoWorkflowInProgressError
from cli.services import workspace_config_service, state_service


@click.command()
@click.argument("project")
def resume(project: str):
    """Resume an interrupted AI-DLC workflow from aidlc-state.md."""
    workspace_root = Path.cwd()
    try:
        config = workspace_config_service.load_config(workspace_root)
        if not config:
            raise ConfigNotFoundError("Run 'aidlc init' first")

        docs_dir = workspace_root / DOCS_DIR
        # Find docs repo subdirectory
        docs_repo_path = None
        if docs_dir.exists():
            subdirs = [p for p in docs_dir.iterdir() if p.is_dir()]
            if subdirs:
                docs_repo_path = subdirs[0]

        if not docs_repo_path:
            raise StateNotFoundError(f"Docs repo not found. Run 'aidlc init' first.")

        state_file = state_service.find_state_file(docs_repo_path, project)
        if not state_file:
            raise StateNotFoundError(f"No workflow found for '{project}'")

        state = state_service.parse_state(state_file)
        if not state_service.is_workflow_in_progress(state):
            raise NoWorkflowInProgressError(f"No active workflow to resume for '{project}'. Use 'aidlc start' instead.")

        current_stage = state_service.get_current_stage(state)
        completed = state_service.get_completed_stages(state)

        click.echo(f"\n📋 Workflow Status for: {project}")
        click.echo(f"   Type: {state.get('project_type', 'Unknown')}")
        click.echo(f"   Current Stage: {current_stage}")
        click.echo(f"   Completed: {len(completed)} stages")
        click.echo()
        click.echo("To resume, open your AI chat and type:")
        click.echo(f'  "Resume AI-DLC workflow for {project} — currently at {current_stage}"')

    except AidlcError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(1)
